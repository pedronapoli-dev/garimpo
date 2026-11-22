import os
from collections.abc import Iterator

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.engine.interfaces import DBAPIConnection
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import ConnectionPoolEntry, Pool


def database_url() -> str:
    return os.environ.get("GARIMPO_DATABASE_URL", "sqlite:///./garimpo.db")


DATABASE_URL = database_url()


def create_db_engine(url: str, *, poolclass: type[Pool] | None = None) -> Engine:
    engine = create_engine(
        url,
        connect_args={"check_same_thread": False},
        poolclass=poolclass,
    )

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(
        dbapi_connection: DBAPIConnection, connection_record: ConnectionPoolEntry
    ) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


engine = create_db_engine(DATABASE_URL)

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def get_session() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session
