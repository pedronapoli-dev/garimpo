"""A deterministic CuratorAssistant for tests, evals and running without a key."""

from collections.abc import Iterator, Sequence

from app.llm.protocol import AssistItem, AssistUnavailable, AssistUsage
from app.schemas import AssistIn, AssistResult, FeedbackDelta

MIN_LENGTH = 80
# Words that usually mean the text says what to listen for.
WHY_WORDS = ("why", "because", "listen", "sounds", "arrangement", "voice")
CHUNK_SIZE = 16

EXPLAINS = "The text tells a new listener what to listen for."
VAGUE = "Say what the music sounds like and why someone should listen."


class FakeAssistant:
    def __init__(
        self, *, suggest: list[str] | None = None, fail_after: int | None = None
    ) -> None:
        self.suggest = suggest
        self.fail_after = fail_after

    def review(self, draft: AssistIn, tags: Sequence[str]) -> Iterator[AssistItem]:
        text = draft.text.casefold()
        explains_why = len(draft.text) >= MIN_LENGTH and any(
            word in text for word in WHY_WORDS
        )
        feedback = EXPLAINS if explains_why else VAGUE

        for sent, start in enumerate(range(0, len(feedback), CHUNK_SIZE)):
            if sent == self.fail_after:
                raise AssistUnavailable("fake failure")
            yield FeedbackDelta(text=feedback[start : start + CHUNK_SIZE])

        suggested = self.suggest
        if suggested is None:
            suggested = [tag for tag in tags if tag in text]
        yield AssistResult(
            explains_why=explains_why, feedback=feedback, suggested_genres=suggested
        )
        yield AssistUsage(
            model="fake", input_tokens=0, output_tokens=0, latency_ms=0, cost_usd=0.0
        )
