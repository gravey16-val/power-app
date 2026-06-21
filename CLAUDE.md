# CLAUDE.md — Weather Dashboard

## Quick Start

```bash
# Clone and start the full stack — no host dependencies required
git clone <repo-url>
cd weather-dashboard
docker compose up --build
```

| Service   | URL                       |
|-----------|---------------------------|
| Frontend  | http://localhost:5173     |
| Backend   | http://localhost:8000     |
| API Docs  | http://localhost:8000/docs |
| DB        | localhost:5432            |

> **Everything runs inside Docker.** No local Python, Node, or PostgreSQL installation is required.

---

## How to Run

### Start the stack
```bash
docker compose up --build          # first run (builds images)
docker compose up                  # subsequent runs
docker compose up -d               # detached mode
```

### Stop the stack
```bash
docker compose down                # stop containers
docker compose down -v             # stop + delete DB volume (full reset)
```

### Rebuild a single service
```bash
docker compose up --build backend
docker compose up --build frontend
```

### View logs
```bash
docker compose logs -f             # all services
docker compose logs -f backend
docker compose logs -f frontend
```

### Reset the database
```bash
docker compose down -v
docker compose up --build
```

---

## How to Test

All tests run **inside Docker containers**. Do not run pytest or vitest on the host.

### Backend Tests (pytest)
```bash
# Run all backend tests
docker compose exec backend pytest

# Run with verbose output
docker compose exec backend pytest -v

# Run a specific test file
docker compose exec backend pytest tests/test_cities.py

# Run a specific test
docker compose exec backend pytest tests/test_cities.py::test_add_city

# Run with coverage
docker compose exec backend pytest --cov=app --cov-report=term-missing
```

Backend test files live in `backend/tests/`:
```
backend/tests/
├── conftest.py          # pytest fixtures: test DB session, FastAPI TestClient
├── test_health.py       # GET /health
├── test_cities.py       # GET/POST/DELETE /api/cities
├── test_weather.py      # GET /api/weather/{lat}/{lon} (mocked httpx)
├── test_geocode.py      # GET /api/geocode (mocked httpx)
└── test_weather_codes.py # WMO code utility unit tests
```

### Frontend Tests (Vitest + React Testing Library)
```bash
# Run all frontend tests
docker compose exec frontend npx vitest run

# Run in watch mode (for development inside container)
docker compose exec frontend npx vitest

# Run a specific test file
docker compose exec frontend npx vitest run src/tests/components/WeatherCard.test.tsx

# Run with coverage
docker compose exec frontend npx vitest run --coverage
```

Frontend test files live in `frontend/src/tests/`:
```
frontend/src/tests/
├── api/
│   └── client.test.ts
├── components/
│   ├── WeatherCard.test.tsx
│   ├── CityTreeItem.test.tsx
│   ├── SearchInput.test.tsx
│   └── EmptyState.test.tsx
└── hooks/
    ├── useGeocodeSearch.test.ts
    └── useWeatherRefresh.test.ts
```

---

## Project Structure

```
weather-dashboard/
├── docker-compose.yml        # Orchestrates frontend, backend, db
├── render.yaml               # Render.com deployment config
├── README.md
│
├── backend/
│   ├── Dockerfile            # python:3.12-slim, single-stage, non-root user
│   ├── requirements.txt
│   └── app/
│       ├── main.py           # FastAPI app factory, CORS, startup hook
│       ├── models.py         # SQLAlchemy ORM models
│       ├── database.py       # Engine, SessionLocal, Base, get_db dep
│       ├── schemas.py        # Pydantic v2 schemas (request + response)
│       ├── routers/
│       │   ├── cities.py     # /api/cities routes
│       │   ├── weather.py    # /api/weather routes
│       │   └── geocode.py    # /api/geocode routes
│       └── utils/
│           └── weather_codes.py
│
└── frontend/
    ├── Dockerfile            # node:20-alpine, single-stage
    ├── package.json
    ├── tsconfig.json
    ├── vite.config.ts
    ├── tailwind.config.ts
    ├── index.html
    └── src/
        ├── main.tsx
        ├── App.tsx
        ├── api/client.ts     # All fetch calls to backend
        ├── context/
        │   └── AppContext.tsx # useReducer global state
        ├── hooks/            # Custom React hooks
        ├── components/
        │   ├── Layout.tsx
        │   ├── Sidebar/      # City tree, search, context menu
        │   └── MainPanel/    # Weather cards, grid, skeletons
        └── tests/            # Vitest + RTL test files
```

---

## Key Conventions

### General
- **No host dependencies.** All commands (install, test, lint, build) run inside Docker via `docker compose exec`.
- **Single-stage Dockerfiles only.** No multi-stage builds.
- **Non-root user in backend container.** The backend Dockerfile creates and switches to `appuser`.
- **Volume mounts for hot reload.** `./backend:/app` and `./frontend:/app` mounts enable live reload during development without rebuilding images.

### Backend Conventions

#### File Organization
- One router file per resource group (`cities.py`, `weather.py`, `geocode.py`).
- All Pydantic schemas (request + response) live in `schemas.py`.
- All SQLAlchemy models live in `models.py`.
- Database session management via FastAPI's `Depends(get_db)` dependency injection.

#### HTTP & Error Handling
- Use FastAPI's `HTTPException` for all error responses; never return raw error strings.
- `POST /api/cities` returns `201` on create, `200` on duplicate (idempotent).
- `DELETE /api/cities/{id}` returns `204 No Content` on success, `404` if not found.
- Upstream Open-Meteo failures raise `502 Bad Gateway`.
- All external HTTP calls to Open-Meteo use `httpx.AsyncClient` (async, timeout=10s).

#### Database
- Tables created at startup via `Base.metadata.create_all()`. No Alembic for this project.
- `DATABASE_URL` is always read from the environment variable — never hardcoded.
- Use `ROUND(latitude::numeric, 2)` uniqueness index to silently reject duplicates.

#### Testing
- Use `pytest-asyncio` for async route tests.
- Use `httpx.MockTransport` or `respx` to mock all Open-Meteo calls — tests must never hit the real external API.
- Test DB uses an in-memory SQLite database via `override_get_db` fixture in `conftest.py`.
- Every router must have at least: happy-path test, not-found test, and validation-error test.

#### Python Style
- Type-annotate all function signatures.
- Use Pydantic v2 model syntax (`model_config`, `model_validator`, etc.).
- No `print()` in application code — use Python `logging`.

### Frontend Conventions

#### State Management
- All global state lives in `AppContext` (React Context + `useReducer`). No Redux, Zustand, or other libraries.
- Weather data is keyed by `city.id` in a `Record<number, WeatherData>` map.
- Local UI state (dropdown open, context menu position) stays local in the relevant component.

#### API Calls
- All `fetch` calls go through `src/api/client.ts`. No inline fetch in components.
- `VITE_API_URL` from `import.meta.env` is the base URL — never hardcode `localhost`.

#### Components
- One component per file; filename matches the exported component name (PascalCase).
- Props interfaces are defined in the same file as the component, above the component.
- No default exports with anonymous functions — always name the function: `export function WeatherCard(...)`.

#### Styling
- Tailwind CSS only — no custom CSS files, no CSS-in-JS, no inline `style` props (except for dynamic animation values).
- Responsive classes follow mobile-first order: base → `sm:` → `md:` → `lg:`.
- Card grid: `grid-cols-1 sm:grid-cols-2 lg:grid-cols-3`.
- Animation classes: use Tailwind's `transition`, `duration-200`, `opacity`, `translate-y` utilities. Add/remove animation state via `useAnimatedList` hook.

#### Testing
- Use `@testing-library/react` + `@testing-library/user-event` for all component tests.
- Mock `src/api/client.ts` with `vi.mock('../api/client')` — tests never hit the real backend.
- Assert on accessible queries (`getByRole`, `getByLabelText`) over implementation details (`getByTestId`) where possible.
- Each component test file covers: renders correctly, user interactions, loading state, error/empty state.

#### TypeScript
- `strict: true` in `tsconfig.json` — no `any`, no `// @ts-ignore`.
- All API response shapes are typed in `src/api/client.ts` and imported where needed.
- Avoid type assertions (`as`) except when narrowing from `unknown` in catch blocks.

### Environment Variables
- **Backend:** Only `DATABASE_URL` is required. Read via `os.environ["DATABASE_URL"]` (raise on missing).
- **Frontend:** Only `VITE_API_URL` is required. Falls back to `http://localhost:8000` in dev for convenience.
- Never commit `.env` files. Use `docker-compose.yml` for local dev values.

### Git Conventions
- Branch naming: `milestone/{number}-short-description`
- Commit messages: conventional commits — `feat:`, `fix:`, `test:`, `chore:`, `docs:`
- Each milestone should be a pull request targeting `main`.

---

## Backend `requirements.txt`

```
fastapi==0.111.0
uvicorn[standard]==0.30.1
sqlalchemy==2.0.30
psycopg2-binary==2.9.9
httpx==0.27.0
pydantic==2.7.1

# Testing
pytest==8.2.0
pytest-asyncio==0.23.7
httpx==0.27.0
respx==0.21.1
pytest-cov==5.0.0
```

## Frontend `package.json` (key deps)

```json
{
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0"
  },
  "devDependencies": {
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.0",
    "typescript": "^5.4.0",
    "vite": "^5.3.0",
    "tailwindcss": "^3.4.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0",
    "vitest": "^1.6.0",
    "@vitest/coverage-v8": "^1.6.0",
    "@testing-library/react": "^16.0.0",
    "@testing-library/user-event": "^14.5.0",
    "@testing-library/jest-dom": "^6.4.0",
    "jsdom": "^24.1.0"
  }
}
```

---

## Common Pitfalls & Troubleshooting

| Problem | Solution |
|---|---|
| `backend` exits immediately on start | Check DB health — backend `depends_on` db with `service_healthy`. Run `docker compose logs db`. |
| Frontend can't reach backend | Ensure `VITE_API_URL=http://localhost:8000` in `docker-compose.yml`. In-browser calls go to `localhost`, not the Docker service name. |
| `relation "cities" does not exist` | The DB volume may have stale data without the schema. Run `docker compose down -v && docker compose up --build`. |
| Hot reload not working | Ensure volume mounts are present in `docker-compose.yml`. The `node_modules` exclusion volume (`/app/node_modules`) prevents the host from overwriting container deps. |
| pytest can't find `app` module | Ensure `PYTHONPATH` is set or tests are run from `/app` inside the container: `docker compose exec backend pytest`. |
| Vitest can't find modules | Run `docker compose exec frontend npx vitest run` — not `npm test` — to use the correct config. |
| Open-Meteo returns 429 | Free tier; add a 1-second delay between bulk weather fetches on page load. |
