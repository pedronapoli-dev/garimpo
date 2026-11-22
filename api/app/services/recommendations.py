import base64
import binascii
from datetime import datetime

from sqlalchemy import ColumnElement, Select, and_, exists, false, func, or_, select
from sqlalchemy.orm import Session, joinedload, selectinload, with_expression

from app.models import Recommendation, RecommendationType, Save, Tag, User, Vote
from app.normalization import normalize_key
from app.schemas import (
    FeedSort,
    RecommendationCreate,
    RecommendationUpdate,
    check_title_for_type,
)
from app.services.exceptions import (
    DuplicateRecommendation,
    InvalidCursor,
    InvalidRecommendation,
    NotAuthor,
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
    # Reload with the per-viewer fields (vote_count, voted_by_me, saved_by_me).
    return get_recommendation(session, recommendation.id, viewer=author)


def update_recommendation(
    session: Session, user: User, recommendation_id: int, data: RecommendationUpdate
) -> Recommendation:
    """Partial update: only the fields present in the request body change."""
    recommendation = _get_own_recommendation(session, user, recommendation_id)
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
    return get_recommendation(session, recommendation.id, viewer=user)


def delete_recommendation(session: Session, user: User, recommendation_id: int) -> None:
    session.delete(_get_own_recommendation(session, user, recommendation_id))
    session.commit()


def _get_own_recommendation(
    session: Session, user: User, recommendation_id: int
) -> Recommendation:
    """Rule 5: only the author can edit or delete."""
    recommendation = get_recommendation(session, recommendation_id)
    if recommendation.author_id != user.id:
        raise NotAuthor()
    return recommendation


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


# Per-viewer fields, computed in SQL for every query (see query_expression in
# models.py). Correlated subqueries: one small lookup per returned row.
_vote_count = (
    select(func.count())
    .where(Vote.recommendation_id == Recommendation.id)
    .correlate(Recommendation)
    .scalar_subquery()
)


def _select(viewer: User | None) -> Select[tuple[Recommendation]]:
    """A SELECT of recommendations with author, tags and the viewer's state."""
    if viewer is None:
        voted_by_me: ColumnElement[bool] = false()
        saved_by_me: ColumnElement[bool] = false()
    else:
        voted_by_me = exists().where(
            Vote.recommendation_id == Recommendation.id, Vote.user_id == viewer.id
        )
        saved_by_me = exists().where(
            Save.recommendation_id == Recommendation.id, Save.user_id == viewer.id
        )
    return (
        select(Recommendation)
        .options(
            joinedload(Recommendation.author),
            selectinload(Recommendation.tags),
            with_expression(Recommendation.vote_count, _vote_count),
            with_expression(Recommendation.voted_by_me, voted_by_me),
            with_expression(Recommendation.saved_by_me, saved_by_me),
        )
        # Refresh objects already in the session, so the expressions are recomputed.
        .execution_options(populate_existing=True)
    )


def get_recommendation(
    session: Session, recommendation_id: int, *, viewer: User | None = None
) -> Recommendation:
    recommendation = session.scalars(
        _select(viewer).where(Recommendation.id == recommendation_id)
    ).one_or_none()
    if recommendation is None:
        raise RecommendationNotFound(recommendation_id)
    return recommendation


def list_recommendations(
    session: Session,
    *,
    viewer: User | None = None,
    sort: FeedSort = FeedSort.NEWEST,
    genre: str | None = None,
    author_id: int | None = None,
    saved_by: User | None = None,
    cursor: str | None = None,
    limit: int = DEFAULT_PAGE_SIZE,
) -> tuple[list[Recommendation], str | None]:
    """One page of recommendations and the cursor for the next one.

    The feed, a curator's profile (author_id) and the saved list (saved_by)
    are all this query with a different filter.
    """
    if sort is FeedSort.TOP:
        key, order = _vote_count, Recommendation.vote_count
    else:
        key, order = Recommendation.created_at, Recommendation.created_at

    query = (
        _select(viewer)
        .order_by(key.desc(), Recommendation.id.desc())
        # One extra row tells whether there is a next page.
        .limit(limit + 1)
    )
    if genre is not None:
        query = query.where(Recommendation.tags.any(Tag.name == normalize_key(genre)))
    if author_id is not None:
        query = query.where(Recommendation.author_id == author_id)
    if saved_by is not None:
        query = query.where(
            exists().where(
                Save.recommendation_id == Recommendation.id, Save.user_id == saved_by.id
            )
        )
    if cursor is not None:
        position, recommendation_id = _decode_cursor(cursor, sort)
        # Rows strictly after the cursor in (key desc, id desc) order.
        # Comparing column by column makes each bound value use its column's
        # type; inside tuple_() they would not get the SQLite storage format.
        query = query.where(
            or_(
                key < position,
                and_(key == position, Recommendation.id < recommendation_id),
            )
        )

    rows = list(session.scalars(query))
    if len(rows) <= limit:
        return rows, None
    page = rows[:limit]
    last = page[-1]
    return page, _encode_cursor(sort, getattr(last, order.key), last.id)


def _encode_cursor(
    sort: FeedSort, position: datetime | int, recommendation_id: int
) -> str:
    value = position.isoformat() if isinstance(position, datetime) else str(position)
    raw = f"{sort}|{value}|{recommendation_id}"
    return base64.urlsafe_b64encode(raw.encode()).decode()


def _decode_cursor(cursor: str, sort: FeedSort) -> tuple[datetime | int, int]:
    try:
        raw = base64.urlsafe_b64decode(cursor.encode()).decode()
        cursor_sort, value, recommendation_id = raw.split("|")
        if cursor_sort != sort:
            raise ValueError("the cursor belongs to another sort order")
        position = int(value) if sort is FeedSort.TOP else datetime.fromisoformat(value)
        return position, int(recommendation_id)
    except (binascii.Error, UnicodeDecodeError, ValueError) as error:
        raise InvalidCursor() from error
