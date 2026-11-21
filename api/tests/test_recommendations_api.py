import time
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Tag, User
from app.services.exceptions import DomainError
from main import STATUS_BY_ERROR, app
from tests.conftest import (
    VALID_TEXT,
    auth_headers,
    make_recommendation,
    make_user,
    make_vote,
)


def payload(**overrides: Any) -> dict[str, Any]:
    fields: dict[str, Any] = {
        "type": "album",
        "artist": "Arthur Verocai",
        "title": "Arthur Verocai",
        "genres": ["MPB", "jazz"],
        "text": VALID_TEXT,
    }
    return fields | overrides


# POST /recommendations


def test_create_returns_201_with_recommendation(client: TestClient) -> None:
    response = client.post("/recommendations", json=payload())

    assert response.status_code == 201
    body = response.json()
    assert body["id"] > 0
    assert body["genres"] == ["jazz", "mpb"]
    assert body["author"] == {"id": 1, "display_name": "Pedro"}
    assert set(body) == {
        "id",
        "type",
        "artist",
        "title",
        "genres",
        "text",
        "author",
        "created_at",
        "updated_at",
        "vote_count",
        "voted_by_me",
        "saved_by_me",
    }
    assert (body["vote_count"], body["voted_by_me"], body["saved_by_me"]) == (
        0,
        False,
        False,
    )
    assert body["created_at"].endswith("Z") or body["created_at"].endswith("+00:00")


def test_create_duplicate_returns_409_with_existing_id(client: TestClient) -> None:
    first = client.post("/recommendations", json=payload()).json()

    response = client.post("/recommendations", json=payload(artist="arthur verocai"))

    assert response.status_code == 409
    assert response.json() == {
        "code": "duplicate_recommendation",
        "message": "This artist and title were already recommended.",
        "existing_id": first["id"],
    }


def test_create_invalid_payload_returns_422_error_out(client: TestClient) -> None:
    response = client.post("/recommendations", json=payload(genres=[]))

    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "validation_error"
    assert "genres" in body["message"]
    assert set(body) == {"code", "message"}


# Contract


def test_every_domain_error_has_a_status_code() -> None:
    assert set(DomainError.__subclasses__()) == set(STATUS_BY_ERROR)


def test_openapi_operation_ids_are_camel_case() -> None:
    operation_ids = {
        operation["operationId"]
        for path in app.openapi()["paths"].values()
        for operation in path.values()
    }

    assert operation_ids == {
        "health",
        "signup",
        "login",
        "createInvite",
        "createRecommendation",
        "listRecommendations",
        "getRecommendation",
        "updateRecommendation",
        "deleteRecommendation",
        "voteRecommendation",
        "unvoteRecommendation",
        "saveRecommendation",
        "unsaveRecommendation",
        "listTags",
        "getUser",
        "listMySaves",
    }


def test_openapi_uses_camel_case_ids_and_error_out() -> None:
    operation = app.openapi()["paths"]["/recommendations"]["post"]

    assert operation["operationId"] == "createRecommendation"
    for status_code in ("409", "422"):
        schema = operation["responses"][status_code]["content"]["application/json"]
        assert schema["schema"] == {"$ref": "#/components/schemas/ErrorOut"}


# GET /recommendations/{id}


def test_get_returns_200_with_recommendation(client: TestClient) -> None:
    created = client.post("/recommendations", json=payload()).json()

    response = client.get(f"/recommendations/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created


def test_get_missing_returns_404_error_out(client: TestClient) -> None:
    response = client.get("/recommendations/999")

    assert response.status_code == 404
    assert response.json() == {
        "code": "recommendation_not_found",
        "message": "Recommendation 999 does not exist.",
    }


# GET /recommendations


def test_list_returns_page_with_next_cursor(client: TestClient) -> None:
    for index in range(3):
        client.post("/recommendations", json=payload(title=f"Album {index}"))

    first = client.get("/recommendations", params={"limit": 2}).json()
    second = client.get(
        "/recommendations", params={"limit": 2, "cursor": first["next_cursor"]}
    ).json()

    assert [item["title"] for item in first["items"]] == ["Album 2", "Album 1"]
    assert [item["title"] for item in second["items"]] == ["Album 0"]
    assert second["next_cursor"] is None


def test_list_filters_by_genre(client: TestClient) -> None:
    client.post("/recommendations", json=payload(title="A", genres=["jazz"]))
    client.post("/recommendations", json=payload(title="B", genres=["soul"]))

    body = client.get("/recommendations", params={"genre": "Soul"}).json()

    assert [item["title"] for item in body["items"]] == ["B"]


def test_list_invalid_cursor_returns_422_error_out(client: TestClient) -> None:
    response = client.get("/recommendations", params={"cursor": "nope"})

    assert response.status_code == 422
    assert response.json()["code"] == "invalid_cursor"


def test_list_limit_out_of_range_returns_422(client: TestClient) -> None:
    response = client.get("/recommendations", params={"limit": 101})

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


@pytest.mark.parametrize("sort", ["newest", "top"])
def test_list_with_many_rows_responds_under_300_ms(
    client: TestClient, session: Session, curator: User, sort: str
) -> None:
    jazz = Tag(name="jazz")
    voters = [
        make_user(session, email=f"voter{index}@example.com") for index in range(5)
    ]
    for index in range(2000):
        recommendation = make_recommendation(
            session,
            curator,
            title=f"Album {index}",
            title_key=f"album {index}",
            tags=[jazz],
        )
        for voter in voters[: index % 6]:
            make_vote(session, voter, recommendation)
    session.commit()

    started = time.perf_counter()
    response = client.get(
        "/recommendations", params={"genre": "jazz", "limit": 50, "sort": sort}
    )
    elapsed = time.perf_counter() - started

    assert response.status_code == 200
    assert len(response.json()["items"]) == 50
    assert elapsed < 0.3


# PATCH /recommendations/{id}


def test_update_returns_200_with_changes(client: TestClient) -> None:
    created = client.post("/recommendations", json=payload()).json()

    response = client.patch(
        f"/recommendations/{created['id']}", json={"genres": ["Soul"]}
    )

    assert response.status_code == 200
    assert response.json()["genres"] == ["soul"]
    assert response.json()["text"] == created["text"]


def test_update_duplicate_returns_409_with_existing_id(client: TestClient) -> None:
    first = client.post("/recommendations", json=payload()).json()
    second = client.post("/recommendations", json=payload(title="Saudade")).json()

    response = client.patch(
        f"/recommendations/{second['id']}", json={"title": first["title"]}
    )

    assert response.status_code == 409
    assert response.json()["existing_id"] == first["id"]


def test_update_breaking_title_rule_returns_422_error_out(client: TestClient) -> None:
    created = client.post("/recommendations", json=payload()).json()

    response = client.patch(
        f"/recommendations/{created['id']}", json={"type": "artist"}
    )

    assert response.status_code == 422
    assert response.json()["code"] == "invalid_recommendation"


def test_update_null_artist_returns_422(client: TestClient) -> None:
    created = client.post("/recommendations", json=payload()).json()

    response = client.patch(f"/recommendations/{created['id']}", json={"artist": None})

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


def test_update_missing_returns_404(client: TestClient) -> None:
    response = client.patch("/recommendations/999", json={"genres": ["soul"]})

    assert response.status_code == 404


# DELETE /recommendations/{id}


def test_delete_returns_204_and_removes_it(client: TestClient) -> None:
    created = client.post("/recommendations", json=payload()).json()

    response = client.delete(f"/recommendations/{created['id']}")

    assert response.status_code == 204
    assert response.content == b""
    assert client.get(f"/recommendations/{created['id']}").status_code == 404


def test_delete_missing_returns_404(client: TestClient) -> None:
    assert client.delete("/recommendations/999").status_code == 404


# Auth and rule 5


def test_create_without_token_returns_401_error_out(
    anonymous_client: TestClient,
) -> None:
    response = anonymous_client.post("/recommendations", json=payload())

    assert response.status_code == 401
    assert response.json() == {
        "code": "not_authenticated",
        "message": "Log in to do this.",
    }


def test_create_with_invalid_token_returns_401(anonymous_client: TestClient) -> None:
    response = anonymous_client.post(
        "/recommendations",
        json=payload(),
        headers={"Authorization": "Bearer not-a-jwt"},
    )

    assert response.status_code == 401


def test_read_endpoints_need_no_token(anonymous_client: TestClient) -> None:
    assert anonymous_client.get("/recommendations").status_code == 200
    assert anonymous_client.get("/tags").status_code == 200


def test_create_sets_logged_in_user_as_author(
    anonymous_client: TestClient, session: Session
) -> None:
    other = make_user(session, email="other@example.com", display_name="Other")

    response = anonymous_client.post(
        "/recommendations", json=payload(), headers=auth_headers(other)
    )

    assert response.json()["author"] == {"id": other.id, "display_name": "Other"}


def test_update_by_other_user_returns_403(client: TestClient, session: Session) -> None:
    created = client.post("/recommendations", json=payload()).json()
    other = make_user(session, email="other@example.com")

    response = client.patch(
        f"/recommendations/{created['id']}",
        json={"genres": ["soul"]},
        headers=auth_headers(other),
    )

    assert response.status_code == 403
    assert response.json()["code"] == "not_author"


def test_delete_by_other_user_returns_403(client: TestClient, session: Session) -> None:
    created = client.post("/recommendations", json=payload()).json()
    other = make_user(session, email="other@example.com")

    response = client.delete(
        f"/recommendations/{created['id']}", headers=auth_headers(other)
    )

    assert response.status_code == 403


# GET /tags


def test_list_tags_returns_200_with_tags(client: TestClient) -> None:
    client.post("/recommendations", json=payload(genres=["soul", "jazz"]))

    response = client.get("/tags")

    assert response.status_code == 200
    assert [tag["name"] for tag in response.json()] == ["jazz", "soul"]
