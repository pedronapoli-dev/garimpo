from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import User
from app.services import auth

SessionDep = Annotated[Session, Depends(get_session)]

# auto_error=False: a missing header reaches get_current_user, which raises the
# domain error, so the 401 body is an ErrorOut like every other error.
_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    session: SessionDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User:
    token = credentials.credentials if credentials is not None else None
    return auth.authenticate(session, token)


def get_optional_user(
    session: SessionDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User | None:
    """For public routes that add per-user fields (voted_by_me, saved_by_me).

    No token means an anonymous reader. A token that fails still raises 401,
    so the app finds out that its session expired.
    """
    if credentials is None:
        return None
    return auth.authenticate(session, credentials.credentials)


CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[User | None, Depends(get_optional_user)]
