# Agent Context — pytest setup inside backend container
*Retrieved 1 relevant documents from shared knowledge base*

## Architecture & Decisions

**doc:CLAUDE.md** _CLAUDE.md_
# CLAUDE.md — Weather Dashboard: Real-time City Weather Tracker

## Environment Configuration (.env)

All runtime config is supplied via environment variables that Docker Compose
loads from a gitignored `.env` file. `.env.example` is the committed, documented
template.

**One-step local setup:**
```bash
cp .env.example .env
docker compose up --build
```

| Variable            | Service  | Notes                                                    |
|---------------------|----------|----------------------------------------------------------|
| `POSTGRES_USER/PASSWORD/DB` | db | Initialise the loc