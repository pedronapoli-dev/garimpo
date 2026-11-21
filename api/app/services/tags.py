from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Tag


def list_tags(session: Session) -> Sequence[Tag]:
    return session.scalars(select(Tag).order_by(Tag.name)).all()
