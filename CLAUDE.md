# CLAUDE.md — Weather Dashboard: Real-time City Weather Tracker

## How to Run

### Prerequisites
- Docker Desktop (or Docker Engine + Docker Compose plugin) installed.
- No other host dependencies required — everything runs in containers.

### Start the full stack

```bash
docker compose up --build
```

This starts three services:
| Service | URL | Notes |
|---|---|---|
| `frontend` | http://localhost:5173 | Vite dev server (React app) |
| `backend` | http://localhost:8000 | FastAPI + Uvicorn |
| `db` | localhost:5432 | PostgreSQL 16 |

The backend waits for the `db` health check to pass before starting. Tables are created automatically on first backend startup via SQLAlchemy `create_all`.

### Stop the stack

```bash
docker compose down          # stop containers, keep volumes
docker compose down -v       # stop containers AND delete the DB volume
```

### Rebuild after dependency changes

```bash
docker compose up --build    # always rebuilds images
```

---

## How to Test

All tests run **inside Docker containers**. Do not run pytest or Vitest on the host.

### Backend tests (pytest)

```bash
docker compose exec backend pytest
```

Run with verbose output:
```bash
docker compose exec backend pytest -v
```

Run a specific test file:
```bash
docker compose exec backend pytest tests/test_cities.py -v
```

Run with coverage:
```bash
docker compose exec backend pytest --cov=app --cov-report=term-missing
```

### Frontend tests (Vitest + React Testing Library)

```bash
docker compose exec frontend npx vitest run
```

Run with verbose reporter:
```bash
docker compose exec frontend npx vitest run --reporter=verbose
```

Run a specific test file:
```bash
docker compose exec frontend npx vitest run src/components/weather/WeatherCard.test.tsx
```

> **Note:** The stack must be running (`docker compose up --build`) before executing `exec` commands.

---

## Project Structure

```
weather-dashboard/
├── docker-compose.yml
├── render.yaml
├── README.md
├── ARCHITECTURE.md
├── CLAUDE.md
│
├── backend/
│   ├── Dockerfile                  # Single-stage, python:3.12-slim, non-root user
│   ├── requirements.txt
│   ├── pytest.ini                  # testpaths = tests, asyncio_mode = auto
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app, CORS, router inclusion, lifespan (create_all)
│   │   ├── database.py             # SQLAlchemy engine + SessionLocal + Base
│   │   ├── models.py               # City ORM model
│   │   ├── schemas.py              # Pydantic request/response schemas
│   │   ├── dependencies.py         # get_db() dependency
│   │   └── routers/
│   │       ├── __init__.py
│   │       ├── cities.py           # GET/POST /api/cities, DELETE /api/cities/{id}
│   │       ├── weather.py          # GET /api/weather/{latitude}/{longitude}
│   │       └── geocode.py          # GET /api/geocode?q=
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py             # TestClient, in-memory SQLite override, fixtures
│       ├── test_health.py          # GET /health
│       ├── test_cities.py          # CRUD city endpoints
│       ├── test_weather.py         # Weather endpoint (mocked httpx calls)
│       └── test_geocode.py         # Geocode endpoint (mocked httpx calls)
│
└── frontend/
    ├── Dockerfile                  # Single-stage, node:20-alpine, npm ci + dev server
    ├── package.json
    ├── package-lock.json
    ├── vite.config.ts              # Vitest config embedded here
    ├── tailwind.config.ts
    ├── tsconfig.json
    ├── index.html
    └── src/
        ├── main.tsx
        ├── App.tsx
        ├── api/
        │   └── client.ts
        ├── types/
        │   └── index.ts
        ├── hooks/
        │   ├── useCities.ts
        │   ├── useWeather.ts
        │   └── useGeocode.ts
        ├── components/
        │   ├── layout/
        │   │   ├── AppLayout.tsx
        │   │   ├── Sidebar.tsx
        │   │   └── MainContent.tsx
        │   ├── sidebar/
        │   │   ├── CityTree.tsx
        │   │   ├── CityTreeItem.tsx
        │   │   ├── ContextMenu.tsx
        │   │   ├── AddCityButton.tsx
        │   │   └── AddCityFlow.tsx
        │   ├── geocode/
        │   │   └── GeoSearchDropdown.tsx
        │   ├── weather/
        │   │   ├── WeatherCard.tsx
        │   │   ├── WeatherCard.test.tsx
        │   │   ├── WeatherCardGrid.tsx
        │   │   ├── WeatherCardSkeleton.tsx
        │   │   └── WeatherIcon.tsx
        │   └── common/
        │       ├── EmptyState.tsx
        │       └── ErrorBanner.tsx
        ├── styles/
        │   └── index.css
        └── test/
            ├── setup.ts                    # @testing-library/jest-dom setup
            ├── App.test.tsx
            ├── hooks/
            │   ├── useCities.test.ts
            │   ├── useWeather.test.ts
            │   └── useGeocode.test.ts
            └── components/
                ├── sidebar/
                │   ├── CityTree.test.tsx
                │   ├── CityTreeItem.test.tsx
                │   └── AddCityFlow.test.tsx
                └── weather/
                    ├── WeatherCard.test.tsx
                    └── WeatherCardGrid.test.tsx
```

---

## Key Conventions

### General
- **Single-stage Dockerfiles only.** No multi-stage builds anywhere.
- **Nothing runs on the host OS.** All dev, test, and build commands go through `docker compose exec`.
- **No API key required.** Open-Meteo (weather + geocoding) is free and keyless.

### Backend (Python / FastAPI)

#### Code Style
- Python 3.12; type hints on all function signatures.
- Pydantic v2 schemas in `schemas.py` — separate `CityCreate`, `CityRead` schemas.
- One router file per resource group (`cities.py`, `weather.py`, `geocode.py`).
- External HTTP calls use `httpx` (async) with a timeout of 10 seconds.
- All router functions are `async def`.

#### Database
- SQLAlchemy 2.x with `DeclarativeBase`.
- `DATABASE_URL` always read from `os.environ` — never hardcoded.
- Tables created via `Base.metadata.create_all(bind=engine)` in FastAPI `lifespan` handler.
- Duplicate city guard: catch `IntegrityError` on unique index violation → return existing record with `201`.

#### Error Handling
- `404` via `HTTPException(status_code=404, detail="City not found")`.
- `502` via `HTTPException(status_code=502, detail="Upstream API error")` when Open-Meteo is unreachable.
- `422` handled automatically by FastAPI/Pydantic validation.

#### Testing (pytest)
- Test database: **SQLite in-memory** (`:memory:`) — overrides `get_db` dependency via `app.dependency_overrides`.
- External HTTP calls mocked with `pytest-mock` / `unittest.mock.patch` — no real network calls in tests.
- `conftest.py` provides: `client` (TestClient), `db_session`, and pre-seeded `sample_city` fixtures.
- Every endpoint must have at least: happy-path test + relevant error case test.

#### `requirements.txt` (key packages)
```
fastapi>=0.111.0
uvicorn[standard]>=0.29.0
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.9
httpx>=0.27.0
pydantic>=2.7.0
pytest>=8.2.0
pytest-asyncio>=0.23.0
httpx>=0.27.0   # also used as AsyncClient in tests
pytest-mock>=3.14.0
coverage>=7.5.0
```

### Frontend (React / TypeScript / Vite)

#### Code Style
- Strict TypeScript (`"strict": true` in `tsconfig.json`).
- Functional components only — no class components.
- All shared types in `src/types/index.ts`; import from there, never re-declare inline.
- Custom hooks in `src/hooks/` — one hook per concern.
- Component files: `PascalCase.tsx`; hook files: `camelCase.ts`; test files: `ComponentName.test.tsx`.

#### API Client (`src/api/client.ts`)
- All `fetch` calls go through `client.ts` — no direct `fetch` in components or hooks.
- Base URL sourced from `import.meta.env.VITE_API_URL` with a fallback of `http://localhost:8000`.
- All functions are `async` and return typed results.
- Non-2xx responses throw an `Error` with the status code included in the message.

#### State Management
- **No Redux or Zustand.** Global city list lives in `App.tsx` state via `useCities` hook.
- `useCities` returns: `{ cities, loading, error, addCity, removeCity }`.
- `useWeather(lat, lon)` returns: `{ weather, loading, error }` — auto-refreshes via `setInterval` every 60 000 ms; clears interval on unmount.
- `useGeocode(query)` returns: `{ results, loading, error }` — debounced 300 ms, skips if query < 3 chars.

#### Styling (Tailwind CSS)
- Tailwind utility classes only — no custom CSS except in `src/styles/index.css` for the base layer directives.
- Responsive breakpoints: `sm` (≥640px), `md` (≥768px), `lg` (≥1024px), `xl` (≥1280px).
- Card grid: `grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4`.
- Sidebar width: fixed `w-72` on `lg+`, full-width collapsible on mobile.
- Animations: Tailwind `transition`, `duration-200`, `opacity`, `translate-y` utilities (no external animation library).

#### Animations
- **Card add:** `opacity-0 translate-y-4` → `opacity-100 translate-y-0` via `transition-all duration-300`.
- **Card remove:** `opacity-100 translate-y-0` → `opacity-0 translate-y-4` via `transition-all duration-200`, then `removeCity()` called after transition ends.

#### Testing (Vitest + React Testing Library)
- Vitest config in `vite.config.ts` under `test:` key (`environment: 'jsdom'`, `setupFiles: ['src/test/setup.ts']`).
- `src/test/setup.ts` imports `@testing-library/jest-dom/vitest`.
- All API calls mocked via `vi.mock('../../api/client')` — no real network calls.
- Use `@testing-library/user-event` for simulating user interactions (typing, clicking).
- Each component test file: renders component → asserts visible output → simulates interaction → asserts state change.
- Hooks tested via `renderHook` from `@testing-library/react`.

#### `package.json` (key dependencies)
```json
{
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "^6.4.0",
    "@testing-library/react": "^16.0.0",
    "@testing-library/user-event": "^14.5.0",
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.0",
    "autoprefixer": "^10.4.0",
    "jsdom": "^24.0.0",
    "postcss": "^8.4.0",
    "tailwindcss": "^3.4.0",
    "typescript": "^5.4.0",
    "vite": "^5.3.0",
    "vitest": "^1.6.0"
  }
}
```

---

## Milestone Checklist

| # | Milestone | Key Deliverables |
|---|---|---|
| 1 | Infrastructure & Scaffold | `docker compose up --build` green; `GET /health` returns `{"status":"ok"}`; pytest + vitest harnesses pass placeholder tests |
| 2 | Backend API | All 6 endpoints implemented + pytest coverage; Open-Meteo integrated; correct HTTP status codes |
| 3 | Frontend Shell | Two-panel layout renders; typed API client wired; loading + error states handled |
| 4 | City Tree View | Add city (typeahead), remove city (× and right-click), persistence across refresh |
| 5 | Weather Card Grid | Real Open-Meteo data; 60s auto-refresh; animate in/out; responsive grid |
| 6 | Polish & Deployment | All breakpoints verified; `render.yaml` committed; env vars documented; edge cases handled |

---

## Common Commands Reference

```bash
# Start everything
docker compose up --build

# Run backend tests
docker compose exec backend pytest

# Run frontend tests
docker compose exec frontend npx vitest run

# Open a backend shell
docker compose exec backend bash

# Open a frontend shell
docker compose exec frontend sh

# View backend logs
docker compose logs backend -f

# View all logs
docker compose logs -f

# Reset database (delete volume)
docker compose down -v && docker compose up --build

# Check running services
docker compose ps
```
