from collections.abc import Iterator

from fastapi import APIRouter, status
from fastapi.sse import EventSourceResponse

from app.dependencies import Assistant, CurrentUser, OptionalAssistant, SessionDep
from app.routers.responses import error_responses
from app.schemas import AssistEvent, AssistIn, AssistStatusOut
from app.services import assist as service

router = APIRouter(prefix="/assist", tags=["assist"])


@router.get("/status")
def get_assist_status(assistant: OptionalAssistant) -> AssistStatusOut:
    """Whether the server has a curator assist. The app hides it when not."""
    return AssistStatusOut(enabled=assistant is not None)


@router.post(
    "/review",
    response_class=EventSourceResponse,
    responses=error_responses(
        status.HTTP_401_UNAUTHORIZED, status.HTTP_503_SERVICE_UNAVAILABLE, 422
    ),
)
def review_draft(
    draft: AssistIn, session: SessionDep, user: CurrentUser, assistant: Assistant
) -> Iterator[AssistEvent]:
    """Streams the review as server-sent events: deltas, then done or error."""
    yield from service.review(session, assistant, draft)
