from fastapi import APIRouter, status

from app.dependencies import CurrentUser, SessionDep
from app.routers.responses import error_responses
from app.schemas import SaveOut, VoteOut
from app.services import saves, votes

# Idempotent PUT and DELETE that return the new state, so the app can retry an
# optimistic update and reconcile it with the server.
router = APIRouter(
    prefix="/recommendations/{recommendation_id}", tags=["votes and saves"]
)

ERRORS = error_responses(status.HTTP_401_UNAUTHORIZED, status.HTTP_404_NOT_FOUND, 422)


@router.put(
    "/vote",
    responses=error_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
        422,
    ),
)
def vote_recommendation(
    recommendation_id: int, session: SessionDep, user: CurrentUser
) -> VoteOut:
    return votes.vote(session, user, recommendation_id)


@router.delete("/vote", responses=ERRORS)
def unvote_recommendation(
    recommendation_id: int, session: SessionDep, user: CurrentUser
) -> VoteOut:
    return votes.unvote(session, user, recommendation_id)


@router.put("/save", responses=ERRORS)
def save_recommendation(
    recommendation_id: int, session: SessionDep, user: CurrentUser
) -> SaveOut:
    return saves.save(session, user, recommendation_id)


@router.delete("/save", responses=ERRORS)
def unsave_recommendation(
    recommendation_id: int, session: SessionDep, user: CurrentUser
) -> SaveOut:
    return saves.unsave(session, user, recommendation_id)
