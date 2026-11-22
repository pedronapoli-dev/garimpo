"""The curator assist's model boundary (FR12).

This is the one Protocol in the API, because it has two real
implementations: ClaudeAssistant (claude.py) and FakeAssistant (fake.py).
"""

from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from typing import Protocol

from app.schemas import AssistIn, AssistResult, FeedbackDelta


class AssistUnavailable(Exception):
    """The model could not answer: offline, timed out, rate limited or refused."""


@dataclass(frozen=True)
class AssistUsage:
    """What one review cost. Logged by the service; never holds the user's text."""

    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: int
    cost_usd: float


AssistItem = FeedbackDelta | AssistResult | AssistUsage


class CuratorAssistant(Protocol):
    def review(self, draft: AssistIn, tags: Sequence[str]) -> Iterator[AssistItem]:
        """Streams feedback deltas, then one AssistResult, then one AssistUsage.

        `tags` are the genres that already exist; suggestions should come from
        them. Raises AssistUnavailable when the model cannot answer, possibly
        after some deltas were already yielded.
        """
        ...
