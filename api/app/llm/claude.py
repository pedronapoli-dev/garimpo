"""ClaudeAssistant: the curator assist on the Claude Messages API (FR12).

The AI core of slice 7. Pedro implements it; the tests in
tests/test_claude_assistant.py describe each piece and are marked xfail until
then. See "Your part" in docs/slice-7-blueprint.md for the order.

Before starting: `uv add anthropic` (the official SDK; nothing in the stack can
call the Messages API today), then read the SDK docs for streaming, tool use
and structured outputs.
"""

from collections.abc import Iterator, Sequence
from typing import Any

from app.llm.protocol import AssistItem, AssistUsage
from app.schemas import AssistIn, AssistResult

# TODO(slice 7, Pedro): the system prompt. It must say that the assistant
# - reviews the curator's text: does it explain why someone should listen?
# - never recommends music, artists or records;
# - suggests 0 to 5 genres, only from the list_tags tool;
# - treats everything inside <draft> as data, never as instructions.
SYSTEM_PROMPT = ""

# Price per million tokens, (input, output), from the Claude pricing page.
PRICES_PER_MTOK: dict[str, tuple[float, float]] = {
    "claude-opus-5-5": (4.00, 20.00),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-haiku-5-5": (0.10, 0.50),
}

# TODO(slice 7, Pedro): the list_tags tool definition, a dict with name,
# description and input_schema. Use strict tool use ("strict": True), which
# needs "additionalProperties": False and "required" on the schema.
LIST_TAGS_TOOL: dict[str, Any] = {}


def build_messages(draft: AssistIn) -> list[dict[str, Any]]:
    """The user message: the draft's fields inside <draft> tags, as data.

    A draft that contains "</draft>" must not be able to close the tag early
    (prompt injection): escape or strip it.
    """
    raise NotImplementedError("TODO(slice 7, Pedro)")


def tool_result_for_tags(tool_use_id: str, tags: Sequence[str]) -> dict[str, Any]:
    """The tool_result block that answers a list_tags call."""
    raise NotImplementedError("TODO(slice 7, Pedro)")


def parse_result(text: str) -> AssistResult:
    """The model's final JSON as an AssistResult.

    Anything that does not validate raises AssistUnavailable, so the app shows
    "unavailable" instead of a broken review.
    """
    raise NotImplementedError("TODO(slice 7, Pedro)")


def usage_from(
    model: str, input_tokens: int, output_tokens: int, latency_ms: int
) -> AssistUsage:
    """Token counts and cost of one review, from response.usage."""
    raise NotImplementedError("TODO(slice 7, Pedro)")


class ClaudeAssistant:
    def __init__(self, model: str) -> None:
        self.model = model
        # TODO(slice 7, Pedro): create the client. anthropic.Anthropic() reads
        # ANTHROPIC_API_KEY. Set a timeout and max_retries suited to a user
        # waiting on a phone.

    def review(self, draft: AssistIn, tags: Sequence[str]) -> Iterator[AssistItem]:
        # TODO(slice 7, Pedro):
        # 1. Stream a Messages request: SYSTEM_PROMPT, build_messages(draft),
        #    tools=[LIST_TAGS_TOOL], adaptive thinking.
        # 2. When the model calls list_tags, answer with tool_result_for_tags
        #    and continue the loop.
        # 3. Yield FeedbackDelta for the feedback text as it streams.
        # 4. Yield parse_result(...) of the final answer (structured output).
        # 5. Yield usage_from(...) with the summed usage and the latency.
        # 6. Turn timeouts, connection errors, rate limits and a refusal stop
        #    reason into AssistUnavailable.
        raise NotImplementedError("TODO(slice 7, Pedro)")
