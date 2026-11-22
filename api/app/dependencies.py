from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app import settings
from app.db import get_session
from app.llm.claude import ClaudeAssistant, create_client
from app.llm.fake import FakeAssistant
from app.llm.protocol import CuratorAssistant
from app.models import User
from app.services import auth
from app.services.exceptions import AssistDisabled

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


@lru_cache
def _claude_assistant(model: str, provider: str) -> ClaudeAssistant:
    # One instance per process, so requests share its HTTP connections.
    return ClaudeAssistant(model=model, client=create_client(provider))


def get_assistant() -> CuratorAssistant | None:
    """The curator assist, or None when the server has none (FR12 is optional)."""
    if settings.ASSIST_FAKE:
        return FakeAssistant()
    # Bedrock authenticates with the server's AWS credentials instead of a key.
    if settings.ASSIST_PROVIDER == "anthropic" and not settings.ASSIST_HAS_API_KEY:
        return None
    return _claude_assistant(settings.ASSIST_MODEL, settings.ASSIST_PROVIDER)


def require_assistant(
    assistant: Annotated[CuratorAssistant | None, Depends(get_assistant)],
) -> CuratorAssistant:
    # Raised in a dependency, before the stream starts, so it is a normal 503.
    if assistant is None:
        raise AssistDisabled()
    return assistant


OptionalAssistant = Annotated[CuratorAssistant | None, Depends(get_assistant)]
Assistant = Annotated[CuratorAssistant, Depends(require_assistant)]
