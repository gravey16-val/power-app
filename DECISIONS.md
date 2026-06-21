# Architecture Decisions

This file records architectural decisions made during development.
Agents: if you need to deviate from ARCHITECTURE.md, document WHY here before doing so.

---

## Decision Log

| Date | Decision | Reason | Made by |
|------|----------|--------|---------|
| 2026-06-21 | Frontend Dockerfile uses `node:20-slim` instead of ARCHITECTURE.md's `node:20-alpine` | Ticket "Frontend Dockerfile & Vite dev server setup" explicitly specifies `node:20-slim` in both its description and acceptance criteria. The ticket is the binding work order; the deviation is recorded here per MILESTONE.md's review rule. `slim` (Debian-based, glibc) also avoids musl-related native-module surprises versus `alpine`. ARCHITECTURE.md should be reconciled to `node:20-slim` in a follow-up. | Dev Agent |
