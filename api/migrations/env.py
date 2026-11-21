from alembic import context
from sqlalchemy import Connection

from app.db import DATABASE_URL, create_db_engine
from app.models import Base

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_with_connection(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    # Tests pass their own connection (see tests/test_migrations.py).
    connection = context.config.attributes.get("connection")
    if connection is not None:
        run_with_connection(connection)
        return

    engine = create_db_engine(DATABASE_URL)
    with engine.connect() as connection:
        run_with_connection(connection)
    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
