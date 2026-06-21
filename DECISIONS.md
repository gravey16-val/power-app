# Architecture Decisions

This file records architectural decisions made during development.
Agents: if you need to deviate from ARCHITECTURE.md, document WHY here before doing so.

---

## Decision Log

| Date | Decision | Reason | Made by |
|------|----------|--------|---------|
| 2026-06-21 | CORS origins are read from a `CORS_ORIGINS` env var (default `http://localhost:5173`) instead of allowing all origins. | Per-environment configurability without code changes; avoids wildcard origins with credentials. Aligns with prior review feedback against hardcoded URLs. | Dev (ticket-68) |
| 2026-06-21 | Frontend Dockerfile uses `npm install` instead of `npm ci`. | No `package-lock.json` is committed yet at M1 scaffold; `npm ci` requires a lockfile. Revisit and switch to `npm ci` once a lockfile is generated. | Dev (ticket-68) |
| 2026-06-21 | `Base.metadata.create_all` runs in a FastAPI `lifespan` startup hook rather than at import time. | Keeps module import (and unit tests) independent of a reachable PostgreSQL instance; schema is still applied on app startup. | Dev (ticket-68) |
| 2026-06-21 | `render.yaml`: `VITE_API_URL` and `CORS_ORIGINS` use `sync: false`; explicit `plan: free` on all services with a free-tier caveat comment; pip upgraded before install. | Directly addresses prior review feedback (hardcoded prod URL, missing plan, unannounced free-tier data loss, no pip pinning/upgrade). | Dev (ticket-68) |
