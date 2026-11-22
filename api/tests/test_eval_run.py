from pathlib import Path

import pytest

from app.llm.fake import FakeAssistant
from app.schemas import AssistResult
from evals.checks import EvalCase
from evals.judge import FakeJudge, JudgeScore
from evals.run import CASES_PATH, evaluate, load_cases, main


@pytest.fixture
def cases() -> list[EvalCase]:
    return load_cases(CASES_PATH)


def test_seed_cases_cover_good_vague_and_injection_drafts(
    cases: list[EvalCase],
) -> None:
    ids = [case.id for case in cases]

    assert len(ids) == len(set(ids)) >= 6
    assert sum(case.expect.explains_why for case in cases) >= 2
    assert sum(bool(case.forbidden_terms) for case in cases) >= 2


def test_the_fake_passes_every_seed_case(cases: list[EvalCase]) -> None:
    report = evaluate(cases, FakeAssistant(), FakeJudge())

    assert [case.failures for case in report.cases] == [[]] * len(cases)
    assert report.passed is True


def test_invented_genres_fail_the_report(cases: list[EvalCase]) -> None:
    report = evaluate(cases, FakeAssistant(suggest=["vaporwave"]), FakeJudge())

    assert report.passed is False
    assert "invented genre: vaporwave" in report.cases[0].failures


def test_an_unavailable_assistant_fails_each_case(cases: list[EvalCase]) -> None:
    report = evaluate(cases, FakeAssistant(fail_after=0), FakeJudge())

    assert all(case.failures == ["assist unavailable"] for case in report.cases)
    assert report.passed is False


class LowJudge:
    def grade(self, case: EvalCase, result: AssistResult) -> JudgeScore:
        return JudgeScore(score=2, reason="Vague feedback.")


def test_a_low_judge_score_fails_the_report(cases: list[EvalCase]) -> None:
    report = evaluate(cases, FakeAssistant(), LowJudge())

    assert report.mean_score == 2
    assert report.passed is False


def test_main_with_the_fake_exits_zero_and_prints_a_summary(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main([]) == 0
    assert "passed" in capsys.readouterr().out


def test_load_cases_reads_one_case_per_line(tmp_path: Path) -> None:
    path = tmp_path / "cases.jsonl"
    line = (
        '{"id": "a", "draft": {"type": "artist", "artist": "Azymuth", '
        '"text": "Great."}, "tags": [], "expect": {"explains_why": false}}'
    )
    path.write_text(f"{line}\n\n")

    assert [case.id for case in load_cases(path)] == ["a"]
