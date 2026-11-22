import os
from datetime import timedelta

# Set GARIMPO_JWT_SECRET outside local development. The default only exists so
# the project runs after a fresh clone; anyone can read it in this public repo.
JWT_SECRET = os.environ.get(
    "GARIMPO_JWT_SECRET", "dev-only-secret-do-not-use-in-production-0123456789"
)
JWT_ALGORITHM = "HS256"
# Mobile app without refresh tokens: a long-lived token, cleared on logout.
ACCESS_TOKEN_TTL = timedelta(days=30)

# Curator assist (FR12, slice 7). Optional: without a key the app works as the
# MVP and hides the assist. GARIMPO_ASSIST_FAKE=1 serves the deterministic fake,
# to work on the app without a key or any cost.
ASSIST_MODEL = os.environ.get("GARIMPO_ASSIST_MODEL", "claude-sonnet-5-5")
ASSIST_HAS_API_KEY = bool(os.environ.get("ANTHROPIC_API_KEY"))
ASSIST_FAKE = os.environ.get("GARIMPO_ASSIST_FAKE") == "1"
