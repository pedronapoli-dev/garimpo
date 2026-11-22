import pytest
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from app.models import User
from app.services import users
from app.services.exceptions import UserNotFound
from tests.conftest import make_recommendation


def test_get_dev_curator_returns_seeded_user(session: Session, curator: User) -> None:
    assert users.get_dev_curator(session) is curator


def test_get_dev_curator_without_seed_raises(session: Session) -> None:
    with pytest.raises(NoResultFound):
        users.get_dev_curator(session)


def test_get_profile_counts_recommendations(session: Session, curator: User) -> None:
    make_recommendation(session, curator)

    profile = users.get_profile(session, curator.id)

    assert profile.display_name == "Pedro"
    assert profile.recommendation_count == 1
    assert "email" not in profile.model_dump()


def test_get_profile_of_missing_user_raises(session: Session) -> None:
    with pytest.raises(UserNotFound):
        users.get_profile(session, 999)
