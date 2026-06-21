# Architecture Decisions

This file records architectural decisions made during development.
Agents: if you need to deviate from ARCHITECTURE.md, document WHY here before doing so.

---

## Decision Log

| Date | Decision | Reason | Made by |
|------|----------|--------|---------|
| 2026-06-21 | Frontend test config lives in a dedicated `vitest.config.ts` (which `mergeConfig`s `vite.config.ts`) rather than inline in `vite.config.ts` as drawn in ARCHITECTURE.md. | Ticket #71 acceptance criteria explicitly require a `vitest.config.ts` using the jsdom environment. Merging keeps the React plugin in sync and avoids a dead/duplicated test block. | Dev Agent (ticket-71) |
| 2026-06-21 | Backend startup uses a FastAPI `lifespan` handler for `Base.metadata.create_all`, replacing the deprecated `@app.on_event("startup")` shown in CLAUDE.md. | `on_event` is deprecated in current FastAPI/Starlette; `lifespan` is the supported equivalent and keeps test output free of deprecation warnings. Behaviour (idempotent schema creation on startup) is unchanged. | Dev Agent (ticket-71) |
