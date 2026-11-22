import os
from datetime import timedelta

# Set GARIMPO_JWT_SECRET outside local development. The default only exists so
# the project runs after a fresh clone; anyone can read it in this public repo.
DEFAULT_JWT_SECRET = "dev-only-secret-do-not-use-in-production-0123456789"
JWT_SECRET = os.environ.get("GARIMPO_JWT_SECRET", DEFAULT_JWT_SECRET)
# The Docker image sets this to "production".
ENVIRONMENT = os.environ.get("GARIMPO_ENV", "development")
# RFC 7518: an HS256 key should be at least as long as the hash, 32 bytes.
MIN_JWT_SECRET_BYTES = 32
JWT_ALGORITHM = "HS256"
# Mobile app without refresh tokens: a long-lived token, cleared on logout.
ACCESS_TOKEN_TTL = timedelta(days=30)

# Curator assist (FR12, slice 7). Optional: without a key the app works as the
# MVP and hides the assist. GARIMPO_ASSIST_FAKE=1 serves the deterministic fake,
# to work on the app without a key or any cost.
# "anthropic" uses ANTHROPIC_API_KEY; "bedrock" uses the server's AWS credentials.
ASSIST_PROVIDER = os.environ.get("GARIMPO_ASSIST_PROVIDER", "anthropic")


def default_assist_model(provider: str) -> str:
    prefix = "anthropic." if provider == "bedrock" else ""
    return f"{prefix}claude-sonnet-5-5"


ASSIST_MODEL = os.environ.get(
    "GARIMPO_ASSIST_MODEL", default_assist_model(ASSIST_PROVIDER)
)
ASSIST_HAS_API_KEY = bool(os.environ.get("ANTHROPIC_API_KEY"))
ASSIST_FAKE = os.environ.get("GARIMPO_ASSIST_FAKE") == "1"


def check_production(environment: str, secret: str) -> None:
    """Stops a deployed server from signing tokens with a public or weak key."""
    if environment != "production":
        return
    if secret == DEFAULT_JWT_SECRET or len(secret.encode()) < MIN_JWT_SECRET_BYTES:
        raise RuntimeError(
            "Set GARIMPO_JWT_SECRET to a private value of at least "
            f"{MIN_JWT_SECRET_BYTES} bytes."
        )
