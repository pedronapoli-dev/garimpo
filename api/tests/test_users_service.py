import pytest
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from app.models import User
from app.services import users


def test_get_dev_curator_returns_seeded_user(session: Session, curator: User) -> None:
    assert users.get_dev_curator(session) is curator


def test_get_dev_curator_without_seed_raises(session: Session) -> None:
    with pytest.raises(NoResultFound):
        users.get_dev_curator(session)
