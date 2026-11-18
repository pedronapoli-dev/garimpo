from sqlalchemy import text
from sqlalchemy.orm import Session


def test_session_executes_query_returns_one(session: Session) -> None:
    assert session.execute(text("SELECT 1")).scalar_one() == 1


def test_foreign_keys_enabled_returns_one(session: Session) -> None:
    assert session.execute(text("PRAGMA foreign_keys")).scalar_one() == 1
