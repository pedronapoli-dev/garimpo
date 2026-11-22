from sqlalchemy.orm import Session

from app.models import Invite, User
from app.services import invites
from tests.conftest import make_user


def test_create_invite_returns_unused_code_for_creator(
    session: Session, curator: User
) -> None:
    invite = invites.create_invite(session, curator)

    stored = session.get_one(Invite, invite.code)
    assert stored.created_by_id == curator.id
    assert stored.used_by_id is None
    assert len(invite.code) == 12


def test_any_user_can_create_many_unique_invites(session: Session) -> None:
    user = make_user(session)

    codes = {invites.create_invite(session, user).code for _ in range(20)}

    assert len(codes) == 20
