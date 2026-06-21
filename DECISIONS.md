# Architecture Decisions

This file records architectural decisions made during development.
Agents: if you need to deviate from ARCHITECTURE.md, document WHY here before doing so.

---

## Decision Log

| Date | Decision | Reason | Made by |
|------|----------|--------|---------|
| 2026-06-21 | Configuration is driven entirely by env vars loaded from a gitignored `.env`; `.env.example` is the committed template. | One-step local setup (`cp .env.example .env && docker compose up`) while keeping secrets out of source control. | Dev Agent (ticket: env config) |
| 2026-06-21 | `DATABASE_URL` has no hardcoded fallback — the backend raises on startup if it is unset. | A hardcoded fallback embeds credentials in source and, on Render, silently targets an unreachable `db` host. Fail fast instead. | Dev Agent |
| 2026-06-21 | CORS origins are read from `CORS_ORIGINS` (default `http://localhost:5173`), never `"*"`. | `allow_origins=["*"]` with `allow_credentials=True` is invalid per the CORS spec and a production security risk. | Dev Agent |
| 2026-06-21 | Backend CMD binds to `${PORT:-8000}`; base images and Python deps are pinned. | Render injects its own `$PORT`; pinning avoids silent dependency/version drift across builds. | Dev Agent |
| 2026-06-21 | Frontend Dockerfile uses `npm install` (no committed `package-lock.json`) for the M1 scaffold. | Avoids committing a lock file before dependencies stabilise; revisit and switch to `npm ci` with a committed lock once the dependency set is final. | Dev Agent |
| 2026-06-21 | Backend startup retries the schema-creation DB connection (bounded, then fails fast); the db healthcheck gains a `start_period`. | On first `docker compose up` Postgres briefly reports ready on its bootstrap server; a single transient `OperationalError` would otherwise crash uvicorn and `restart: unless-stopped` would loop forever, blocking `docker compose exec`. Retry tolerates the race without weakening fail-fast. | Dev Agent |
