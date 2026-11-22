"""Curator assist (FR12): review a draft and suggest existing genres."""

import logging
from collections.abc import Iterator
from dataclasses import asdict

from sqlalchemy.orm import Session

from app.llm.protocol import AssistUnavailable, AssistUsage, CuratorAssistant
from app.schemas import AssistDone, AssistFailed, AssistIn, AssistResult, FeedbackDelta
from app.services.tags import list_tags

logger = logging.getLogger("garimpo.assist")

AssistEventItem = FeedbackDelta | AssistDone | AssistFailed

UNAVAILABLE = AssistFailed(
    code="assist_unavailable",
    message="The review is unavailable right now. You can still publish without it.",
)


def review(
    session: Session, assistant: CuratorAssistant, draft: AssistIn
) -> Iterator[AssistEventItem]:
    """The events of one review, ready to stream.

    Tags are read now, before streaming starts: the response body is sent
    after the route returns, when the request's session may be closed.
    """
    tags = [tag.name for tag in list_tags(session)]
    return _stream(assistant, draft, tags)


def _stream(
    assistant: CuratorAssistant, draft: AssistIn, tags: list[str]
) -> Iterator[AssistEventItem]:
    known = set(tags)
    done = False
    try:
        for item in assistant.review(draft, tags):
            if isinstance(item, FeedbackDelta):
                yield item
            elif isinstance(item, AssistResult):
                yield AssistDone(result=_only_known_genres(item, known))
                done = True
            else:
                _log_usage(item)
    except AssistUnavailable as error:
        logger.warning("assist unavailable: %s", type(error).__name__)
        yield UNAVAILABLE
        return
    if not done:
        # The model stopped without a result; the app must not wait forever.
        yield UNAVAILABLE


def _only_known_genres(result: AssistResult, known: set[str]) -> AssistResult:
    """Rule 2 and FR12: suggestions come from existing tags, whatever the model says."""
    genres = [genre for genre in result.suggested_genres if genre in known]
    return result.model_copy(update={"suggested_genres": genres})


def _log_usage(usage: AssistUsage) -> None:
    # Numbers only: the draft text never reaches the logs.
    logger.info("assist review", extra=asdict(usage))
