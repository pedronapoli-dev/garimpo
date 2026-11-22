from datetime import UTC, datetime
from typing import Any

import pytest
from pydantic import ValidationError

from app.models import RecommendationType, Tag
from app.schemas import RecommendationCreate, RecommendationOut, RecommendationUpdate
from tests.conftest import VALID_TEXT


def create_payload(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "type": "album",
        "artist": "Arthur Verocai",
        "title": "Arthur Verocai",
        "genres": ["mpb", "jazz"],
        "text": VALID_TEXT,
    }
    return payload | overrides


def test_create_valid_payload_returns_model() -> None:
    recommendation = RecommendationCreate.model_validate(create_payload())

    assert recommendation.type is RecommendationType.ALBUM
    assert recommendation.genres == ["mpb", "jazz"]


def test_create_strips_artist_title_and_text() -> None:
    recommendation = RecommendationCreate.model_validate(
        create_payload(artist="  Verocai ", title=" Arthur ", text=f"  {VALID_TEXT}  ")
    )

    assert recommendation.artist == "Verocai"
    assert recommendation.title == "Arthur"
    assert recommendation.text == VALID_TEXT


@pytest.mark.parametrize("genres", [[], ["a", "b", "c", "d", "e", "f"]])
def test_create_genre_count_out_of_range_raises(genres: list[str]) -> None:
    with pytest.raises(ValidationError):
        RecommendationCreate.model_validate(create_payload(genres=genres))


def test_create_five_genres_returns_model() -> None:
    genres = ["a", "b", "c", "d", "e"]

    assert (
        RecommendationCreate.model_validate(create_payload(genres=genres)).genres
        == genres
    )


def test_create_normalizes_and_deduplicates_genres() -> None:
    recommendation = RecommendationCreate.model_validate(
        create_payload(genres=[" Jazz ", "jazz", "Hip  Hop"])
    )

    assert recommendation.genres == ["jazz", "hip hop"]


def test_create_blank_genre_raises() -> None:
    with pytest.raises(ValidationError):
        RecommendationCreate.model_validate(create_payload(genres=["   "]))


@pytest.mark.parametrize("length", [79, 1001])
def test_create_text_length_out_of_range_raises(length: int) -> None:
    with pytest.raises(ValidationError):
        RecommendationCreate.model_validate(create_payload(text="x" * length))


@pytest.mark.parametrize("length", [80, 1000])
def test_create_text_length_at_bounds_returns_model(length: int) -> None:
    assert RecommendationCreate.model_validate(create_payload(text="x" * length))


def test_create_text_padded_with_spaces_counts_stripped_length() -> None:
    with pytest.raises(ValidationError):
        RecommendationCreate.model_validate(create_payload(text=" " * 10 + "x" * 79))


@pytest.mark.parametrize("type_", ["album", "track"])
@pytest.mark.parametrize("title", [None, "", "   "])
def test_create_album_or_track_without_title_raises(
    type_: str, title: str | None
) -> None:
    with pytest.raises(ValidationError, match="title is required"):
        RecommendationCreate.model_validate(create_payload(type=type_, title=title))


def test_create_artist_with_title_raises() -> None:
    with pytest.raises(ValidationError, match="cannot have a title"):
        RecommendationCreate.model_validate(create_payload(type="artist", title="X"))


@pytest.mark.parametrize("title", [None, ""])
def test_create_artist_without_title_returns_model(title: str | None) -> None:
    recommendation = RecommendationCreate.model_validate(
        create_payload(type="artist", title=title)
    )

    assert recommendation.title is None


def test_create_unknown_type_raises() -> None:
    with pytest.raises(ValidationError):
        RecommendationCreate.model_validate(create_payload(type="playlist"))


def test_create_blank_artist_raises() -> None:
    with pytest.raises(ValidationError):
        RecommendationCreate.model_validate(create_payload(artist="  "))


def test_update_empty_payload_sets_no_fields() -> None:
    assert RecommendationUpdate.model_validate({}).model_dump(exclude_unset=True) == {}


def test_update_keeps_only_sent_fields() -> None:
    update = RecommendationUpdate.model_validate({"text": VALID_TEXT, "title": None})

    assert update.model_dump(exclude_unset=True) == {"text": VALID_TEXT, "title": None}


@pytest.mark.parametrize("field", ["type", "artist", "genres", "text"])
def test_update_null_for_required_field_raises(field: str) -> None:
    with pytest.raises(ValidationError, match="cannot be null"):
        RecommendationUpdate.model_validate({field: None})


def test_update_applies_field_rules() -> None:
    with pytest.raises(ValidationError):
        RecommendationUpdate.model_validate({"genres": []})


def test_out_from_orm_returns_genre_names_and_utc_timestamps() -> None:
    naive = datetime(2026, 11, 21, 12, 0)
    source = {
        "id": 1,
        "type": "artist",
        "artist": "Arthur Verocai",
        "title": None,
        "tags": [Tag(name="mpb"), "jazz"],
        "text": VALID_TEXT,
        "author": {"id": 1, "display_name": "Pedro"},
        "created_at": naive,
        "updated_at": naive,
        "vote_count": 0,
        "voted_by_me": False,
        "saved_by_me": False,
    }

    out = RecommendationOut.model_validate(source)

    assert out.genres == ["mpb", "jazz"]
    assert out.created_at == naive.replace(tzinfo=UTC)
    assert "genres" in out.model_dump(by_alias=True)
