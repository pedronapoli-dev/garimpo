from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User

# Seeded by the "Seed dev curator" migration. Slice 4 replaces it with real auth.
DEV_CURATOR_EMAIL = "curator@garimpo.local"


def get_dev_curator(session: Session) -> User:
    return session.scalars(select(User).where(User.email == DEV_CURATOR_EMAIL)).one()
