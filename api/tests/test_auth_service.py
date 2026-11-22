from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Invite, User
from app.schemas import LoginIn, SignupIn
from app.services import auth, invites
from app.services.exceptions import (
    EmailTaken,
    InvalidCredentials,
    InvalidInvite,
    NotAuthenticated,
)
from app.settings import JWT_ALGORITHM, JWT_SECRET
from tests.conftest import make_user

PASSWORD = "correct horse battery"


def signup_data(code: str, **overrides: Any) -> SignupIn:
    fields: dict[str, Any] = {
        "invite_code": code,
        "email": "new@example.com",
        "display_name": "New Curator",
        "password": PASSWORD,
    }
    return SignupIn.model_validate(fields | overrides)


def count_users(session: Session) -> int:
    return session.scalar(select(func.count(User.id))) or 0


# Passwords


def test_hash_password_returns_argon2_hash_that_verifies() -> None:
    password_hash = auth.hash_password(PASSWORD)

    assert password_hash.startswith("$argon2id$")
    assert auth.verify_password(password_hash, PASSWORD) is True
    assert auth.verify_password(password_hash, "wrong password") is False


def test_verify_password_against_dev_curator_hash_returns_false() -> None:
    assert auth.verify_password("!", "anything") is False


# Sign-up and rule 1


def test_signup_creates_user_and_spends_invite(session: Session, curator: User) -> None:
    invite = invites.create_invite(session, curator)

    user = auth.signup(session, signup_data(invite.code, email="New@Example.com"))

    assert user.email == "new@example.com"
    assert auth.verify_password(user.password_hash, PASSWORD)
    session.refresh(invite)
    assert invite.used_by_id == user.id
    assert invite.used_at is not None


def test_signup_with_used_invite_raises_and_creates_no_user(
    session: Session, curator: User
) -> None:
    invite = invites.create_invite(session, curator)
    auth.signup(session, signup_data(invite.code))
    users_before = count_users(session)

    with pytest.raises(InvalidInvite):
        auth.signup(session, signup_data(invite.code, email="second@example.com"))

    assert count_users(session) == users_before


def test_signup_with_unknown_invite_raises(session: Session, curator: User) -> None:
    with pytest.raises(InvalidInvite):
        auth.signup(session, signup_data("no-such-code"))

    assert count_users(session) == 1


def test_signup_with_taken_email_raises_and_keeps_invite(
    session: Session, curator: User
) -> None:
    taken = make_user(session, email="taken@example.com")
    invite = invites.create_invite(session, curator)

    with pytest.raises(EmailTaken):
        auth.signup(session, signup_data(invite.code, email=taken.email))

    assert session.get_one(Invite, invite.code).used_by_id is None


def test_signup_losing_the_email_race_raises_and_keeps_invite(
    session: Session, curator: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    taken = make_user(session, email="taken@example.com")
    invite = invites.create_invite(session, curator)
    # Skip the pre-check, as when a concurrent sign-up passed it too.
    monkeypatch.setattr(auth, "_ensure_email_free", lambda session, email: None)

    with pytest.raises(EmailTaken):
        auth.signup(session, signup_data(invite.code, email=taken.email))

    assert session.get_one(Invite, invite.code).used_by_id is None
    assert count_users(session) == 2


def test_signup_violating_another_constraint_raises_it(
    session: Session, curator: User
) -> None:
    invite = invites.create_invite(session, curator)
    # model_construct skips validation, so only the NOT NULL on email stops it.
    data = SignupIn.model_construct(
        invite_code=invite.code, email=None, display_name="X", password=PASSWORD
    )

    with pytest.raises(IntegrityError):
        auth.signup(session, data)


# Login


def test_login_returns_user_for_right_password(session: Session) -> None:
    user = make_user(session, password_hash=auth.hash_password(PASSWORD))

    logged_in = auth.login(
        session, LoginIn(email=user.email.upper(), password=PASSWORD)
    )

    assert logged_in is user


@pytest.mark.parametrize("email", ["curator@example.com", "nobody@example.com"])
def test_login_with_wrong_email_or_password_raises(
    session: Session, email: str
) -> None:
    make_user(session, password_hash=auth.hash_password(PASSWORD))

    with pytest.raises(InvalidCredentials):
        auth.login(session, LoginIn(email=email, password="wrong password"))


def test_login_with_unusable_hash_raises(session: Session) -> None:
    # The dev curator's hash is "!"; no password, not even "!", matches it.
    user = make_user(session, password_hash="!")

    with pytest.raises(InvalidCredentials):
        auth.login(session, LoginIn(email=user.email, password="!"))


# Tokens


def test_token_authenticates_its_user(session: Session, curator: User) -> None:
    token = auth.create_access_token(curator)

    assert auth.authenticate(session, token) is curator


def test_authenticate_without_token_raises(session: Session) -> None:
    with pytest.raises(NotAuthenticated):
        auth.authenticate(session, None)


def test_expired_token_raises(session: Session, curator: User) -> None:
    token = auth.create_access_token(
        curator, now=datetime.now(UTC) - timedelta(days=31)
    )

    with pytest.raises(NotAuthenticated):
        auth.authenticate(session, token)


@pytest.mark.parametrize(
    "token",
    [
        "not-a-jwt",
        jwt.encode({"sub": "1", "exp": 4102444800}, "x" * 32, algorithm=JWT_ALGORITHM),
        jwt.encode({"exp": 4102444800}, JWT_SECRET, algorithm=JWT_ALGORITHM),
        jwt.encode(
            {"sub": "abc", "exp": 4102444800}, JWT_SECRET, algorithm=JWT_ALGORITHM
        ),
    ],
    ids=["garbage", "wrong-secret", "no-subject", "non-numeric-subject"],
)
def test_invalid_token_raises(session: Session, curator: User, token: str) -> None:
    with pytest.raises(NotAuthenticated):
        auth.authenticate(session, token)


def test_token_for_deleted_user_raises(session: Session) -> None:
    ghost = User(
        id=999, email="ghost@example.com", display_name="Ghost", password_hash="!"
    )

    with pytest.raises(NotAuthenticated):
        auth.authenticate(session, auth.create_access_token(ghost))
