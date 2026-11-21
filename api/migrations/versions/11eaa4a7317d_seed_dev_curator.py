"""Seed dev curator

Revision ID: 11eaa4a7317d
Revises: 1ee2533c2a54
Create Date: 2026-11-21 16:18:23.236216

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "11eaa4a7317d"
down_revision: str | Sequence[str] | None = "1ee2533c2a54"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# Frozen copy of the columns this migration writes. Migrations never import
# app.models, because the models keep changing after the migration is written.
users = sa.table(
    "users",
    sa.column("email", sa.String),
    sa.column("display_name", sa.String),
    sa.column("password_hash", sa.String),
)

DEV_CURATOR_EMAIL = "curator@garimpo.local"


def upgrade() -> None:
    """Seed the dev curator, the author of every recommendation until slice 4."""
    # "!" is not a valid Argon2 hash, so no password can ever log in as this user.
    op.bulk_insert(
        users,
        [
            {
                "email": DEV_CURATOR_EMAIL,
                "display_name": "Pedro",
                "password_hash": "!",
            }
        ],
    )


def downgrade() -> None:
    """Remove the dev curator."""
    op.execute(users.delete().where(users.c.email == DEV_CURATOR_EMAIL))
