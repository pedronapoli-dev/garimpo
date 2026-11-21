from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Recommendation, RecommendationType, Tag, User
from app.normalization import normalize_key
from app.schemas import RecommendationCreate
from app.services.exceptions import DuplicateRecommendation


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


def _ensure_unique(
    session: Session,
    type_: RecommendationType,
    artist_key: str,
    title_key: str,
) -> None:
    """Rule 7. The unique index also guards it; this check finds the existing id."""
    query = select(Recommendation.id).where(
        Recommendation.type == type_,
        Recommendation.artist_key == artist_key,
        Recommendation.title_key == title_key,
    )
    existing_id = session.scalar(query)
    if existing_id is not None:
        raise DuplicateRecommendation(existing_id)


def _get_or_create_tags(session: Session, names: list[str]) -> list[Tag]:
    existing = {
        tag.name: tag for tag in session.scalars(select(Tag).where(Tag.name.in_(names)))
    }
    return [existing.get(name) or Tag(name=name) for name in names]
