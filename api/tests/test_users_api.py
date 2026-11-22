from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import User
from tests.conftest import make_recommendation, make_user


def test_get_user_returns_public_profile(
    anonymous_client: TestClient, session: Session, curator: User
) -> None:
    make_recommendation(session, curator)

    response = anonymous_client.get(f"/users/{curator.id}")

    assert response.status_code == 200
    body = response.json()
    assert body["display_name"] == "Pedro"
    assert body["recommendation_count"] == 1
    assert "email" not in body


def test_get_missing_user_returns_404(anonymous_client: TestClient) -> None:
    response = anonymous_client.get("/users/999")

    assert response.status_code == 404
    assert response.json()["code"] == "user_not_found"


def test_profile_recommendations_come_from_feed_filter(
    anonymous_client: TestClient, session: Session, curator: User
) -> None:
    other = make_user(session, email="other@example.com")
    make_recommendation(session, curator)
    theirs = make_recommendation(session, other, title="Theirs", title_key="theirs")

    body = anonymous_client.get(
        "/recommendations", params={"author_id": other.id}
    ).json()

    assert [item["id"] for item in body["items"]] == [theirs.id]
