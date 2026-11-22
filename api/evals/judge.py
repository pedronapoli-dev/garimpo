"""LLM-as-judge for the curator assist evals."""

from typing import Annotated, Protocol

from pydantic import BaseModel, Field

from app.schemas import AssistResult
from evals.checks import EvalCase


class JudgeScore(BaseModel):
    score: Annotated[int, Field(ge=1, le=5)]
    reason: str


class Judge(Protocol):
    def grade(self, case: EvalCase, result: AssistResult) -> JudgeScore: ...


class FakeJudge:
    """Always satisfied: lets CI run the harness without a key."""

    def grade(self, case: EvalCase, result: AssistResult) -> JudgeScore:
        return JudgeScore(score=5, reason="fake judge")


class ClaudeJudge:
    """Grades the feedback against a rubric with Claude."""

    def __init__(self, model: str) -> None:
        self.model = model

    def grade(self, case: EvalCase, result: AssistResult) -> JudgeScore:
        # TODO(slice 7, Pedro): write the rubric prompt and call Claude.
        # - Rubric, 1 to 5: is the feedback specific to this draft, actionable,
        #   kind, short, and does it stay a review (no music recommendations)?
        # - Give the judge the draft and the feedback as data, inside tags.
        # - Parse the answer into JudgeScore with structured output.
        raise NotImplementedError("ClaudeJudge is part of the AI core (slice 7).")
