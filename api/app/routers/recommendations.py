from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from app.dependencies import CurrentUser, OptionalUser, SessionDep
from app.models import Recommendation
from app.routers.responses import error_responses
from app.schemas import (
    FeedSort,
    RecommendationCreate,
    RecommendationOut,
    RecommendationPage,
    RecommendationUpdate,
)
from app.services import recommendations as service

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    responses=error_responses(
        status.HTTP_401_UNAUTHORIZED, status.HTTP_409_CONFLICT, 422
    ),
)
def create_recommendation(
    data: RecommendationCreate, session: SessionDep, author: CurrentUser
) -> RecommendationOut:
    recommendation = service.create_recommendation(session, author, data)
    return RecommendationOut.model_validate(recommendation)


Limit = Annotated[int, Query(ge=1, le=100)]


def to_page(items: list[Recommendation], next_cursor: str | None) -> RecommendationPage:
    return RecommendationPage(
        items=[RecommendationOut.model_validate(item) for item in items],
        next_cursor=next_cursor,
    )


@router.get("", responses=error_responses(status.HTTP_401_UNAUTHORIZED, 422))
def list_recommendations(
    session: SessionDep,
    viewer: OptionalUser,
    sort: FeedSort = FeedSort.NEWEST,
    genre: str | None = None,
    author_id: int | None = None,
    cursor: str | None = None,
    limit: Limit = service.DEFAULT_PAGE_SIZE,
) -> RecommendationPage:
    """The feed. `author_id` lists one curator's recommendations (their profile)."""
    return to_page(
        *service.list_recommendations(
            session,
            viewer=viewer,
            sort=sort,
            genre=genre,
            author_id=author_id,
            cursor=cursor,
            limit=limit,
        )
    )


@router.get(
    "/{recommendation_id}",
    responses=error_responses(
        status.HTTP_401_UNAUTHORIZED, status.HTTP_404_NOT_FOUND, 422
    ),
)
def get_recommendation(
    recommendation_id: int, session: SessionDep, viewer: OptionalUser
) -> RecommendationOut:
    recommendation = service.get_recommendation(
        session, recommendation_id, viewer=viewer
    )
    return RecommendationOut.model_validate(recommendation)


@router.patch(
    "/{recommendation_id}",
    responses=error_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
        status.HTTP_409_CONFLICT,
        422,
    ),
)
def update_recommendation(
    recommendation_id: int,
    data: RecommendationUpdate,
    session: SessionDep,
    user: CurrentUser,
) -> RecommendationOut:
    recommendation = service.update_recommendation(
        session, user, recommendation_id, data
    )
    return RecommendationOut.model_validate(recommendation)


@router.delete(
    "/{recommendation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=error_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
        422,
    ),
)
def delete_recommendation(
    recommendation_id: int, session: SessionDep, user: CurrentUser
) -> Response:
    service.delete_recommendation(session, user, recommendation_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
