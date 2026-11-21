from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Recommendation, User
from app.schemas import UserProfileOut
from app.services.exceptions import UserNotFound

# Seeded by the "Seed dev curator" migration. Since slice 4 it authors the
# recommendations created before auth and creates the first invite (app/cli.py).
DEV_CURATOR_EMAIL = "curator@garimpo.local"


def get_dev_curator(session: Session) -> User:
    return session.scalars(select(User).where(User.email == DEV_CURATOR_EMAIL)).one()


def get_profile(session: Session, user_id: int) -> UserProfileOut:
    """A curator's public profile (FR7). Never exposes the email."""
    user = session.get(User, user_id)
    if user is None:
        raise UserNotFound(user_id)
    count = session.scalar(
        select(func.count()).where(Recommendation.author_id == user_id)
    )
    return UserProfileOut(
        id=user.id,
        display_name=user.display_name,
        created_at=user.created_at,
        recommendation_count=count or 0,
    )
