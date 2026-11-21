from datetime import UTC, datetime
from typing import Annotated, Any, Self

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

from app.models import RecommendationType
from app.normalization import normalize_key

MIN_GENRES = 1
MAX_GENRES = 5


def _as_utc(value: datetime) -> datetime:
    # SQLite returns naive datetimes. They are UTC (server_default), so say so.
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


UtcDatetime = Annotated[datetime, AfterValidator(_as_utc)]
Artist = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)
]
Title = Annotated[str, StringConstraints(strip_whitespace=True, max_length=200)]
Text = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=80, max_length=1000)
]
Genre = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=50),
    AfterValidator(normalize_key),
]


def _unique_genres(genres: list[str]) -> list[str]:
    # "Jazz" and "jazz " are one genre once normalized; keep the first order seen.
    unique = list(dict.fromkeys(genres))
    if len(unique) < MIN_GENRES:
        raise ValueError(f"at least {MIN_GENRES} genre is required")
    return unique


Genres = Annotated[
    list[Genre],
    Field(min_length=MIN_GENRES, max_length=MAX_GENRES),
    AfterValidator(_unique_genres),
]


def check_title_for_type(type_: RecommendationType, title: str | None) -> None:
    """Rule 2: albums and tracks need a title; artists cannot have one."""
    if type_ is RecommendationType.ARTIST and title is not None:
        raise ValueError("an artist recommendation cannot have a title")
    if type_ is not RecommendationType.ARTIST and title is None:
        raise ValueError(f"a title is required for type {type_}")


def _empty_to_none(title: str | None) -> str | None:
    return title or None


class RecommendationCreate(BaseModel):
    type: RecommendationType
    artist: Artist
    title: Annotated[Title | None, AfterValidator(_empty_to_none)] = None
    genres: Genres
    text: Text

    @model_validator(mode="after")
    def title_matches_type(self) -> Self:
        check_title_for_type(self.type, self.title)
        return self


class RecommendationUpdate(BaseModel):
    """Every field is optional; only the ones sent are changed.

    The title rule depends on the stored type, so the service checks it after
    merging this update with the recommendation.
    """

    type: RecommendationType | None = None
    artist: Artist | None = None
    title: Annotated[Title | None, AfterValidator(_empty_to_none)] = None
    genres: Genres | None = None
    text: Text | None = None

    @model_validator(mode="after")
    def only_title_can_be_null(self) -> Self:
        for name in self.model_fields_set - {"title"}:
            if getattr(self, name) is None:
                raise ValueError(f"{name} cannot be null")
        return self


class AuthorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    display_name: str


class RecommendationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: RecommendationType
    artist: str
    title: str | None
    genres: list[str] = Field(validation_alias="tags")
    text: str
    author: AuthorOut
    created_at: UtcDatetime
    updated_at: UtcDatetime

    @field_validator("genres", mode="before")
    @classmethod
    def tag_names(cls, tags: list[Any]) -> list[str]:
        # Reading from the ORM gives Tag objects; reading from a dict gives names.
        return [tag if isinstance(tag, str) else tag.name for tag in tags]


class RecommendationPage(BaseModel):
    items: list[RecommendationOut]
    next_cursor: str | None


class TagOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


Email = Annotated[EmailStr, AfterValidator(str.lower)]
DisplayName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)
]
# Argon2 has no input limit; the maximum only stops absurd payloads.
Password = Annotated[str, StringConstraints(min_length=8, max_length=128)]


class SignupIn(BaseModel):
    invite_code: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    email: Email
    display_name: DisplayName
    password: Password


class LoginIn(BaseModel):
    email: Email
    # No length rule on login: a wrong password is just a wrong password.
    password: str


class CurrentUserOut(BaseModel):
    """The logged-in user, including the private email."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    display_name: str


class SessionOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: CurrentUserOut


class InviteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str


class ErrorOut(BaseModel):
    code: str
    message: str
    existing_id: int | None = None
