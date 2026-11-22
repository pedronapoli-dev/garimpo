from fastapi import APIRouter, status

from app.dependencies import CurrentUser, SessionDep
from app.routers.recommendations import Limit, to_page
from app.routers.responses import error_responses
from app.schemas import RecommendationPage, UserProfileOut
from app.services import recommendations, users

router = APIRouter(tags=["users"])


@router.get(
    "/users/{user_id}",
    responses=error_responses(status.HTTP_404_NOT_FOUND, 422),
)
def get_user(user_id: int, session: SessionDep) -> UserProfileOut:
    return users.get_profile(session, user_id)


@router.get(
    "/me/saves",
    responses=error_responses(status.HTTP_401_UNAUTHORIZED, 422),
)
def list_my_saves(
    session: SessionDep,
    user: CurrentUser,
    cursor: str | None = None,
    limit: Limit = recommendations.DEFAULT_PAGE_SIZE,
) -> RecommendationPage:
    """The current user's "listen later" list, newest recommendations first."""
    return to_page(
        *recommendations.list_recommendations(
            session, viewer=user, saved_by=user, cursor=cursor, limit=limit
        )
    )
