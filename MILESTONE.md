# Current Milestone: M1 — Infrastructure & Project Scaffold

## Goal
Full Docker Compose stack (frontend, backend, db) starts cleanly, health endpoint responds, DB schema is applied, and CI-ready test suites pass inside containers.

## What this means for agents

**Dev Agent:** Read ARCHITECTURE.md before writing any code. Every file you create must conform to the architecture defined there. Do not invent new patterns.

**QA Agent:** Tests must verify the milestone goal, not just pass in isolation. After M1, the full Docker stack must build and run. After M2, all API endpoints must respond correctly.

**Review Agent:** Reject any PR that deviates from ARCHITECTURE.md without a documented reason in DECISIONS.md.

## What is NOT in scope for this milestone
Do not implement features from future milestones. If you discover something missing that blocks this milestone, file a ticket with `priority:high` and tag it to this milestone.

## Definition of Done
- All milestone tickets closed
- `docker compose up --build` succeeds with no errors
- All tests pass inside Docker
- Integration smoke test passes (PM Agent will verify before closing milestone)
