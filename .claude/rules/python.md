---
paths:
  - "api/**/*.py"
---

# Python style

- Type annotations on every function and method signature, including the return type (`-> None`).
- Naming: `snake_case` for functions, variables and modules; `PascalCase` for classes; `UPPER_SNAKE_CASE` for constants.
- Compare with `None` using `is` and `is not`, never `==`.
- Format strings with f-strings.
- Never use a bare `except:` or a generic `except Exception:`; catch the specific exception.
- Absolute imports only; ruff owns the ordering.
- Data crossing the HTTP boundary is a Pydantic model in `schemas.py`. Never return SQLAlchemy models directly from routers.

# Swift habits to avoid

When writing or reviewing code, replace these patterns with the Python equivalent:

- A class that only groups stateless functions → module-level functions.
- Explicit getters and setters → a public attribute; use `@property` only when there is logic.
- A protocol for every dependency → `typing.Protocol` only when there are at least two real implementations.
- Chained optionals imitating `?.` → an explicit `if x is None: return ...` early in the function.
- Raw-value enums everywhere → `enum.StrEnum` when the value is persisted or sent as JSON; otherwise `Literal`.

# Tests

- Files named `tests/test_<module>.py`; functions named `test_<behavior>_<expected_result>`.
- Plain `assert`, no assertion libraries.
- Shared fixtures in `tests/conftest.py`.
- Business rules are tested at the service level, without HTTP. Routers are tested with `TestClient`, covering status codes and response shape.
- Files stay flat in `tests/`: `test_<resource>_service.py` for rules, `test_<resource>_api.py` for routers, `test_schemas.py`, `test_models.py`, `test_migrations.py`.
- Services and schemas are written test first (red, green, refactor). Models and migrations get tests alongside them.
- Tests use the real in-memory SQLite session; do not mock the database or SQLAlchemy.
- Test data comes from helper functions in `conftest.py` (`make_user`, `make_recommendation`) with keyword overrides.
