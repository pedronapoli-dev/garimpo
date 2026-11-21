from typing import Any

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Recommendation, RecommendationType, Tag, User
from app.schemas import RecommendationCreate
from app.services import recommendations
from app.services.exceptions import DuplicateRecommendation
from tests.conftest import VALID_TEXT, make_user


def new_recommendation(**overrides: Any) -> RecommendationCreate:
    fields: dict[str, Any] = {
        "type": "album",
        "artist": "Arthur Verocai",
        "title": "Arthur Verocai",
        "genres": ["mpb", "jazz"],
        "text": VALID_TEXT,
    }
    return RecommendationCreate.model_validate(fields | overrides)


# Create


def test_create_persists_recommendation_with_keys_and_tags(
    session: Session, curator: User
) -> None:
    data = new_recommendation(artist="Arthur  VEROCAI", title=" Arthur Verocai ")

    created = recommendations.create_recommendation(session, curator, data)

    stored = session.get_one(Recommendation, created.id)
    assert stored.author is curator
    assert stored.artist == "Arthur  VEROCAI"
    assert stored.artist_key == "arthur verocai"
    assert stored.title_key == "arthur verocai"
    assert [tag.name for tag in stored.tags] == ["mpb", "jazz"]


def test_create_artist_stores_empty_title_key(session: Session, curator: User) -> None:
    data = new_recommendation(type="artist", title=None)

    created = recommendations.create_recommendation(session, curator, data)

    assert created.title is None
    assert created.title_key == ""


def test_create_reuses_existing_tags(session: Session, curator: User) -> None:
    recommendations.create_recommendation(session, curator, new_recommendation())

    recommendations.create_recommendation(
        session, curator, new_recommendation(title="Saudade", genres=["jazz", "soul"])
    )

    names = session.scalars(select(Tag.name).order_by(Tag.name)).all()
    assert names == ["jazz", "mpb", "soul"]


# Rule 7


@pytest.mark.parametrize(
    ("artist", "title"),
    [
        ("Arthur Verocai", "Arthur Verocai"),
        ("ARTHUR VEROCAI", "arthur verocai"),
        ("  Arthur   Verocai ", "Arthur    Verocai"),
    ],
)
def test_create_same_artist_and_title_raises_duplicate_with_existing_id(
    session: Session, curator: User, artist: str, title: str
) -> None:
    first = recommendations.create_recommendation(
        session, curator, new_recommendation()
    )
    other = make_user(session, email="other@example.com")

    with pytest.raises(DuplicateRecommendation) as error:
        recommendations.create_recommendation(
            session, other, new_recommendation(artist=artist, title=title)
        )

    assert error.value.existing_id == first.id
    assert session.scalar(select(func.count(Recommendation.id))) == 1


def test_create_same_artist_twice_raises_duplicate(
    session: Session, curator: User
) -> None:
    data = new_recommendation(type="artist", title=None)
    recommendations.create_recommendation(session, curator, data)

    with pytest.raises(DuplicateRecommendation):
        recommendations.create_recommendation(session, curator, data)


def test_create_same_artist_and_title_with_other_type_persists(
    session: Session, curator: User
) -> None:
    recommendations.create_recommendation(session, curator, new_recommendation())

    track = recommendations.create_recommendation(
        session, curator, new_recommendation(type="track")
    )

    assert track.type is RecommendationType.TRACK


def test_create_same_artist_with_other_title_persists(
    session: Session, curator: User
) -> None:
    recommendations.create_recommendation(session, curator, new_recommendation())

    other = recommendations.create_recommendation(
        session, curator, new_recommendation(title="Saudade")
    )

    assert other.id is not None
