from fastapi import APIRouter, status

from app.dependencies import CurrentUser, SessionDep
from app.routers.responses import error_responses
from app.schemas import RecommendationCreate, RecommendationOut
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
