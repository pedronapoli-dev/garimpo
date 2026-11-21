from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import User
from app.services import users

SessionDep = Annotated[Session, Depends(get_session)]


def get_current_user(session: SessionDep) -> User:
    # Slice 4 replaces only this body with JWT validation.
    return users.get_dev_curator(session)


CurrentUser = Annotated[User, Depends(get_current_user)]
