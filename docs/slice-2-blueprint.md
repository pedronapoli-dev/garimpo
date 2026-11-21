# Slice 2 blueprint: what was built, step by step

Written on 2026-11-21, when slice 2 was finished. It records what each step of `docs/slice-2-plan.md` built, why, and which Python concepts it uses, compared with Swift. `docs/requirements.md` still takes precedence.

Everything is on the `slice-2` branch, one commit per step. Final state: 102 tests passing, 100% coverage on `app/services`, ruff lint and format clean.

```
9334c70  Document architecture, testing strategy and slice 7
0c9784d  Step 2  Add models and first migrations
3ecfba9  Step 3  Add recommendation schemas with rule 2 validation
0ed9835  Step 4  Add POST /recommendations with rule 7
503e20e  Step 5  Add feed, detail and tags endpoints
821bd37  Step 6  Add PATCH and DELETE /recommendations
```

Step 1 (database setup) was already committed as `93350b8`.

## How a request flows

```
HTTP request
  → FastAPI parses the body into a schema (schemas.py)   422 validation_error if it fails
  → router function (routers/)                           receives SessionDep and CurrentUser
  → service function (services/)                         applies the rules, raises DomainError
  → SQLAlchemy models (models.py) → SQLite
  ← the router converts the model into RecommendationOut
  ← main.py converts any DomainError into ErrorOut with its status code
```

Swift comparison: think of a Vapor app where routes are thin, the business logic lives in free functions that take a `Database`, and errors are `AbortError`s. The one difference is that the routes never `catch`. Errors bubble up to a single handler registered in `main.py`, the way `ErrorMiddleware` works in Vapor.

## Step 2: models and the first migrations

### Review of the step as it was

The models in `app/models.py` matched the approved data model. Three problems stopped the tests from running:

1. `tests/conftest.py` read `app.state.Base`. That attribute never existed, so every test that used `session` failed with `AttributeError`. The fix was to import `Base` from `app.models`.
2. Each test in `tests/test_models.py` still ended with `raise NotImplementedError`, left over from the skeleton.
3. Some tests passed for the wrong reason. `make_recommendation(User(...))` read `author.id` before the user was saved, so `author_id` was `None`. The duplicate test then failed on `NOT NULL author_id` and never reached the unique index. In Swift terms, the test asserted that "an error was thrown" without checking which one.

There was also no migration yet.

### What was built

- `tests/conftest.py`: the `make_user(session, **overrides)` and `make_recommendation(session, author, **overrides)` helpers. They add the object and `flush()` it, so the object has an id and constraint errors show up immediately, inside `pytest.raises`.
- `tests/test_models.py`: tests for each constraint. Each one now fails for the reason it names: the unique index on `(type, artist_key, title_key)`, the foreign key to `users`, the text length `CHECK`, unique email, `ON DELETE CASCADE` from recommendations to `recommendation_tags`, and `ON DELETE RESTRICT` from tags.
- `migrations/versions/1ee2533c2a54_...py`: generated with `alembic revision --autogenerate`.
- `migrations/versions/11eaa4a7317d_seed_dev_curator.py`: written by hand. It seeds `curator@garimpo.local` with the password hash `"!"`.
- `migrations/env.py`: also accepts a connection through `config.attributes["connection"]`, so tests can run migrations against an in-memory database.
- `tests/test_migrations.py`: `upgrade head` on an empty database, `alembic check` (it fails if `models.py` and the migrations drift apart), and `downgrade base`.
- `pyproject.toml`: `[tool.ruff.lint.isort] known-first-party`. The editor runs ruff from the repository root and was grouping `app` and `main` with third-party imports, which made `ruff check` fail.

### Concepts

- **`Mapped[str]` and `mapped_column`** are like a Core Data attribute or a GRDB `Column`, declared through the type annotation. `Mapped[str | None]` makes the column nullable, the same way `String?` would.
- **`relationship(back_populates=...)`** works like an inverse relationship in Core Data. `secondary=recommendation_tags` makes it many-to-many through the join table.
- **Seed migrations never import `app.models`.** They declare a frozen copy of the table with `sa.table(...)`. The models keep changing, and a migration has to run the same way forever. It is the same reason a Core Data mapping model refers to a fixed model version.
- **`flush()` and `commit()`.** `flush()` sends the SQL inside the current transaction, which gives you ids and constraint errors. `commit()` ends the transaction. `NSManagedObjectContext.save()` does both at once; SQLAlchemy separates them.

## Step 3: schemas and rule 2

### What was built

- `app/normalization.py`: `normalize_key()` lowercases (`casefold`), trims and collapses repeated spaces. The rule 7 keys and tag names both use it.
- `app/schemas.py`:
  - Reusable field types built with `Annotated`: `Artist`, `Title`, `Text` (stripped, 80 to 1000 characters), `Genre` (normalized) and `Genres` (1 to 5, deduplicated after normalizing).
  - `check_title_for_type()`: rule 2's title rule as a plain function, so the update service can reuse it.
  - `RecommendationCreate`: field rules plus a `model_validator(mode="after")` for the title.
  - `RecommendationUpdate`: every field is optional. A validator rejects an explicit `null` for every field except `title`, so `{"artist": null}` fails while leaving `artist` out does not.
  - `RecommendationOut`: reads `tags` from the ORM and exposes them as `genres`. Timestamps come back in UTC.
  - `RecommendationPage`, `TagOut` and `ErrorOut`.
- `tests/test_schemas.py`: 32 tests with no HTTP and no database.

### Concepts

- **`Annotated[str, StringConstraints(...)]`** is a type that carries its validation with it. Swift has no direct equivalent. The closest is a property wrapper such as `@Clamped`, but here the rule belongs to the type, so `Artist` can be reused in both `Create` and `Update`.
- **`model_validator(mode="after")`** is like checking invariants at the end of a throwing `init(from decoder:)`, after every field has been decoded.
- **`model_dump(exclude_unset=True)`** returns only the fields the client actually sent. That is how `PATCH` tells "not sent" apart from "sent as null". Swift's `Codable` cannot make that distinction without a custom `decodeIfPresent` wrapper.
- **The text is stripped before its length is checked**, so 79 characters padded with spaces still fail.

## Step 4: create, plus rule 7

### What was built

- `app/services/exceptions.py`: `DomainError` is the base class, with `code`, `message` and `existing_id`. `DuplicateRecommendation` carries the existing id.
- `app/services/recommendations.py`:
  - `create_recommendation(session, author, data)` computes the keys, calls `_ensure_unique` and reuses existing tags (`_get_or_create_tags`).
  - `_ensure_unique` queries for an existing `(type, artist_key, title_key)` and raises `DuplicateRecommendation(existing_id)`.
- `app/services/users.py`: `DEV_CURATOR_EMAIL` and `get_dev_curator()`.
- `app/dependencies.py`: `SessionDep` and `CurrentUser`, both `Annotated[..., Depends(...)]`. Slice 4 changes only the body of `get_current_user`.
- `app/routers/responses.py`: `error_responses(409, 422)` documents each error status with `ErrorOut`.
- `app/routers/recommendations.py`: `POST /recommendations` returns 201.
- `main.py`:
  - `STATUS_BY_ERROR` maps each domain error to a status code, and a single handler turns any `DomainError` into an `ErrorOut`.
  - A second handler turns FastAPI's request validation errors into `ErrorOut` with `code: "validation_error"`, so every error response has the same shape, as the contract requires.
  - `generate_unique_id_function` turns `create_recommendation` into the operation id `createRecommendation`.
- Tests:
  - `test_recommendations_service.py`: rule 7 with different case and spacing, artist recommendations, the same title with another type, and tag reuse.
  - `test_recommendations_api.py`: checks the status codes and the response shape.
  - `test_every_domain_error_has_a_status_code`: fails if a new exception is added without a status code.

### Concepts

- **Domain exceptions and Swift typed `throws`.** Python does not declare what a function throws. The contract lives in the exception class and in the tests. `raise X from error` keeps the original error as `__cause__`, much like wrapping an `underlyingError`.
- **`Depends`** is dependency injection resolved per request. `Annotated[Session, Depends(get_session)]` is written once and reused as `SessionDep` in every route.
- **`app.add_exception_handler(DomainError, ...)`** also catches subclasses, because Starlette walks the class hierarchy (the MRO).
- **`pytest --cov`** with `fail_under = 100` (configured in `pyproject.toml`) is like an Xcode code coverage gate, but limited to `app/services`.

## Step 5: read endpoints

### What was built

- `get_recommendation()` raises `RecommendationNotFound`, and the API returns 404.
- `list_recommendations(session, genre=, cursor=, limit=)`:
  - Sorts by `created_at desc, id desc` and fetches `limit + 1` rows to know whether a next page exists.
  - Filters with `Recommendation.tags.any(Tag.name == normalize_key(genre))`.
  - The cursor is base64url of `"<created_at iso>|<id>"`. The app treats it as opaque. An invalid cursor raises `InvalidCursor`, which returns 422.
  - `joinedload(author)` and `selectinload(tags)` avoid N+1 queries.
- `app/services/tags.py` and `app/routers/tags.py`: `GET /tags`, sorted by name.
- `GET /recommendations?limit=` is between 1 and 100, with a default of 20.
- A test seeds 2000 recommendations and checks that the feed answers in under 300 ms.

### The bug found by the pagination test

The test that pages through 7 recommendations created within the same second got the same 3 rows on every page. Two causes stacked up:

1. SQLite has no datetime type. `CURRENT_TIMESTAMP` stores the text `2026-11-21 19:18:35`, but SQLAlchemy sends a Python `datetime` as `2026-11-21 19:18:35.000000`. Compared as text, the shorter string is "smaller", so the `created_at == cursor` comparison never matched.
2. `tuple_(created_at, id) < tuple_(value, id)` does not give the bound values the column's type, so even a column-level fix would not apply inside the tuple.

The fixes:

- `app/models.py` defines `Timestamp`, a `DateTime` with a SQLite variant that uses the same `YYYY-MM-DD HH:MM:SS` format as the database.
- The cursor filter uses `or_(created_at < c, and_(created_at == c, id < cid))`, so each bound value takes its column's type.

The schema did not change, and `alembic check` still reports no drift.

### Concepts

- **`select()` in SQLAlchemy 2.0** builds a query value, which `session.scalars()` then runs. It feels like building an `NSFetchRequest` or a GRDB `QueryInterfaceRequest`, then fetching.
- **Keyword-only parameters (`*`)** in `list_recommendations(session, *, genre=None, ...)` force callers to name the arguments. That is the default for Swift argument labels; in Python you opt in.
- **`Query(ge=1, le=100)`** validates the query parameter and documents the range in OpenAPI.

## Step 6: edit and delete

### What was built

- `update_recommendation(session, id, data)`:
  1. Loads the recommendation (404 if it is missing).
  2. Builds `changes = data.model_dump(exclude_unset=True)`.
  3. Checks rule 2 on the **merged** state. For example, `{"type": "artist"}` on an album fails with `InvalidRecommendation` (422) unless the body also sends `"title": null`.
  4. Recomputes the keys and checks rule 7 again, skipping its own id, when `type`, `artist` or `title` change.
  5. Replaces the genres if they were sent, and sets `updated_at = func.now()`. Without that, an edit that changes only the genres would not update the timestamp, because `onupdate` only fires when a column changes.
- `delete_recommendation()`: 204 with an empty body. The join rows go with the recommendation; the tags stay.
- `PATCH` and `DELETE` routes with 404, 409 and 422 declared in `responses=`.
- A test that lists every operation id in `/openapi.json`.

### Concepts

- **`dict | dict`** merges dictionaries; the right side wins. `{"type": stored, "title": stored} | changes` is the merged view, similar to `merging(_:uniquingKeysWith:)` keeping the new value.
- **`setattr(obj, name, value)`** is dynamic assignment by name. Swift does not allow it without key paths, and here it keeps the partial update to three lines.

## Decisions taken during implementation

These were not in the plan. Revisit them if you disagree.

1. **Request validation errors use `ErrorOut`.** FastAPI's default 422 body has a different shape. The contract says every error uses `ErrorOut`, so `main.py` converts it, and `message` lists `field: problem` pairs.
2. **Genres are deduplicated after normalizing.** `["Jazz", "jazz "]` becomes `["jazz"]`, and the count rule (1 to 5) applies after deduplication. Tags also collapse repeated spaces, the same as the rule 7 keys.
3. **Empty titles become `null`.** `""` and `"   "` are treated as "no title", so an artist recommendation sent with `"title": ""` is valid.
4. **Rule 7 under a race.** If two requests create the same recommendation at the same moment, the second one gets past the service check, hits the unique index and returns 500 instead of 409. That is acceptable with one curator. Handle it if it ever matters: catch `IntegrityError` on commit, roll back, query again and raise `DuplicateRecommendation`.
5. **Rule 5 is not enforced.** Anyone can edit or delete. The routes have a comment pointing to slice 4.
6. **Test helpers are imported as `from tests.conftest import ...`.** Fixtures are injected by pytest, but plain helpers like `make_recommendation` and `VALID_TEXT` have to be imported.

## Commands

```
cd api
uv run pytest --cov          # tests plus the 100% service coverage gate
uv run ruff check . && uv run ruff format .
uv run alembic upgrade head  # creates garimpo.db with the dev curator
uv run fastapi dev main.py   # http://127.0.0.1:8000/docs
```

## What moves to slice 3

- The API is ready for the app: the feed, detail and create routes all exist, with camelCase operation ids and typed errors, so `openapi-typescript` can generate `schema.d.ts`.
- Before slice 3, merge `slice-2` into `main` (or open a pull request) and run `/slice 3`.
