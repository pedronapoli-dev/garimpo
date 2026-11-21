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
