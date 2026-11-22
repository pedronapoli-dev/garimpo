"""Run the curator assist evals: `uv run python -m evals.run [--live]`.

Without --live it uses the fake assistant and judge, which CI always runs.
With --live it calls Claude and costs money; see docs/slice-7-blueprint.md.
"""

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path

from app.llm.protocol import AssistUnavailable, CuratorAssistant
from app.schemas import AssistResult
from evals.checks import EvalCase, check_result
from evals.judge import Judge

CASES_PATH = Path(__file__).parent / "cases.jsonl"
# The gate: every deterministic check passes and the judge's mean is this high.
MIN_MEAN_SCORE = 4.0


@dataclass
class CaseReport:
    id: str
    failures: list[str]
    score: int | None = None
    reason: str = ""


@dataclass
class Report:
    cases: list[CaseReport] = field(default_factory=list)

    @property
    def mean_score(self) -> float:
        scores = [case.score for case in self.cases if case.score is not None]
        return sum(scores) / len(scores) if scores else 0.0

    @property
    def passed(self) -> bool:
        no_failures = all(not case.failures for case in self.cases)
        return no_failures and self.mean_score >= MIN_MEAN_SCORE


def load_cases(path: Path) -> list[EvalCase]:
    lines = path.read_text().splitlines()
    return [EvalCase.model_validate_json(line) for line in lines if line.strip()]


def evaluate(
    cases: list[EvalCase], assistant: CuratorAssistant, judge: Judge
) -> Report:
    report = Report()
    for case in cases:
        result = _review(assistant, case)
        if result is None:
            report.cases.append(CaseReport(case.id, ["assist unavailable"]))
            continue
        score = judge.grade(case, result)
        report.cases.append(
            CaseReport(case.id, check_result(case, result), score.score, score.reason)
        )
    return report


def _review(assistant: CuratorAssistant, case: EvalCase) -> AssistResult | None:
    # Calls the assistant directly, without the service's tag filter: the eval
    # measures whether the model itself invents genres.
    try:
        for item in assistant.review(case.draft, case.tags):
            if isinstance(item, AssistResult):
                return item
    except AssistUnavailable:
        return None
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="call Claude (costs)")
    args = parser.parse_args(argv)

    if args.live:
        from app.llm.claude import ClaudeAssistant
        from app.settings import ASSIST_MODEL
        from evals.judge import ClaudeJudge

        assistant: CuratorAssistant = ClaudeAssistant(model=ASSIST_MODEL)
        judge: Judge = ClaudeJudge(model=ASSIST_MODEL)
    else:
        from app.llm.fake import FakeAssistant
        from evals.judge import FakeJudge

        assistant, judge = FakeAssistant(), FakeJudge()

    report = evaluate(load_cases(CASES_PATH), assistant, judge)
    for case in report.cases:
        status = "ok  " if not case.failures else "FAIL"
        print(f"{status} {case.id} score={case.score} {'; '.join(case.failures)}")
    verdict = "passed" if report.passed else "failed"
    print(f"{verdict}: mean score {report.mean_score:.1f} (gate {MIN_MEAN_SCORE})")
    return 0 if report.passed else 1


if __name__ == "__main__":
    sys.exit(main())
