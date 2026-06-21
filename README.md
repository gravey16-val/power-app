# Weather Dashboard — Real-time City Weather Tracker

A containerized full-stack app for tracking current weather across cities.

- **Frontend:** React 18 + TypeScript + Vite + Tailwind (port 5173)
- **Backend:** FastAPI + SQLAlchemy (port 8000)
- **Database:** PostgreSQL 16 (port 5432)

Everything runs in Docker — no local Python or Node required.

## Quick Start (one step)

```bash
# 1. Create your local environment file from the template
cp .env.example .env

# 2. Build and start the full stack
docker compose up --build
```

That's it. Docker Compose reads `.env` automatically and injects the values into
each service. Once running:

| Service  | URL                          |
|----------|------------------------------|
| Frontend | http://localhost:5173        |
| Backend  | http://localhost:8000        |
| API Docs | http://localhost:8000/docs   |
| Health   | http://localhost:8000/health |

Run detached with `docker compose up --build -d`; stop with `docker compose down`
(add `-v` to also drop the database volume).

## Environment Variables

All configuration lives in `.env` (gitignored). `.env.example` is the committed,
documented template — copy it and edit as needed.

| Variable            | Service   | Description                                                        |
|---------------------|-----------|--------------------------------------------------------------------|
| `POSTGRES_USER`     | db        | Postgres username used to initialise the local database.          |
| `POSTGRES_PASSWORD` | db        | Postgres password.                                                 |
| `POSTGRES_DB`       | db        | Postgres database name.                                            |
| `DATABASE_URL`      | backend   | SQLAlchemy connection string. **Required** — backend fails fast if unset. |
| `CORS_ORIGINS`      | backend   | Comma-separated allowed origins. Defaults to the local frontend.   |
| `VITE_API_URL`      | frontend  | Base URL the browser uses to reach the backend (build-time).       |

> `DATABASE_URL` has **no hardcoded fallback**. If it is missing the backend
> raises a clear error on startup instead of silently connecting to a wrong/
> unreachable host. Local-dev defaults are documented only in `.env.example`.

## Testing

```bash
# Start the stack first
docker compose up --build -d

# Backend (pytest)
docker compose exec backend pytest

# Frontend (Vitest)
docker compose exec frontend npx vitest run
```

## More Docs

- `ARCHITECTURE.md` — canonical architecture, DB schema, API contracts
- `CLAUDE.md` — how to run, test, and extend the app
- `MILESTONE.md` — current milestone scope
- `DECISIONS.md` — architectural decision log
