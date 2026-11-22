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


CurrentUser = Annotated[User, Depends(get_current_user)]
