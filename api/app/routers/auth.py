from fastapi import APIRouter, status

from app.dependencies import SessionDep
from app.models import User
from app.routers.responses import error_responses
from app.schemas import CurrentUserOut, LoginIn, SessionOut, SignupIn
from app.services import auth as service

router = APIRouter(prefix="/auth", tags=["auth"])


def _session_out(user: User) -> SessionOut:
    return SessionOut(
        access_token=service.create_access_token(user),
        user=CurrentUserOut.model_validate(user),
    )


@router.post(
    "/signup",
    status_code=status.HTTP_201_CREATED,
    responses=error_responses(status.HTTP_409_CONFLICT, 422),
)
def signup(data: SignupIn, session: SessionDep) -> SessionOut:
    return _session_out(service.signup(session, data))


# Logout has no endpoint: the token is stateless, so the app deletes it.
@router.post("/login", responses=error_responses(status.HTTP_401_UNAUTHORIZED, 422))
def login(data: LoginIn, session: SessionDep) -> SessionOut:
    return _session_out(service.login(session, data))
