from sqlalchemy import delete
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Session

from app.models import Save, User
from app.schemas import SaveOut
from app.services.recommendations import get_recommendation


def save(session: Session, user: User, recommendation_id: int) -> SaveOut:
    """Listen later (FR6). Idempotent, like votes."""
    get_recommendation(session, recommendation_id)
    session.execute(
        insert(Save)
        .values(user_id=user.id, recommendation_id=recommendation_id)
        .on_conflict_do_nothing()
    )
    session.commit()
    return SaveOut(saved_by_me=True)


def unsave(session: Session, user: User, recommendation_id: int) -> SaveOut:
    get_recommendation(session, recommendation_id)
    session.execute(
        delete(Save).where(
            Save.user_id == user.id, Save.recommendation_id == recommendation_id
        )
    )
    session.commit()
    return SaveOut(saved_by_me=False)
