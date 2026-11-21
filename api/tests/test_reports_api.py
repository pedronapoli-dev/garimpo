from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import User
from tests.conftest import auth_headers, make_recommendation, make_user


def test_report_returns_201(
    client: TestClient, session: Session, curator: User
) -> None:
    recommendation = make_recommendation(session, curator)

    response = client.post(
        f"/recommendations/{recommendation.id}/reports",
        json={"reason": " Too famous. "},
    )

    assert response.status_code == 201
    assert response.json()["reason"] == "Too famous."


def test_report_twice_returns_409(
    client: TestClient, session: Session, curator: User
) -> None:
    recommendation = make_recommendation(session, curator)
    url = f"/recommendations/{recommendation.id}/reports"
    client.post(url, json={"reason": "Too famous."})

    response = client.post(url, json={"reason": "Again."})

    assert response.status_code == 409
    assert response.json()["code"] == "already_reported"


def test_report_without_reason_returns_422(
    client: TestClient, session: Session, curator: User
) -> None:
    recommendation = make_recommendation(session, curator)

    response = client.post(
        f"/recommendations/{recommendation.id}/reports", json={"reason": " "}
    )

    assert response.status_code == 422


def test_report_without_token_returns_401(
    anonymous_client: TestClient, session: Session, curator: User
) -> None:
    recommendation = make_recommendation(session, curator)

    response = anonymous_client.post(
        f"/recommendations/{recommendation.id}/reports", json={"reason": "x"}
    )

    assert response.status_code == 401


def test_three_reports_hide_from_feed(
    anonymous_client: TestClient, session: Session, curator: User
) -> None:
    recommendation = make_recommendation(session, curator)
    for index in range(3):
        reporter = make_user(session, email=f"reporter{index}@example.com")
        anonymous_client.post(
            f"/recommendations/{recommendation.id}/reports",
            json={"reason": "Too famous."},
            headers=auth_headers(reporter),
        )

    assert anonymous_client.get("/recommendations").json()["items"] == []
    detail = anonymous_client.get(f"/recommendations/{recommendation.id}").json()
    assert detail["hidden"] is True
