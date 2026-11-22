import secrets

from sqlalchemy.orm import Session

from app.models import Invite, User


def create_invite(session: Session, creator: User) -> Invite:
    """Rule 1: every user can generate invites, each usable once."""
    # 9 random bytes -> 12 URL-safe characters, easy to type and to share.
    invite = Invite(code=secrets.token_urlsafe(9), created_by_id=creator.id)
    session.add(invite)
    session.commit()
    return invite
