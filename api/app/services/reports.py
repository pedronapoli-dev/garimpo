from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Report, User
from app.schemas import ReportIn
from app.services.exceptions import AlreadyReported
from app.services.recommendations import get_recommendation

# Rule 6. There is no moderation tooling (out of scope): a maintainer reviews
# hidden recommendations by hand, as the README describes.
REPORTS_TO_HIDE = 3


def report(
    session: Session, user: User, recommendation_id: int, data: ReportIn
) -> Report:
    recommendation = get_recommendation(session, recommendation_id)
    already = session.scalar(
        select(Report.id).where(
            Report.user_id == user.id, Report.recommendation_id == recommendation_id
        )
    )
    if already is not None:
        raise AlreadyReported()

    created = Report(
        user_id=user.id, recommendation_id=recommendation_id, reason=data.reason
    )
    session.add(created)
    session.flush()

    count = session.scalar(
        select(func.count()).where(Report.recommendation_id == recommendation_id)
    )
    if (count or 0) >= REPORTS_TO_HIDE:
        recommendation.hidden = True

    session.commit()
    return created
