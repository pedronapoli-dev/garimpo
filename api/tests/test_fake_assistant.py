import pytest

from app.llm.fake import FakeAssistant
from app.llm.protocol import AssistUnavailable, AssistUsage
from app.models import RecommendationType
from app.schemas import AssistIn, AssistResult, FeedbackDelta

TAGS = ["jazz", "mpb", "samba"]
WHY = (
    "Listen for the strings: Verocai arranged this record in 1972 and it sounds "
    "like jazz and mpb at once."
)


def draft(text: str) -> AssistIn:
    return AssistIn(
        type=RecommendationType.ALBUM,
        artist="Arthur Verocai",
        title="Arthur",
        text=text,
    )


def run(assistant: FakeAssistant, text: str) -> list[object]:
    return list(assistant.review(draft(text), TAGS))


def test_streams_feedback_then_result_then_usage() -> None:
    items = run(FakeAssistant(), WHY)

    deltas = [item for item in items if isinstance(item, FeedbackDelta)]
    result, usage = items[-2], items[-1]
    assert len(deltas) > 1
    assert isinstance(result, AssistResult)
    assert "".join(delta.text for delta in deltas) == result.feedback
    assert isinstance(usage, AssistUsage)
    assert usage.model == "fake"


def test_long_text_with_a_why_word_explains_why() -> None:
    result = run(FakeAssistant(), WHY)[-2]

    assert isinstance(result, AssistResult)
    assert result.explains_why is True


@pytest.mark.parametrize(
    "text",
    ["Listen to it.", "A very long text that never says anything at all. " * 3],
)
def test_short_or_vague_text_does_not_explain_why(text: str) -> None:
    result = run(FakeAssistant(), text)[-2]

    assert isinstance(result, AssistResult)
    assert result.explains_why is False


def test_suggests_the_tags_named_in_the_text() -> None:
    result = run(FakeAssistant(), WHY)[-2]

    assert isinstance(result, AssistResult)
    assert result.suggested_genres == ["jazz", "mpb"]


def test_suggest_overrides_the_genres() -> None:
    result = run(FakeAssistant(suggest=["vaporwave"]), WHY)[-2]

    assert isinstance(result, AssistResult)
    assert result.suggested_genres == ["vaporwave"]


def test_fail_after_raises_once_that_many_deltas_were_sent() -> None:
    received: list[object] = []

    with pytest.raises(AssistUnavailable):
        # extend() keeps the items yielded before the exception.
        received.extend(FakeAssistant(fail_after=2).review(draft(WHY), TAGS))

    assert len(received) == 2
    assert all(isinstance(item, FeedbackDelta) for item in received)
