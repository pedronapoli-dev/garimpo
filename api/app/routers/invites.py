from fastapi import APIRouter, status

from app.dependencies import CurrentUser, SessionDep
from app.routers.responses import error_responses
from app.schemas import InviteOut
from app.services import invites as service

router = APIRouter(prefix="/invites", tags=["invites"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    responses=error_responses(status.HTTP_401_UNAUTHORIZED),
)
def create_invite(session: SessionDep, user: CurrentUser) -> InviteOut:
    return InviteOut.model_validate(service.create_invite(session, user))
