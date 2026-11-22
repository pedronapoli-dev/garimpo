"""Settings that protect a deployed server."""

import pytest

from app import settings
from app.db import database_url
from app.llm.claude import ClaudeAssistant, create_client, usage_from

STRONG_SECRET = "s" * 32


def test_production_refuses_the_public_default_secret() -> None:
    with pytest.raises(RuntimeError, match="GARIMPO_JWT_SECRET"):
        settings.check_production("production", settings.DEFAULT_JWT_SECRET)


def test_production_refuses_a_short_secret() -> None:
    with pytest.raises(RuntimeError, match="GARIMPO_JWT_SECRET"):
        settings.check_production("production", "s" * 31)


def test_production_accepts_a_strong_secret() -> None:
    settings.check_production("production", STRONG_SECRET)


def test_development_allows_the_default_secret() -> None:
    settings.check_production("development", settings.DEFAULT_JWT_SECRET)


def test_database_url_comes_from_the_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GARIMPO_DATABASE_URL", "sqlite:////data/garimpo.db")

    assert database_url() == "sqlite:////data/garimpo.db"


def test_database_url_defaults_to_the_local_file(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("GARIMPO_DATABASE_URL", raising=False)

    assert database_url() == "sqlite:///./garimpo.db"


@pytest.mark.parametrize(
    ("provider", "expected"),
    [
        ("anthropic", "claude-sonnet-5-5"),
        ("bedrock", "anthropic.claude-sonnet-5-5"),
    ],
)
def test_default_model_follows_the_provider(provider: str, expected: str) -> None:
    assert settings.default_assist_model(provider) == expected


def test_bedrock_model_ids_use_the_same_prices() -> None:
    usage = usage_from("anthropic.claude-sonnet-5-5", 1_000_000, 1_000_000, 1)

    assert usage.cost_usd == pytest.approx(12.0)
    ClaudeAssistant(model="anthropic.claude-sonnet-5-5", client=object())


def test_create_client_builds_the_bedrock_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test")

    client = create_client("bedrock")

    assert "bedrock-mantle.us-east-1" in str(client.base_url)
    assert client.max_retries == 1


def test_create_client_rejects_an_unknown_provider() -> None:
    with pytest.raises(ValueError, match="nope"):
        create_client("nope")
