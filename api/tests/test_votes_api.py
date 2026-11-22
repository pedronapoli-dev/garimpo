from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import User
from tests.conftest import auth_headers, make_recommendation, make_user


def test_vote_returns_200_with_state(client: TestClient, session: Session) -> None:
    other = make_user(session, email="other@example.com")
    recommendation = make_recommendation(session, other)

    response = client.put(f"/recommendations/{recommendation.id}/vote")

    assert response.status_code == 200
    assert response.json() == {"vote_count": 1, "voted_by_me": True}


def test_vote_on_own_returns_403(
    client: TestClient, session: Session, curator: User
) -> None:
    recommendation = make_recommendation(session, curator)

    response = client.put(f"/recommendations/{recommendation.id}/vote")

    assert response.status_code == 403
    assert response.json()["code"] == "own_recommendation"


def test_vote_without_token_returns_401(
    anonymous_client: TestClient, session: Session, curator: User
) -> None:
    recommendation = make_recommendation(session, curator)

    assert (
        anonymous_client.put(f"/recommendations/{recommendation.id}/vote").status_code
        == 401
    )


def test_unvote_returns_200_with_state(client: TestClient, session: Session) -> None:
    recommendation = make_recommendation(
        session, make_user(session, email="o@example.com")
    )
    client.put(f"/recommendations/{recommendation.id}/vote")

    response = client.delete(f"/recommendations/{recommendation.id}/vote")

    assert response.json() == {"vote_count": 0, "voted_by_me": False}


def test_vote_on_missing_returns_404(client: TestClient) -> None:
    assert client.put("/recommendations/999/vote").status_code == 404


def test_save_then_list_my_saves(
    client: TestClient, session: Session, curator: User
) -> None:
    recommendation = make_recommendation(session, curator)

    assert client.put(f"/recommendations/{recommendation.id}/save").json() == {
        "saved_by_me": True
    }
    body = client.get("/me/saves").json()

    assert [item["id"] for item in body["items"]] == [recommendation.id]
    assert body["items"][0]["saved_by_me"] is True

    assert client.delete(f"/recommendations/{recommendation.id}/save").json() == {
        "saved_by_me": False
    }
    assert client.get("/me/saves").json()["items"] == []


def test_my_saves_without_token_returns_401(anonymous_client: TestClient) -> None:
    assert anonymous_client.get("/me/saves").status_code == 401


def test_feed_shows_viewer_state_only_with_token(
    anonymous_client: TestClient, session: Session, curator: User
) -> None:
    recommendation = make_recommendation(session, curator)
    voter = make_user(session, email="voter@example.com")
    anonymous_client.put(
        f"/recommendations/{recommendation.id}/vote", headers=auth_headers(voter)
    )

    anonymous = anonymous_client.get("/recommendations").json()["items"][0]
    as_voter = anonymous_client.get(
        "/recommendations", headers=auth_headers(voter)
    ).json()["items"][0]

    assert (anonymous["vote_count"], anonymous["voted_by_me"]) == (1, False)
    assert (as_voter["vote_count"], as_voter["voted_by_me"]) == (1, True)


def test_feed_with_expired_token_returns_401(anonymous_client: TestClient) -> None:
    response = anonymous_client.get(
        "/recommendations", headers={"Authorization": "Bearer expired"}
    )

    assert response.status_code == 401


def test_feed_sorted_by_top(
    client: TestClient, session: Session, curator: User
) -> None:
    older = make_recommendation(session, curator, title="Older", title_key="older")
    make_recommendation(session, curator, title="Newer", title_key="newer")
    make_user_vote = make_user(session, email="voter@example.com")
    client.put(
        f"/recommendations/{older.id}/vote", headers=auth_headers(make_user_vote)
    )

    body = client.get("/recommendations", params={"sort": "top"}).json()

    assert [item["title"] for item in body["items"]] == ["Older", "Newer"]


def test_feed_unknown_sort_returns_422(client: TestClient) -> None:
    assert client.get("/recommendations", params={"sort": "random"}).status_code == 422
