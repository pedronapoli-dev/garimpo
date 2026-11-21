from typing import Any

from fastapi.testclient import TestClient

from app.services.exceptions import DomainError
from main import STATUS_BY_ERROR, app
from tests.conftest import VALID_TEXT


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
    assert body["genres"] == ["mpb", "jazz"]
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
    }
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


def test_openapi_uses_camel_case_ids_and_error_out() -> None:
    operation = app.openapi()["paths"]["/recommendations"]["post"]

    assert operation["operationId"] == "createRecommendation"
    for status_code in ("409", "422"):
        schema = operation["responses"][status_code]["content"]["application/json"]
        assert schema["schema"] == {"$ref": "#/components/schemas/ErrorOut"}
