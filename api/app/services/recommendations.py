import base64
import binascii
from datetime import datetime

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models import Recommendation, RecommendationType, Tag, User
from app.normalization import normalize_key
from app.schemas import RecommendationCreate, RecommendationUpdate, check_title_for_type
from app.services.exceptions import (
    DuplicateRecommendation,
    InvalidCursor,
    InvalidRecommendation,
    RecommendationNotFound,
)

DEFAULT_PAGE_SIZE = 20


def create_recommendation(
    session: Session, author: User, data: RecommendationCreate
) -> Recommendation:
    artist_key = normalize_key(data.artist)
    title_key = normalize_key(data.title or "")
    _ensure_unique(session, data.type, artist_key, title_key)

    recommendation = Recommendation(
        author=author,
        type=data.type,
        artist=data.artist,
        title=data.title,
        artist_key=artist_key,
        title_key=title_key,
        text=data.text,
        tags=_get_or_create_tags(session, data.genres),
    )
    session.add(recommendation)
    session.commit()
    return recommendation


def update_recommendation(
    session: Session, recommendation_id: int, data: RecommendationUpdate
) -> Recommendation:
    """Partial update: only the fields present in the request body change."""
    recommendation = get_recommendation(session, recommendation_id)
    changes = data.model_dump(exclude_unset=True)
    genres = changes.pop("genres", None)

    # Rule 2 on the merged state: the type may come from the request or the row.
    merged = {"type": recommendation.type, "title": recommendation.title} | changes
    try:
        check_title_for_type(merged["type"], merged["title"])
    except ValueError as error:
        raise InvalidRecommendation(str(error)) from error

    if changes.keys() & {"type", "artist", "title"}:
        artist_key = normalize_key(changes.get("artist", recommendation.artist))
        title_key = normalize_key(merged["title"] or "")
        _ensure_unique(
            session, merged["type"], artist_key, title_key, exclude_id=recommendation.id
        )
        recommendation.artist_key = artist_key
        recommendation.title_key = title_key

    for field, value in changes.items():
        setattr(recommendation, field, value)
    if genres is not None:
        recommendation.tags = _get_or_create_tags(session, genres)
    # onupdate only fires when a column changes; a genre-only edit counts too.
    recommendation.updated_at = func.now()

    session.commit()
    return recommendation


def delete_recommendation(session: Session, recommendation_id: int) -> None:
    session.delete(get_recommendation(session, recommendation_id))
    session.commit()


def _ensure_unique(
    session: Session,
    type_: RecommendationType,
    artist_key: str,
    title_key: str,
    *,
    exclude_id: int | None = None,
) -> None:
    """Rule 7. The unique index also guards it; this check finds the existing id."""
    query = select(Recommendation.id).where(
        Recommendation.type == type_,
        Recommendation.artist_key == artist_key,
        Recommendation.title_key == title_key,
    )
    if exclude_id is not None:
        query = query.where(Recommendation.id != exclude_id)
    existing_id = session.scalar(query)
    if existing_id is not None:
        raise DuplicateRecommendation(existing_id)


def _get_or_create_tags(session: Session, names: list[str]) -> list[Tag]:
    existing = {
        tag.name: tag for tag in session.scalars(select(Tag).where(Tag.name.in_(names)))
    }
    return [existing.get(name) or Tag(name=name) for name in names]


def get_recommendation(session: Session, recommendation_id: int) -> Recommendation:
    recommendation = session.get(Recommendation, recommendation_id)
    if recommendation is None:
        raise RecommendationNotFound(recommendation_id)
    return recommendation


def list_recommendations(
    session: Session,
    *,
    genre: str | None = None,
    cursor: str | None = None,
    limit: int = DEFAULT_PAGE_SIZE,
) -> tuple[list[Recommendation], str | None]:
    """The feed, newest first. Returns one page and the cursor for the next one."""
    query = (
        select(Recommendation)
        .options(joinedload(Recommendation.author), selectinload(Recommendation.tags))
        .order_by(Recommendation.created_at.desc(), Recommendation.id.desc())
        # One extra row tells whether there is a next page.
        .limit(limit + 1)
    )
    if genre is not None:
        query = query.where(Recommendation.tags.any(Tag.name == normalize_key(genre)))
    if cursor is not None:
        created_at, recommendation_id = _decode_cursor(cursor)
        # Rows strictly after the cursor in (created_at desc, id desc) order.
        # Comparing column by column makes each bound value use its column's
        # type; inside tuple_() they would not get the SQLite storage format.
        query = query.where(
            or_(
                Recommendation.created_at < created_at,
                and_(
                    Recommendation.created_at == created_at,
                    Recommendation.id < recommendation_id,
                ),
            )
        )

    rows = list(session.scalars(query))
    if len(rows) <= limit:
        return rows, None
    page = rows[:limit]
    return page, _encode_cursor(page[-1])


def _encode_cursor(recommendation: Recommendation) -> str:
    raw = f"{recommendation.created_at.isoformat()}|{recommendation.id}"
    return base64.urlsafe_b64encode(raw.encode()).decode()


def _decode_cursor(cursor: str) -> tuple[datetime, int]:
    try:
        raw = base64.urlsafe_b64decode(cursor.encode()).decode()
        created_at, recommendation_id = raw.split("|")
        return datetime.fromisoformat(created_at), int(recommendation_id)
    except (binascii.Error, UnicodeDecodeError, ValueError) as error:
        raise InvalidCursor() from error
