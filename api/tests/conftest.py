from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db import create_db_engine, get_session
from app.models import Base, Recommendation, RecommendationType, User
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
def client(session: Session) -> Iterator[TestClient]:
    def override_get_session() -> Iterator[Session]:
        yield session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


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
