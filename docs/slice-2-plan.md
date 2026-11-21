# Slice 2 plan: models, migrations and recommendation CRUD

Status: approved on 2026-11-18; implemented on 2026-11-21 (see `docs/slice-2-blueprint.md`). The decisions below were refined into the "Data model" section of `docs/requirements.md`, which takes precedence (rule 7 also matches on `type`, and the unique index lives in the database). Read it together with `docs/requirements.md`, `CLAUDE.md`, `api/CLAUDE.md` and `.claude/rules/python.md`.

## Where things stand

- Slice 1 is done: `GET /health` works and has one test. Tests, lint and format all pass.
- The repository is public on GitHub as `origin` (`pedronapoli-dev/garimpo`), on `main`, and has an MIT license.
- Not yet committed: the `ruff format` fix in `api/main.py` and `api/tests/test_health.py`, which only adds the missing final newline. Suggested commit message: `Apply ruff formatting`.
- Working mode: Pedro writes the code. Claude explains each concept by comparing it with Swift, provides skeletons with `TODO` markers and reviews the result. Claude writes configuration and generated migrations directly.

## Scope

In scope:

- The SQLAlchemy and Alembic setup.
- Models for `users`, `recommendations`, `tags` and `recommendation_tags`.
- These endpoints, all without auth:
  - `POST /recommendations`
  - `GET /recommendations`
  - `GET /recommendations/{id}`
  - `PATCH /recommendations/{id}`
  - `DELETE /recommendations/{id}`
  - `GET /tags`
- Business rules 2 and 7.

Out of scope, with the slice that covers each:

- Rule 5 (only the author can edit or delete) needs auth: slice 4.
- Sorting the feed by most voted needs votes: slice 5.
- Rule 6 (3 reports hide a recommendation) and the reports table: slice 6.
- The `invites`, `votes`, `saves` and `reports` tables: their own slices.

## Steps

Each step ends with tests, lint and format passing, and gets one commit.

1. **Database setup.** Add `sqlalchemy` and `alembic` with `uv add`. Write `app/db.py` with the engine, a session factory and a `get_session` dependency. In `tests/conftest.py`, add a fixture that gives each test a fresh in-memory SQLite database and overrides the dependency.
   - Concepts: `Depends`, a `yield` function used as a dependency (cleanup after the request, similar to `defer`), pytest fixtures, and `app.dependency_overrides`.
2. **Models and the first migration.** Write `app/models.py`. The recommendation type is a `StrEnum` with the values `artist`, `album` and `track`. `recommendation_tags` is the join table between recommendations and tags. Claude generates the Alembic migration, which also seeds the dev curator (see decision 1).
   - Concepts: `DeclarativeBase`, `Mapped[...]` and `mapped_column`, `relationship`, many-to-many tables, Alembic autogenerate, and `alembic upgrade head`.
3. **Schemas and rule 2.** In `app/schemas.py`, write `RecommendationCreate`, `RecommendationUpdate` and `RecommendationOut`. Validation:
   - 1 to 5 genres;
   - text of 80 to 1000 characters;
   - a title is required for `album` and `track` and must be empty for `artist`.

   Tests run against the schemas, without HTTP.
   - Concepts: `Field` constraints, `model_validator`, and how Pydantic validation compares with `Codable` plus a throwing `init(from:)`.
4. **Create, plus rule 7.** Add `pytest-cov` and write `app/services/recommendations.py` test first; there is no repository layer (see "Architecture" in `docs/requirements.md`). The service raises a `DuplicateRecommendation` domain exception that carries the existing id. Then write `app/routers/recommendations.py` with `POST /recommendations`, and register an exception handler in `main.py` that turns the exception into a **409** `ErrorOut` response with `code` and `existing_id`. Rule tests run at the service level; the router is tested with `TestClient` for the status code and the response shape.
   - Concepts: custom exception classes compared with Swift typed `throws`, `app.add_exception_handler`, `responses=` in the route decorator, `include_router` and `pytest --cov`.
5. **Read endpoints.**
   - `GET /recommendations/{id}` returns 404 when the recommendation is missing.
   - `GET /recommendations` uses cursor pagination, filters with `?genre=` and sorts newest first.
   - `GET /tags` lists all tags.

   The feed must respond in under 300 ms locally.
   - Concepts: `select()` in SQLAlchemy 2.0, an opaque cursor built from `created_at` and `id`, and query parameters with defaults.
6. **Edit and delete.** `PATCH /recommendations/{id}` makes a partial update, and rule 7 is checked again when the artist or title changes. `DELETE /recommendations/{id}` returns 204.
   - Concepts: `model_dump(exclude_unset=True)` for partial updates.

## Decisions waiting for approval

These are the proposed defaults. Confirm them or change them before step 2.

1. **The author before auth exists.** Create the `users` table now. The first migration seeds one local "dev curator" user, and every recommendation in slice 2 uses that user as its author. Slice 4 replaces it with the logged-in user without changing the schema. The rejected alternative is a nullable `author_id`, which would need another migration later.
2. **Matching duplicates for rule 7.** Artist and title are compared case-insensitively, with leading and trailing whitespace removed and repeated spaces collapsed into one. Genre tags are stored in lowercase and trimmed.

## How to start the new session

Run `/slice 2` and point it at this file. The session should confirm the two decisions, then start step 1 with the Swift comparison and the skeleton.
