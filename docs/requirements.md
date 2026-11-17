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

- `users` — id, email, display name, password hash, created at
- `invites` — code, created by, used by, used at
- `recommendations` — id, author, type, artist, title, text, hidden, created at
- `tags` — id, name
- `recommendation_tags` — recommendation, tag
- `votes` — user, recommendation (composite key)
- `saves` — user, recommendation (composite key)
- `reports` — user, recommendation, reason, created at

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
