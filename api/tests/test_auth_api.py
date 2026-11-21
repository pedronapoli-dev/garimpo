from typing import Any

from fastapi.testclient import TestClient

from tests.conftest import auth_headers

PASSWORD = "correct horse battery"


def signup_payload(code: str, **overrides: Any) -> dict[str, Any]:
    fields = {
        "invite_code": code,
        "email": "new@example.com",
        "display_name": "New Curator",
        "password": PASSWORD,
    }
    return fields | overrides


def new_invite(client: TestClient) -> str:
    return client.post("/invites").json()["code"]


def test_create_invite_returns_201_with_code(client: TestClient) -> None:
    response = client.post("/invites")

    assert response.status_code == 201
    assert set(response.json()) == {"code"}


def test_create_invite_without_token_returns_401(anonymous_client: TestClient) -> None:
    assert anonymous_client.post("/invites").status_code == 401


def test_signup_returns_201_with_token_and_user(client: TestClient) -> None:
    response = client.post("/auth/signup", json=signup_payload(new_invite(client)))

    assert response.status_code == 201
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == "new@example.com"
    me = {"Authorization": f"Bearer {body['access_token']}"}
    assert client.post("/invites", headers=me).status_code == 201


def test_signup_with_used_invite_returns_422(client: TestClient) -> None:
    code = new_invite(client)
    client.post("/auth/signup", json=signup_payload(code))

    response = client.post(
        "/auth/signup", json=signup_payload(code, email="second@example.com")
    )

    assert response.status_code == 422
    assert response.json()["code"] == "invalid_invite"


def test_signup_with_taken_email_returns_409(client: TestClient) -> None:
    client.post("/auth/signup", json=signup_payload(new_invite(client)))

    response = client.post("/auth/signup", json=signup_payload(new_invite(client)))

    assert response.status_code == 409
    assert response.json()["code"] == "email_taken"


def test_signup_with_short_password_returns_422(client: TestClient) -> None:
    response = client.post(
        "/auth/signup", json=signup_payload(new_invite(client), password="short")
    )

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


def test_login_returns_token_that_authenticates(client: TestClient) -> None:
    client.post("/auth/signup", json=signup_payload(new_invite(client)))

    response = client.post(
        "/auth/login", json={"email": "NEW@example.com", "password": PASSWORD}
    )

    assert response.status_code == 200
    token = response.json()["access_token"]
    me = {"Authorization": f"Bearer {token}"}
    assert client.post("/invites", headers=me).status_code == 201


def test_login_with_wrong_password_returns_401(client: TestClient) -> None:
    client.post("/auth/signup", json=signup_payload(new_invite(client)))

    response = client.post(
        "/auth/login", json={"email": "new@example.com", "password": "wrong password"}
    )

    assert response.status_code == 401
    assert response.json() == {
        "code": "invalid_credentials",
        "message": "Wrong email or password.",
    }


def test_auth_headers_helper_authenticates(
    anonymous_client: TestClient, curator: Any
) -> None:
    response = anonymous_client.post("/invites", headers=auth_headers(curator))

    assert response.status_code == 201
