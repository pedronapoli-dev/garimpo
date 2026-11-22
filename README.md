# Garimpo

Music curation made by people. Curators recommend lesser-known artists, albums and tracks, always with a "why listen" text. There is no recommendation algorithm and no external data: just people who dig.

Garimpo is an open source study project: a Python API and a React Native app, built in small slices. See [`docs/requirements.md`](docs/requirements.md) for the full requirements and [`docs/community-guidelines.md`](docs/community-guidelines.md) for the house rules.

## Features

- Invite-only sign-up; every curator can invite others, each code works once.
- Recommend an artist, album or track with 1 to 5 genres and an 80 to 1000 character text.
- The same artist and title cannot be recommended twice; you are sent to the existing one.
- A feed sorted by newest or most voted, filtered by genre, with cursor pagination.
- Votes (one per person, never on your own), "listen later" saves and curator profiles.
- Three reports from different people hide a recommendation until it is reviewed.
- Optional curator assist: while writing, Claude says whether the text explains why to listen and suggests existing genres. It never recommends music. Without an API key the app works the same, without the assist.

## Stack

| Part | Choice |
|---|---|
| API | FastAPI, Pydantic, SQLAlchemy 2 + Alembic, SQLite, managed with uv |
| App | Expo (React Native + TypeScript), Expo Router, TanStack Query, Zustand |
| Contract | OpenAPI; the app's types are generated from it with openapi-typescript |
| Tests | pytest (100% coverage on business rules), Jest + React Native Testing Library |

## Getting started

You need [uv](https://docs.astral.sh/uv/), Node.js 24 and, for the iOS simulator, Xcode.

```sh
# API: http://127.0.0.1:8000, interactive docs at /docs
cd api
uv sync
uv run alembic upgrade head
uv run python -m app.cli create-invite   # prints the first invite code
uv run fastapi dev main.py
```

```sh
# App, in another terminal
cd app
npm install
npm run ios
```

Sign up in the app's Account tab with the invite code. On a physical device or the Android emulator, point the app to your machine with `EXPO_PUBLIC_API_URL` in `app/.env.local` (for example `http://10.0.2.2:8000` on Android).

Outside local development, set `GARIMPO_JWT_SECRET` to a long random value.

The curator assist is off unless the API has a model behind it:

| Variable | Effect |
|---|---|
| `GARIMPO_ASSIST_FAKE=1` | Serves a deterministic fake, to work on the app without a key or any cost |
| `ANTHROPIC_API_KEY` | Enables the assist with Claude (once `api/app/llm/claude.py` is implemented) |
| `GARIMPO_ASSIST_PROVIDER` | `anthropic` by default, or `bedrock` to use AWS credentials |
| `GARIMPO_ASSIST_MODEL` | The Claude model, Sonnet 5.5 by default |
| `GARIMPO_DATABASE_URL` | The database, `sqlite:///./garimpo.db` by default |
| `GARIMPO_ENV` | `production` refuses to start without a strong `GARIMPO_JWT_SECRET` |

## Checks

```sh
cd api && uv run pytest --cov && uv run pyright && uv run ruff check . && uv run ruff format --check .
cd api && uv run python -m evals.run           # curator assist evals with the fake; --live calls Claude
cd app && npm test && npm run typecheck && npm run lint && npm run format:check
cd app && npm run generate:api   # after any API change; commit src/api/schema.d.ts
```

CI runs all of them, and fails when `schema.d.ts` is out of date.

## Reviewing hidden recommendations

There is no moderation tooling. After 3 reports a recommendation is hidden from every list. A maintainer reads the reports and either deletes the recommendation or restores it:

```sh
cd api
sqlite3 garimpo.db "SELECT reason, created_at FROM reports WHERE recommendation_id = 42;"
# Restore it (and clear its reports, so it is not hidden again by old reports):
sqlite3 garimpo.db "UPDATE recommendations SET hidden = 0 WHERE id = 42; DELETE FROM reports WHERE recommendation_id = 42;"
# Or delete it (votes, saves, tags and reports go with it):
sqlite3 garimpo.db "PRAGMA foreign_keys = ON; DELETE FROM recommendations WHERE id = 42;"
```

## Repository layout

```
api/    FastAPI service (see api/CLAUDE.md)
app/    Expo app (see app/CLAUDE.md)
docs/   requirements, guidelines, slice plans and blueprints
```

## License

[MIT](LICENSE)
