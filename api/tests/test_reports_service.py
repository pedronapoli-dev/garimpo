import pytest
from sqlalchemy.orm import Session

from app.models import Recommendation, User
from app.schemas import ReportIn
from app.services import recommendations, reports, users
from app.services.exceptions import AlreadyReported, RecommendationNotFound
from tests.conftest import make_recommendation, make_user

REASON = ReportIn(reason="Millions of monthly listeners, not lesser-known.")


def report_by(session: Session, count: int, recommendation: Recommendation) -> None:
    for index in range(count):
        reporter = make_user(session, email=f"reporter{index}@example.com")
        reports.report(session, reporter, recommendation.id, REASON)


def test_report_stores_reason(session: Session, curator: User) -> None:
    recommendation = make_recommendation(session, curator)
    reporter = make_user(session, email="reporter@example.com")

    created = reports.report(session, reporter, recommendation.id, REASON)

    assert created.reason == REASON.reason
    assert created.user_id == reporter.id


# Rule 6


def test_two_reports_keep_recommendation_visible(
    session: Session, curator: User
) -> None:
    recommendation = make_recommendation(session, curator)

    report_by(session, 2, recommendation)

    assert session.get_one(Recommendation, recommendation.id).hidden is False
    items, _ = recommendations.list_recommendations(session)
    assert [item.id for item in items] == [recommendation.id]


def test_third_report_hides_from_every_list(session: Session, curator: User) -> None:
    recommendation = make_recommendation(session, curator)
    other = make_recommendation(session, curator, title="Other", title_key="other")

    report_by(session, 3, recommendation)

    assert session.get_one(Recommendation, recommendation.id).hidden is True
    feed, _ = recommendations.list_recommendations(session)
    profile, _ = recommendations.list_recommendations(session, author_id=curator.id)
    assert [item.id for item in feed] == [other.id]
    assert [item.id for item in profile] == [other.id]
    assert users.get_profile(session, curator.id).recommendation_count == 1


def test_reports_on_other_recommendations_do_not_count(
    session: Session, curator: User
) -> None:
    reported = make_recommendation(session, curator)
    other = make_recommendation(session, curator, title="Other", title_key="other")
    report_by(session, 2, reported)

    reports.report(
        session, make_user(session, email="third@example.com"), other.id, REASON
    )

    assert session.get_one(Recommendation, other.id).hidden is False


def test_hidden_recommendation_detail_still_loads(
    session: Session, curator: User
) -> None:
    recommendation = make_recommendation(session, curator)
    report_by(session, 3, recommendation)

    assert recommendations.get_recommendation(session, recommendation.id).hidden is True


def test_same_user_reporting_twice_raises(session: Session, curator: User) -> None:
    recommendation = make_recommendation(session, curator)
    reporter = make_user(session, email="reporter@example.com")
    reports.report(session, reporter, recommendation.id, REASON)

    with pytest.raises(AlreadyReported):
        reports.report(session, reporter, recommendation.id, REASON)


def test_report_missing_recommendation_raises(session: Session, curator: User) -> None:
    with pytest.raises(RecommendationNotFound):
        reports.report(session, curator, 999, REASON)
