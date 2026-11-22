from datetime import UTC, datetime

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.models import Invite, User
from app.schemas import LoginIn, SignupIn
from app.services.exceptions import (
    EmailTaken,
    InvalidCredentials,
    InvalidInvite,
    NotAuthenticated,
)
from app.settings import ACCESS_TOKEN_TTL, JWT_ALGORITHM, JWT_SECRET

_hasher = PasswordHasher()
# Verified when the email is unknown, so both failures take the same time and
# response times do not reveal which emails have accounts.
_DUMMY_HASH = _hasher.hash("garimpo-dummy-password")


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        # InvalidHashError covers "!", the dev curator's unusable hash.
        return False


def signup(session: Session, data: SignupIn) -> User:
    """Rule 1: creates the user and spends the invite, or changes nothing."""
    if session.scalar(select(User.id).where(User.email == data.email)) is not None:
        raise EmailTaken()

    # A savepoint: if the invite cannot be claimed, the new user is rolled back
    # too, and nothing else pending in the session is touched.
    with session.begin_nested():
        user = User(
            email=data.email,
            display_name=data.display_name,
            password_hash=hash_password(data.password),
        )
        session.add(user)
        session.flush()

        # Conditional UPDATE: of two sign-ups racing for a code, one matches.
        # RETURNING gives back the code only when the row was claimed.
        claimed = session.scalar(
            update(Invite)
            .where(Invite.code == data.invite_code, Invite.used_by_id.is_(None))
            .values(used_by_id=user.id, used_at=func.now())
            .returning(Invite.code)
        )
        if claimed is None:
            raise InvalidInvite()

    session.commit()
    return user


def login(session: Session, data: LoginIn) -> User:
    user = session.scalar(select(User).where(User.email == data.email))
    if user is None:
        verify_password(_DUMMY_HASH, data.password)
        raise InvalidCredentials()
    if not verify_password(user.password_hash, data.password):
        raise InvalidCredentials()
    return user


def create_access_token(user: User, *, now: datetime | None = None) -> str:
    issued_at = now if now is not None else datetime.now(UTC)
    payload = {
        "sub": str(user.id),
        "iat": issued_at,
        "exp": issued_at + ACCESS_TOKEN_TTL,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def authenticate(session: Session, token: str | None) -> User:
    """The user a bearer token belongs to. Every failure is the same 401."""
    if token is None:
        raise NotAuthenticated()
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
            options={"require": ["exp", "sub"]},
        )
        user_id = int(payload["sub"])
    except (jwt.InvalidTokenError, ValueError) as error:
        raise NotAuthenticated() from error

    user = session.get(User, user_id)
    if user is None:
        raise NotAuthenticated()
    return user
