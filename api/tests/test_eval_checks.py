from app.schemas import AssistResult
from evals.checks import EvalCase, check_result

CASE = EvalCase.model_validate(
    {
        "id": "vague",
        "draft": {
            "type": "artist",
            "artist": "Azymuth",
            "text": "Great band, love it.",
        },
        "tags": ["jazz", "samba"],
        "expect": {"explains_why": False},
        "forbidden_terms": ["Marcos Valle"],
    }
)


def result(**overrides: object) -> AssistResult:
    fields: dict[str, object] = {
        "explains_why": False,
        "feedback": "Say what the band sounds like.",
        "suggested_genres": ["jazz"],
    }
    return AssistResult.model_validate(fields | overrides)


def test_a_good_result_has_no_failures() -> None:
    assert check_result(CASE, result()) == []


def test_a_genre_outside_the_tags_fails() -> None:
    failures = check_result(CASE, result(suggested_genres=["jazz", "vaporwave"]))

    assert failures == ["invented genre: vaporwave"]


def test_the_wrong_explains_why_verdict_fails() -> None:
    assert check_result(CASE, result(explains_why=True)) == [
        "explains_why is True, expected False"
    ]


def test_a_forbidden_term_in_the_feedback_fails_ignoring_case() -> None:
    failures = check_result(CASE, result(feedback="Try MARCOS VALLE next."))

    assert failures == ["feedback mentions a forbidden term: Marcos Valle"]


def test_every_failure_is_reported() -> None:
    failures = check_result(
        CASE,
        result(explains_why=True, feedback="Marcos Valle", suggested_genres=["x"]),
    )

    assert len(failures) == 3
