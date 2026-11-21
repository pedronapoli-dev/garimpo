from typing import Annotated

from fastapi import APIRouter, Query, status

from app.dependencies import CurrentUser, SessionDep
from app.routers.responses import error_responses
from app.schemas import RecommendationCreate, RecommendationOut, RecommendationPage
from app.services import recommendations as service

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    responses=error_responses(status.HTTP_409_CONFLICT, 422),
)
def create_recommendation(
    data: RecommendationCreate, session: SessionDep, author: CurrentUser
) -> RecommendationOut:
    recommendation = service.create_recommendation(session, author, data)
    return RecommendationOut.model_validate(recommendation)


@router.get("", responses=error_responses(422))
def list_recommendations(
    session: SessionDep,
    genre: str | None = None,
    cursor: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = service.DEFAULT_PAGE_SIZE,
) -> RecommendationPage:
    items, next_cursor = service.list_recommendations(
        session, genre=genre, cursor=cursor, limit=limit
    )
    return RecommendationPage(
        items=[RecommendationOut.model_validate(item) for item in items],
        next_cursor=next_cursor,
    )


@router.get(
    "/{recommendation_id}",
    responses=error_responses(status.HTTP_404_NOT_FOUND, 422),
)
def get_recommendation(
    recommendation_id: int, session: SessionDep
) -> RecommendationOut:
    recommendation = service.get_recommendation(session, recommendation_id)
    return RecommendationOut.model_validate(recommendation)
