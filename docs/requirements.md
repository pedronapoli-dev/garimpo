# Garimpo — requirements and system design

Study project for ramping up on React Native and Python. Open source. Scope closed on 2026-11-16.

## Vision

Music curation made by people: music diggers recommend lesser-known artists, albums and tracks, always with a "why listen" text. There is no recommendation algorithm and no dependency on external data.

- **Audience:** curious listeners who explore music by genre.
- **Golden rule:** the app must be useful with a single curator. Community is a bonus.
- **Out of scope:** audio playback, automatic recommendations, Last.fm, data dumps, moderation tooling.
- **Project goal:** learning both technologies, not user growth.

## Business rules

1. Sign-up is invite-only. Every user can generate invites; each invite can be used once.
2. Every recommendation has a type (artist, album or track), an artist name, a title when applicable, 1 to 5 genres (tags) and a mandatory text of 80 to 1000 characters.
3. "Lesser-known" is a house rule, described in the community guidelines and enforced through reports. There is no numeric threshold.
4. One vote per user per recommendation. Users cannot vote on their own recommendations.
5. Only the author can edit or delete a recommendation.
6. A recommendation with 3 reports is hidden from the feed until reviewed.
7. The same artist + title combination cannot be recommended twice; the second user is sent to the existing recommendation.

## Functional requirements

### MVP
- FR1. Sign up with an invite code; log in and log out.
- FR2. Create, edit and delete a recommendation.
- FR3. Paginated feed, filterable by genre, sorted by newest or most voted.
- FR4. Recommendation detail screen.
- FR5. Vote and remove a vote.
- FR6. Save and unsave ("listen later").
- FR7. Curator profile with their recommendations.
- FR8. Generate an invite code.
- FR9. Report a recommendation.

### Later
- FR10. Artist and album autocomplete via MusicBrainz, with manual entry as a fallback.
- FR11. Curator stats (most recommended genres, votes received).

## Non-functional requirements

- The feed responds in under 300 ms locally, with cursor-based pagination.
- Voting uses optimistic updates in the app, rolled back on error.
- Passwords hashed with Argon2; JWT stored in SecureStore.
- Business rules live in the service layer with 100% test coverage.
- No MVP requirement depends on an external service.
- The API contract is OpenAPI; the app's TypeScript types are generated from it.

## Data model

Approved on 2026-11-18.

### Relationships

```
users 1 ───< N recommendations N >───< N tags   (via recommendation_tags)
users 1 ───< N votes   >─── N recommendations
users 1 ───< N saves   >─── N recommendations
users 1 ───< N reports >─── N recommendations
users 1 ───< N invites (created_by); users 0..1 ─── 1 invites (used_by)
```

### Tables

- `users` — id, email, display name, password hash, created at
  - `UNIQUE(email)`; email stored in lowercase.
- `invites` — code, created by, used by, used at
  - `code` is the primary key; `used_by` is nullable and `UNIQUE` (rule 1).
- `recommendations` — id, author, type, artist, title, artist key, title key, text, hidden, created at, updated at
  - `author_id` references `users` with `ON DELETE RESTRICT`.
  - `type` is one of `artist`, `album`, `track`, enforced by a `CHECK`.
  - `title` is null for `artist`; `title_key` is `''` in that case, never null, so the unique index below still applies.
  - `artist_key` and `title_key` are normalized: lowercase, trimmed, repeated spaces collapsed.
  - `UNIQUE(type, artist_key, title_key)` enforces rule 7 at the database level; the service checks it first to return the existing id.
  - `CHECK` on the text length (80 to 1000 characters).
  - `hidden` defaults to false (rule 6, slice 6).
  - Index on `(created_at, id)` for the feed cursor.
- `tags` — id, name
  - `UNIQUE(name)`; stored trimmed and in lowercase.
- `recommendation_tags` — recommendation, tag
  - Composite primary key; `ON DELETE CASCADE` from the recommendation, `ON DELETE RESTRICT` from the tag.
  - "1 to 5 genres" (rule 2) is enforced in the schema and service; SQL cannot express it.
- `votes` — user, recommendation (composite key)
- `saves` — user, recommendation (composite key)
- `reports` — user, recommendation, reason, created at
  - `UNIQUE(user_id, recommendation_id)`, so 3 reports come from 3 different users (rule 6).

### Conventions

- SQLite foreign keys are turned on per connection (`PRAGMA foreign_keys=ON`).
- `Base.metadata` uses a constraint naming convention, which Alembic needs to alter SQLite tables.
- Timestamps are UTC and set by the database (`server_default`).
- Rules that SQL can express are also database constraints, in addition to the service checks.

### Author before auth (slices 2 and 3)

- A separate seed migration creates the dev curator (display name "Pedro", email `curator@garimpo.local`, password hash `"!"`, which no password matches).
- Routes get the author from a `get_current_user` dependency that returns the dev curator. Slice 4 replaces only that dependency's body with JWT validation.

## Endpoints

- `POST /auth/signup`, `POST /auth/login`
- `GET /recommendations`, `POST /recommendations`
- `GET /recommendations/{id}`, `PATCH /recommendations/{id}`, `DELETE /recommendations/{id}`
- `PUT /recommendations/{id}/vote`, `DELETE /recommendations/{id}/vote`
- `PUT /recommendations/{id}/save`, `DELETE /recommendations/{id}/save`
- `POST /recommendations/{id}/reports`
- `GET /users/{id}`, `GET /me/saves`
- `POST /invites`
- `GET /tags`

## Stack

| Layer | Choice | iOS equivalent |
|---|---|---|
| App | Expo + TypeScript | Xcode + SPM |
| Navigation | Expo Router | NavigationStack |
| Remote data | TanStack Query | Repository + cache + async/await |
| Local state | Zustand | @Observable class |
| Token storage | expo-secure-store | Keychain |
| Python project | uv | SPM |
| API | FastAPI + Pydantic | Vapor + Codable |
| Database | SQLAlchemy 2.0 + Alembic, SQLite | GRDB / Core Data + migrations |
| Tests and lint | pytest + ruff | Swift Testing + SwiftLint |

## Repository layout

```
garimpo/
  api/    Python service
  app/    Expo app
  docs/   requirements and decisions
  README.md
  LICENSE
```

## Delivery slices

1. Minimal API: uv project, health endpoint, one test. **Done.**
2. Models, migrations and recommendation CRUD, still without auth.
3. App: feed, detail and create form.
4. Auth and invites, in the API and the app.
5. Votes, saves and profile.
6. Reports, README, license and community guidelines.

Suggested effort split: 60% API, 40% app.
