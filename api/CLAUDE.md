# API

FastAPI + Pydantic, SQLAlchemy 2.0 + Alembic (starting in slice 2), SQLite. Managed with uv as a non-packaged application (`[tool.uv] package = false`).

## Commands

Always run from inside `api/` and always through `uv run`. Never use `pip install` or activate `.venv` manually.

- Tests: `uv run pytest`
- Lint: `uv run ruff check .`
- Format: `uv run ruff format .`
- Local server: `uv run fastapi dev main.py` (docs at http://127.0.0.1:8000/docs)
- New dependency: `uv add <package>`; dev-only: `uv add --dev <package>`

A step is done only when tests, lint and format all pass.

## Layout

Today:

```
api/
  main.py              creates the FastAPI app and registers routers
  tests/
```

From slice 2 on:

```
api/
  main.py
  app/
    db.py              SQLAlchemy engine and session
    models.py          tables (SQLAlchemy)
    schemas.py         API input and output (Pydantic)
    routers/           one file per resource; HTTP only, no business rules
    services/          business rules; unaware of HTTP
    repositories/      database access; unaware of business rules
  migrations/          Alembic
  tests/
```

- Dependencies flow one way: routers → services → repositories.
- Business rule violations are domain exceptions raised in services; routers translate them into `HTTPException`.
- Do not use the `src/` layout, and do not add `__init__.py` outside `app/` and its subfolders.
