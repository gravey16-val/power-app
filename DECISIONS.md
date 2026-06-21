# Architecture Decisions

This file records architectural decisions made during development.
Agents: if you need to deviate from ARCHITECTURE.md, document WHY here before doing so.

---

## Decision Log

| Date | Decision | Reason | Made by |
|------|----------|--------|---------|
| 2026-06-21 | No hardcoded `DATABASE_URL` fallback in `database.py`; raise at import if unset | A committed fallback embeds plaintext creds and silently points at the unreachable compose host `db` on Render. Fail loudly instead. | Dev Agent (ticket-64) |
| 2026-06-21 | CORS origins read from `CORS_ORIGINS` env var (`*` dev-only), `allow_credentials=False` | `allow_origins=["*"]` + credentials is invalid per the CORS spec and unsafe. App uses no cookies/auth. | Dev Agent (ticket-64) |
| 2026-06-21 | Backend `CMD` binds to `${PORT:-8000}`; render.yaml startCommand uses `$PORT` | Render injects `$PORT` and routes to it; a hardcoded `--port 8000` breaks health checks/routing. | Dev Agent (ticket-64) |
| 2026-06-21 | Pin exact dependency versions + base image patch tags (`python:3.12.8-slim`, `node:20.18-alpine`) | Bare `>=` / floating image tags let each build drift. Exact pins = reproducible builds. | Dev Agent (ticket-64) |
| 2026-06-21 | `conftest.py` forces `DATABASE_URL=sqlite://` **before** importing the app | The engine (and the lifespan `create_all`) is built at import time; overriding only `get_db` would still hit real Postgres during startup. | Dev Agent (ticket-64) |
| 2026-06-21 | Frontend tests live in `frontend/src/__tests__/` (deviates from ARCHITECTURE.md `src/tests/`) | Ticket-64 mandatory testing rules specify `src/__tests__/`. Setup file at `src/__tests__/setup.ts`, wired via `vite.config.ts`. | Dev Agent (ticket-64) |
| 2026-06-21 | Frontend Dockerfile uses `npm install` (not `npm ci`) | Scaffold ships without a committed lockfile on first build; `npm ci` requires `package-lock.json`. | Dev Agent (ticket-64) |
| 2026-06-21 | M1 backend implements only `/health` + `cities` table schema | Cities/weather/geocode routers are M2 scope; M1 is infrastructure + schema + test harness only. | Dev Agent (ticket-64) |
| 2026-06-21 | Frontend `App.test.tsx` stubs `VITE_API_URL` via `vi.stubEnv`; `App.tsx` uses `\|\|` fallback | The compose `frontend` service sets `VITE_API_URL`, and Vite surfaces `VITE_`-prefixed env vars on `import.meta.env`, so the value is present (not undefined) when vitest runs in-container. Tests must control the env, not assume it. | Dev Agent (ticket-64) |
