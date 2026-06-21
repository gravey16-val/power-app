# Architecture Decisions

This file records architectural decisions made during development.
Agents: if you need to deviate from ARCHITECTURE.md, document WHY here before doing so.

---

## Decision Log

| Date | Decision | Reason | Made by |
|------|----------|--------|---------|
| 2026-06-21 | Backend non-root user is named `appuser` (not `app` as shown in the original ARCHITECTURE.md Dockerfile snippet). ARCHITECTURE.md updated to match. | Ticket "Backend Dockerfile & non-root user setup" explicitly requires the user `appuser`. Single canonical name keeps docs and image consistent. | Dev (ticket-65) |
| 2026-06-21 | Backend source lives at the `backend/` root (`uvicorn main:app`), not under a `backend/app/` package. | Matches the canonical ARCHITECTURE.md component tree and CLAUDE.md, which both reference `main.py`/`database.py` at the backend root and the `main:app` entrypoint. | Dev (ticket-65) |
| 2026-06-21 | Tests force `DATABASE_URL=sqlite+pysqlite:///:memory:` in `tests/conftest.py`; `database.py` uses `StaticPool` for SQLite URLs. | Keeps the pytest suite hermetic (no Postgres/network), per the CLAUDE.md testing convention, while production still reads Postgres from `DATABASE_URL`. | Dev (ticket-65) |
| 2026-06-21 | Added a minimal `frontend/` scaffold (Vite + React shell, single passing Vitest test) alongside the backend Dockerfile ticket. | The reported failure was the full-stack `docker compose up --build` aborting with "frontend not found" (missing build context). M1 DoD requires the stack to build and the frontend test harness to run. Only the scaffold/harness is added here — the full two-panel shell remains M3. | Dev (ticket-65) |
| 2026-06-21 | Frontend Dockerfile uses `npm install` + `CMD ["npm","run","dev","--","--host",...]` instead of the `npm ci` + `npx vite --host` snippet in ARCHITECTURE.md. | No committed `package-lock.json` exists yet for the M1 scaffold, so `npm ci` would fail; `npm install` is reproducible enough for dev. `npm run dev -- --host` matches the project's mandatory Docker rules. ARCHITECTURE.md snippet updated to match. | Dev (ticket-65) |
| 2026-06-21 | Removed the obsolete `version: "3.9"` key from `docker-compose.yml`. | Compose v2 ignores it and emits a warning; dropping it removes noise. | Dev (ticket-65) |
