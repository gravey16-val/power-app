# Architecture Decisions

This file records architectural decisions made during development.
Agents: if you need to deviate from ARCHITECTURE.md, document WHY here before doing so.

---

## Decision Log

| Date | Decision | Reason | Made by |
|------|----------|--------|---------|
| 2026-06-21 | Backend uses a **flat** module layout (`backend/main.py`, `database.py`, `models.py`) rather than `backend/app/`. | Matches ARCHITECTURE.md (canonical) and the Dockerfile CMD `uvicorn main:app`. | Dev (ticket-67) |
| 2026-06-21 | Schema created via `Base.metadata.create_all()` in the FastAPI **lifespan** startup hook; no Alembic. | M1 simplicity; `create_all` is idempotent. Used lifespan instead of the deprecated `@app.on_event("startup")`. | Dev (ticket-67) |
| 2026-06-21 | `render.yaml` sets `VITE_API_URL` with `sync: false` (no hardcoded backend URL) and pins `plan: free` on every service with comments about free-tier limits. | Addresses prior review feedback on hardcoded prod URLs and missing/implicit plan keys. | Dev (ticket-67) |
