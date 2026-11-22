from sqlalchemy import delete, func, select
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Session

from app.models import User, Vote
from app.schemas import VoteOut
from app.services.exceptions import OwnRecommendation
from app.services.recommendations import get_recommendation


def vote(session: Session, user: User, recommendation_id: int) -> VoteOut:
    """Rule 4: one vote per user, never on your own. Voting twice is a no-op."""
    recommendation = get_recommendation(session, recommendation_id)
    if recommendation.author_id == user.id:
        raise OwnRecommendation()

    # INSERT ... ON CONFLICT DO NOTHING: idempotent, so the app can retry.
    session.execute(
        insert(Vote)
        .values(user_id=user.id, recommendation_id=recommendation_id)
        .on_conflict_do_nothing()
    )
    session.commit()
    return _state(session, recommendation_id, voted_by_me=True)


def unvote(session: Session, user: User, recommendation_id: int) -> VoteOut:
    """Removing a vote that does not exist is a no-op, for the same reason."""
    get_recommendation(session, recommendation_id)
    session.execute(
        delete(Vote).where(
            Vote.user_id == user.id, Vote.recommendation_id == recommendation_id
        )
    )
    session.commit()
    return _state(session, recommendation_id, voted_by_me=False)


def _state(session: Session, recommendation_id: int, *, voted_by_me: bool) -> VoteOut:
    count = session.scalar(
        select(func.count()).where(Vote.recommendation_id == recommendation_id)
    )
    return VoteOut(vote_count=count or 0, voted_by_me=voted_by_me)
