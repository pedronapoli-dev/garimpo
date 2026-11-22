import json
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app import settings
from app.dependencies import get_assistant
from app.llm.fake import FakeAssistant
from main import app

DRAFT = {
    "type": "album",
    "artist": "Arthur Verocai",
    "title": "Arthur Verocai",
    "text": "Great album.",
}


@pytest.fixture
def fake_assistant(anonymous_client: TestClient) -> None:
    app.dependency_overrides[get_assistant] = lambda: FakeAssistant()


@pytest.fixture
def no_assistant(anonymous_client: TestClient) -> None:
    app.dependency_overrides[get_assistant] = lambda: None


def events(body: str) -> list[dict[str, Any]]:
    return [
        json.loads(line.removeprefix("data: "))
        for line in body.splitlines()
        if line.startswith("data: ")
    ]


@pytest.mark.usefixtures("no_assistant")
def test_status_is_disabled_without_an_assistant(anonymous_client: TestClient) -> None:
    response = anonymous_client.get("/assist/status")

    assert response.status_code == 200
    assert response.json() == {"enabled": False}


@pytest.mark.usefixtures("fake_assistant")
def test_status_is_enabled_with_an_assistant(anonymous_client: TestClient) -> None:
    assert anonymous_client.get("/assist/status").json() == {"enabled": True}


@pytest.mark.usefixtures("fake_assistant")
def test_review_streams_events_ending_in_done(client: TestClient) -> None:
    response = client.post("/assist/review", json=DRAFT)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    received = events(response.text)
    assert received[0]["type"] == "feedback_delta"
    assert received[-1]["type"] == "done"
    assert received[-1]["result"]["explains_why"] is False


@pytest.mark.usefixtures("fake_assistant")
def test_review_requires_login(anonymous_client: TestClient) -> None:
    response = anonymous_client.post("/assist/review", json=DRAFT)

    assert response.status_code == 401
    assert response.json()["code"] == "not_authenticated"


@pytest.mark.usefixtures("no_assistant")
def test_review_without_an_assistant_returns_503(client: TestClient) -> None:
    response = client.post("/assist/review", json=DRAFT)

    assert response.status_code == 503
    assert response.json()["code"] == "assist_disabled"


@pytest.mark.usefixtures("fake_assistant")
def test_review_invalid_draft_returns_422(client: TestClient) -> None:
    response = client.post("/assist/review", json=DRAFT | {"text": ""})

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


def test_openapi_documents_the_stream_events(anonymous_client: TestClient) -> None:
    spec = anonymous_client.get("/openapi.json").json()

    review = spec["paths"]["/assist/review"]["post"]
    assert review["operationId"] == "reviewDraft"
    assert "text/event-stream" in review["responses"]["200"]["content"]
    # Errors happen before the stream starts, so they are plain JSON.
    for status_code in ("401", "422", "503"):
        assert list(review["responses"][status_code]["content"]) == ["application/json"]
    assert {"FeedbackDelta", "AssistDone", "AssistFailed"} <= set(
        spec["components"]["schemas"]
    )


def test_get_assistant_without_a_key_is_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "ASSIST_FAKE", False)
    monkeypatch.setattr(settings, "ASSIST_HAS_API_KEY", False)

    assert get_assistant() is None


def test_get_assistant_serves_the_fake_when_asked(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "ASSIST_FAKE", True)

    assert isinstance(get_assistant(), FakeAssistant)
