import logging
from collections.abc import Iterator, Sequence

import pytest
from sqlalchemy.orm import Session

from app.llm.fake import FakeAssistant
from app.llm.protocol import AssistItem
from app.models import RecommendationType, Tag
from app.schemas import AssistDone, AssistFailed, AssistIn, FeedbackDelta
from app.services import assist

SECRET_TEXT = (
    "Listen for the strings: Verocai arranged this jazz record in 1972, and "
    "the private-marker-7f3a sounds like nothing else."
)


def draft() -> AssistIn:
    return AssistIn(
        type=RecommendationType.ALBUM,
        artist="Arthur Verocai",
        title="Arthur Verocai",
        text=SECRET_TEXT,
    )


@pytest.fixture
def tags(session: Session) -> None:
    session.add_all([Tag(name="jazz"), Tag(name="mpb")])
    session.commit()


@pytest.mark.usefixtures("tags")
def test_review_streams_feedback_then_done(session: Session) -> None:
    events = list(assist.review(session, FakeAssistant(), draft()))

    deltas = [event for event in events if isinstance(event, FeedbackDelta)]
    done = events[-1]
    assert deltas
    assert isinstance(done, AssistDone)
    assert done.result.suggested_genres == ["jazz"]
    assert "".join(delta.text for delta in deltas) == done.result.feedback


@pytest.mark.usefixtures("tags")
def test_review_drops_genres_that_do_not_exist(session: Session) -> None:
    assistant = FakeAssistant(suggest=["vaporwave", "mpb", "jazz"])

    done = list(assist.review(session, assistant, draft()))[-1]

    assert isinstance(done, AssistDone)
    assert done.result.suggested_genres == ["mpb", "jazz"]


@pytest.mark.usefixtures("tags")
def test_review_reads_tags_before_streaming(session: Session) -> None:
    events = assist.review(session, FakeAssistant(suggest=["samba"]), draft())
    # Streaming happens after the route returns; the tags must already be read.
    session.add(Tag(name="samba"))
    session.commit()

    done = list(events)[-1]

    assert isinstance(done, AssistDone)
    assert done.result.suggested_genres == []


@pytest.mark.usefixtures("tags")
def test_review_failure_ends_the_stream_with_an_error(session: Session) -> None:
    events = list(assist.review(session, FakeAssistant(fail_after=2), draft()))

    assert [type(event) for event in events] == [
        FeedbackDelta,
        FeedbackDelta,
        AssistFailed,
    ]
    failed = events[-1]
    assert isinstance(failed, AssistFailed)
    assert failed.code == "assist_unavailable"


class NoResultAssistant:
    def review(self, draft: AssistIn, tags: Sequence[str]) -> Iterator[AssistItem]:
        yield FeedbackDelta(text="Half a thought")


def test_review_without_a_result_ends_with_an_error(session: Session) -> None:
    events = list(assist.review(session, NoResultAssistant(), draft()))

    failed = events[-1]
    assert isinstance(failed, AssistFailed)
    assert failed.code == "assist_unavailable"


@pytest.mark.usefixtures("tags")
def test_review_logs_usage_without_the_draft_text(
    session: Session, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.INFO, logger="garimpo.assist"):
        list(assist.review(session, FakeAssistant(), draft()))

    [record] = caplog.records
    assert record.__dict__["model"] == "fake"
    assert record.__dict__["output_tokens"] == 0
    assert "private-marker-7f3a" not in repr(record.__dict__)
