# Architecture Decisions

This file records architectural decisions made during development.
Agents: if you need to deviate from ARCHITECTURE.md, document WHY here before doing so.

---

## Decision Log

| Date | Decision | Reason | Made by |
|------|----------|--------|---------|
| 2026-06-21 | `render.yaml` uses `runtime:` instead of the deprecated `env:` key, and adds `rootDir: backend` / `rootDir: frontend`. | Backend and frontend live in subdirectories, so Render must `cd` into each before running build/start commands. `runtime` is Render's current canonical key (`env` is a deprecated alias). Extends the ARCHITECTURE.md §Deployment template without changing its intent. | Dev Agent (ticket-72) |
| 2026-06-21 | Frontend static site adds a `routes` rewrite (`/* → /index.html`) and backend adds `healthCheckPath: /health`. | SPA client-side routing needs an index.html fallback; the health check lets Render gate deploys on the existing `GET /health` endpoint. | Dev Agent (ticket-72) |
| 2026-06-21 | `VITE_API_URL` is set to the literal `https://weather-backend.onrender.com` rather than a `fromService` reference. | Render's `fromService` exposes only `host`/`port`/`hostport` (no full-URL property), and Vite bakes the value at build time, so a complete `https://` URL is required. Matches ARCHITECTURE.md §Deployment. Not a localhost/secret value, so it does not violate the "no hardcoded URLs" rule. | Dev Agent (ticket-72) |
