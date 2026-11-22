from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db import create_db_engine, get_session
from app.models import Base, Recommendation, RecommendationType, Save, User, Vote
from app.services import auth
from app.services.users import DEV_CURATOR_EMAIL
from main import app

VALID_TEXT = (
    "Why listen: Verocai wrote orchestral arrangements for this record that sound "
    "like nothing else recorded in Brazil in 1972."
)


@pytest.fixture
def session() -> Iterator[Session]:
    engine = create_db_engine("sqlite://", poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        yield session
    engine.dispose()


@pytest.fixture
def curator(session: Session) -> User:
    """The dev curator the seed migration creates; create_all does not seed it."""
    return make_user(session, email=DEV_CURATOR_EMAIL, display_name="Pedro")


@pytest.fixture
def anonymous_client(session: Session) -> Iterator[TestClient]:
    """A client without a token, sharing the test's database session."""

    def override_get_session() -> Iterator[Session]:
        yield session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def client(anonymous_client: TestClient, curator: User) -> TestClient:
    """A client logged in as the curator."""
    anonymous_client.headers.update(auth_headers(curator))
    return anonymous_client


def auth_headers(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {auth.create_access_token(user)}"}


def make_user(session: Session, **overrides: Any) -> User:
    fields: dict[str, Any] = {
        "email": "curator@example.com",
        "display_name": "Curator",
        "password_hash": "!",
    }
    user = User(**(fields | overrides))
    session.add(user)
    session.flush()
    return user


def make_recommendation(
    session: Session, author: User, **overrides: Any
) -> Recommendation:
    fields: dict[str, Any] = {
        "type": RecommendationType.ALBUM,
        "artist": "Arthur Verocai",
        "title": "Arthur Verocai",
        "artist_key": "arthur verocai",
        "title_key": "arthur verocai",
        "text": VALID_TEXT,
    }
    recommendation = Recommendation(author=author, **(fields | overrides))
    session.add(recommendation)
    session.flush()
    return recommendation


def make_vote(session: Session, user: User, recommendation: Recommendation) -> Vote:
    vote = Vote(user_id=user.id, recommendation_id=recommendation.id)
    session.add(vote)
    session.flush()
    return vote


def make_save(session: Session, user: User, recommendation: Recommendation) -> Save:
    save = Save(user_id=user.id, recommendation_id=recommendation.id)
    session.add(save)
    session.flush()
    return save
