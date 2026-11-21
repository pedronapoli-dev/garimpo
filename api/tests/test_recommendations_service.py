from datetime import datetime
from typing import Any

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Recommendation, RecommendationType, Tag, User
from app.schemas import RecommendationCreate, RecommendationUpdate
from app.services import recommendations, tags
from app.services.exceptions import (
    DuplicateRecommendation,
    InvalidCursor,
    InvalidRecommendation,
    NotAuthor,
    RecommendationNotFound,
)
from tests.conftest import VALID_TEXT, make_recommendation, make_user


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


# Read


def make_feed(session: Session, author: User, count: int) -> list[Recommendation]:
    """Creates `count` recommendations, all within the same second."""
    return [
        make_recommendation(
            session,
            author,
            title=f"Album {index}",
            title_key=f"album {index}",
            tags=[_tag(session, "jazz" if index % 2 == 0 else "mpb")],
        )
        for index in range(count)
    ]


def _tag(session: Session, name: str) -> Tag:
    tag = session.scalar(select(Tag).where(Tag.name == name))
    return tag if tag is not None else Tag(name=name)


def test_get_returns_recommendation(session: Session, curator: User) -> None:
    created = make_recommendation(session, curator)

    assert recommendations.get_recommendation(session, created.id) is created


def test_get_missing_raises_not_found(session: Session) -> None:
    with pytest.raises(RecommendationNotFound):
        recommendations.get_recommendation(session, 999)


def test_list_returns_newest_first(session: Session, curator: User) -> None:
    feed = make_feed(session, curator, 3)

    items, next_cursor = recommendations.list_recommendations(session)

    assert [item.id for item in items] == [item.id for item in reversed(feed)]
    assert next_cursor is None


def test_list_orders_by_created_at_before_id(session: Session, curator: User) -> None:
    older = make_recommendation(session, curator, title="Old", title_key="old")
    newer = make_recommendation(session, curator, title="New", title_key="new")
    older.created_at = datetime(2030, 1, 1)
    session.flush()

    items, _ = recommendations.list_recommendations(session)

    assert [item.id for item in items] == [older.id, newer.id]


def test_list_pages_through_feed_without_gaps_or_repeats(
    session: Session, curator: User
) -> None:
    feed = make_feed(session, curator, 7)
    seen: list[int] = []
    cursor = None

    for _ in range(4):
        items, cursor = recommendations.list_recommendations(
            session, cursor=cursor, limit=3
        )
        seen += [item.id for item in items]
        if cursor is None:
            break

    assert seen == [item.id for item in reversed(feed)]
    assert cursor is None


def test_list_last_full_page_returns_no_cursor(session: Session, curator: User) -> None:
    make_feed(session, curator, 3)

    _, next_cursor = recommendations.list_recommendations(session, limit=3)

    assert next_cursor is None


def test_list_filters_by_normalized_genre(session: Session, curator: User) -> None:
    feed = make_feed(session, curator, 4)

    items, _ = recommendations.list_recommendations(session, genre=" JAZZ ")

    assert [item.id for item in items] == [feed[2].id, feed[0].id]


@pytest.mark.parametrize("cursor", ["not-base64!", "bm90LWEtY3Vyc29y", "eHx5"])
def test_list_invalid_cursor_raises(session: Session, cursor: str) -> None:
    with pytest.raises(InvalidCursor):
        recommendations.list_recommendations(session, cursor=cursor)


def test_list_tags_returns_names_alphabetically(
    session: Session, curator: User
) -> None:
    make_feed(session, curator, 2)

    assert [tag.name for tag in tags.list_tags(session)] == ["jazz", "mpb"]


# Update


def update(**fields: Any) -> RecommendationUpdate:
    return RecommendationUpdate.model_validate(fields)


def test_update_changes_only_sent_fields(session: Session, curator: User) -> None:
    created = recommendations.create_recommendation(
        session, curator, new_recommendation()
    )
    new_text = VALID_TEXT.replace("1972", "1973")

    updated = recommendations.update_recommendation(
        session, curator, created.id, update(text=new_text)
    )

    assert updated.text == new_text
    assert updated.artist == "Arthur Verocai"
    assert [tag.name for tag in updated.tags] == ["mpb", "jazz"]


def test_update_artist_recomputes_keys(session: Session, curator: User) -> None:
    created = recommendations.create_recommendation(
        session, curator, new_recommendation()
    )

    updated = recommendations.update_recommendation(
        session,
        curator,
        created.id,
        update(artist="  Azymuth ", title="Light As A Feather"),
    )

    assert updated.artist_key == "azymuth"
    assert updated.title_key == "light as a feather"


def test_update_replaces_genres(session: Session, curator: User) -> None:
    created = recommendations.create_recommendation(
        session, curator, new_recommendation()
    )

    updated = recommendations.update_recommendation(
        session, curator, created.id, update(genres=["Soul", "jazz"])
    )

    assert [tag.name for tag in updated.tags] == ["soul", "jazz"]


def test_update_sets_updated_at(session: Session, curator: User) -> None:
    created = recommendations.create_recommendation(
        session, curator, new_recommendation()
    )
    created.updated_at = datetime(2000, 1, 1)
    session.commit()

    updated = recommendations.update_recommendation(
        session, curator, created.id, update(genres=["soul"])
    )

    assert updated.updated_at > datetime(2000, 1, 1)


def test_update_to_existing_artist_and_title_raises_duplicate(
    session: Session, curator: User
) -> None:
    first = recommendations.create_recommendation(
        session, curator, new_recommendation()
    )
    second = recommendations.create_recommendation(
        session, curator, new_recommendation(title="Saudade")
    )

    with pytest.raises(DuplicateRecommendation) as error:
        recommendations.update_recommendation(
            session, curator, second.id, update(title="ARTHUR VEROCAI")
        )

    assert error.value.existing_id == first.id


def test_update_keeping_own_artist_and_title_persists(
    session: Session, curator: User
) -> None:
    created = recommendations.create_recommendation(
        session, curator, new_recommendation()
    )

    updated = recommendations.update_recommendation(
        session, curator, created.id, update(title="arthur verocai")
    )

    assert updated.title == "arthur verocai"


def test_update_to_artist_with_null_title_persists(
    session: Session, curator: User
) -> None:
    created = recommendations.create_recommendation(
        session, curator, new_recommendation()
    )

    updated = recommendations.update_recommendation(
        session, curator, created.id, update(type="artist", title=None)
    )

    assert updated.type is RecommendationType.ARTIST
    assert updated.title is None
    assert updated.title_key == ""


def test_update_to_artist_keeping_title_raises_invalid(
    session: Session, curator: User
) -> None:
    created = recommendations.create_recommendation(
        session, curator, new_recommendation()
    )

    with pytest.raises(InvalidRecommendation, match="cannot have a title"):
        recommendations.update_recommendation(
            session, curator, created.id, update(type="artist")
        )


def test_update_removing_album_title_raises_invalid(
    session: Session, curator: User
) -> None:
    created = recommendations.create_recommendation(
        session, curator, new_recommendation()
    )

    with pytest.raises(InvalidRecommendation, match="title is required"):
        recommendations.update_recommendation(
            session, curator, created.id, update(title=None)
        )


def test_update_missing_raises_not_found(session: Session, curator: User) -> None:
    with pytest.raises(RecommendationNotFound):
        recommendations.update_recommendation(
            session, curator, 999, update(text=VALID_TEXT)
        )


# Delete


def test_delete_removes_recommendation_and_keeps_tags(
    session: Session, curator: User
) -> None:
    created = recommendations.create_recommendation(
        session, curator, new_recommendation()
    )

    recommendations.delete_recommendation(session, curator, created.id)

    assert session.get(Recommendation, created.id) is None
    assert session.scalars(select(Tag.name).order_by(Tag.name)).all() == ["jazz", "mpb"]


def test_delete_missing_raises_not_found(session: Session, curator: User) -> None:
    with pytest.raises(RecommendationNotFound):
        recommendations.delete_recommendation(session, curator, 999)


# Rule 5


def test_update_by_other_user_raises_not_author(
    session: Session, curator: User
) -> None:
    created = recommendations.create_recommendation(
        session, curator, new_recommendation()
    )
    other = make_user(session, email="other@example.com")

    with pytest.raises(NotAuthor):
        recommendations.update_recommendation(
            session, other, created.id, update(text=VALID_TEXT)
        )


def test_delete_by_other_user_raises_not_author(
    session: Session, curator: User
) -> None:
    created = recommendations.create_recommendation(
        session, curator, new_recommendation()
    )
    other = make_user(session, email="other@example.com")

    with pytest.raises(NotAuthor):
        recommendations.delete_recommendation(session, other, created.id)

    assert session.get(Recommendation, created.id) is not None
