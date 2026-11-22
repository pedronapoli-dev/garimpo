# API

FastAPI + Pydantic, SQLAlchemy 2.0 + Alembic (starting in slice 2), SQLite. Managed with uv as a non-packaged application (`[tool.uv] package = false`).

## Commands

Always run from inside `api/` and always through `uv run`. Never use `pip install` or activate `.venv` manually.

- Tests: `uv run pytest`
- Service coverage (from slice 2 step 4 on): `uv run pytest --cov`; fails below 100% on `app/services`
- Lint: `uv run ruff check .`
- Format: `uv run ruff format .`
- Typecheck: `uv run pyright` (the same checker and mode as Pylance in the editor)
- Local server: `uv run fastapi dev main.py` (docs at http://127.0.0.1:8000/docs)
- New dependency: `uv add <package>`; dev-only: `uv add --dev <package>`
- First invite (sign-up is invite-only): `uv run python -m app.cli create-invite`
- JWT secret: set `GARIMPO_JWT_SECRET` anywhere other than local development (see `app/settings.py`)

A step is done only when tests, typecheck, lint and format all pass.

## Layout

```
api/
  main.py              creates the app, registers routers and error handlers
  app/
    db.py              SQLAlchemy engine and session
    models.py          tables (SQLAlchemy)
    schemas.py         API input and output (Pydantic)
    dependencies.py    SessionDep and CurrentUser for routes
    settings.py        configuration read from the environment
    cli.py             management commands
    normalization.py   normalize_key for rule 7 keys and tag names
    routers/           one file per resource; HTTP only, no business rules
    services/          business rules; unaware of HTTP
  migrations/          Alembic
  tests/
```

- Migrations: `uv run alembic upgrade head` creates `garimpo.db`; after changing `models.py`, `uv run alembic revision --autogenerate -m "..."` and review the file.

- Dependencies flow one way: routers → services → models.
- No repository layer: services are module-level functions that receive a `Session`. Move a query to its own module only when two services share it.
- Business rule violations are domain exceptions raised in services. `main.py` maps them to status codes and the `ErrorOut` schema with `app.add_exception_handler`; routers do not catch them.
- `app/llm/` (slice 7 only) is the one place for a `Protocol`: a Claude client and a deterministic fake.
- Architecture and testing strategy: `docs/requirements.md`.
- Do not use the `src/` layout, and do not add `__init__.py` outside `app/` and its subfolders.
