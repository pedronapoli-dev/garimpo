# App

Expo SDK 58 + TypeScript, Expo Router, TanStack Query, openapi-fetch. Expo changes quickly between SDKs: read `AGENTS.md` and the versioned docs before touching an Expo API.

## Commands

Always run from inside `app/`.

- Install a package: `npx expo install <package>` (picks the version that matches the SDK); dev-only: `npm install --save-dev <package>`
- Tests: `npm test` (Jest with `jest-expo`). If watchman crashes, run `npm test -- --no-watchman` or fix it with `brew reinstall watchman`.
- Typecheck: `npm run typecheck`
- Lint: `npm run lint`
- Format: `npm run format` (`npm run format:check` in CI)
- API types: `npm run generate:api` regenerates `src/api/schema.d.ts` from the API's OpenAPI. Run it after any API change and commit the result. Never edit `schema.d.ts` by hand.
- Run: start the API (`cd ../api && uv run fastapi dev main.py`), then `npm run ios`. On a device or the Android emulator, set `EXPO_PUBLIC_API_URL` in `.env.local`.

A step is done only when tests, typecheck, lint and format all pass.

## Layout

```
src/
  app/                    Expo Router routes only; each file re-exports a screen
  api/                    schema.d.ts (generated), client.ts, errors.ts
  features/<feature>/
    types.ts              aliases over the generated schema types
    queries.ts            TanStack Query hooks and query keys
    cache.ts              pure cache updates
    form.ts               pure form validation (mirrors the API rules, for UX only)
    components/           screens and components of the feature
  components/             shared UI
  test-utils/             fixtures and the QueryClient test wrapper
```

- Server data lives only in the TanStack Query cache.
- Business rules belong to the API. The app validates only for feedback while typing and always shows the API's 409 and 422 messages.
- Tests sit next to the code as `*.test.ts(x)`, never inside `src/app/` (every file there becomes a route).
- RNTL v14: `render`, `renderHook`, `fireEvent` and `act` are async; always `await` them.
