# CLAUDE.md — Weather Dashboard: Real-time City Weather Tracker

## How to Run

### Start the full stack (first time or after changes)
```bash
docker compose up --build
```

### Start without rebuilding
```bash
docker compose up
```

### Stop all services
```bash
docker compose down
```

### Stop and remove volumes (wipe the database)
```bash
docker compose down -v
```

### Access the running services
| Service  | URL                        |
|----------|----------------------------|
| Frontend | http://localhost:5173       |
| Backend  | http://localhost:8000       |
| API Docs | http://localhost:8000/docs  |
| DB       | localhost:5432              |

---

## How to Test

> ⚠️ All tests run **inside Docker containers**. Do not run `pytest` or `vitest` on the host machine.

### Backend tests (pytest)
```bash
docker compose exec backend pytest
```

With verbosity and coverage:
```bash
docker compose exec backend pytest -v --tb=short
```

Run a single test file:
```bash
docker compose exec backend pytest tests/test_cities.py -v
```

### Frontend tests (Vitest + React Testing Library)
```bash
docker compose exec frontend npx vitest run
```

With verbose output:
```bash
docker compose exec frontend npx vitest run --reporter=verbose
```

Run a single test file:
```bash
docker compose exec frontend npx vitest run src/api/client.test.ts
```

Watch mode (for development inside the container):
```bash
docker compose exec frontend npx vitest
```

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
│   ├── Dockerfile                # Single-stage, python:3.12-slim, non-root user
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py               # FastAPI app, lifespan startup, router mounts
│   │   ├── database.py           # SQLAlchemy engine + SessionLocal + Base
│   │   ├── models.py             # City ORM model
│   │   ├── schemas.py            # Pydantic v2 schemas (CityCreate, CityResponse, etc.)
│   │   ├── routers/
│   │   │   ├── cities.py         # /api/cities CRUD
│   │   │   ├── weather.py        # /api/weather/{lat}/{lon}
│   │   │   └── geocode.py        # /api/geocode
│   │   └── services/
│   │       ├── weather.py        # Open-Meteo fetch + WMO code → condition mapping
│   │       └── geocode.py        # Open-Meteo Geocoding fetch
│   └── tests/
│       ├── conftest.py           # Fixtures: in-memory SQLite test DB, TestClient
│       ├── test_health.py
│       ├── test_cities.py
│       ├── test_weather.py
│       └── test_geocode.py
│
└── frontend/
    ├── Dockerfile                # Single-stage, node:20-alpine, Vite dev server
    ├── package.json
    ├── package-lock.json
    ├── vite.config.ts            # Proxy /api → backend:8000 in dev
    ├── tailwind.config.ts
    ├── tsconfig.json
    ├── index.html
    └── src/
        ├── main.tsx
        ├── App.tsx
        ├── context/
        │   └── AppContext.tsx     # cities[], weatherMap, dispatch actions
        ├── api/
        │   └── client.ts         # Typed fetch wrappers for all 6 endpoints
        ├── hooks/
        │   ├── useCities.ts      # load, add, remove city
        │   ├── useWeather.ts     # fetch weather + 60s auto-refresh via setInterval
        │   └── useGeocode.ts     # debounced (300ms) geocode search
        ├── components/
        │   ├── layout/
        │   │   ├── Layout.tsx
        │   │   ├── Sidebar.tsx
        │   │   └── MainContent.tsx
        │   ├── sidebar/
        │   │   ├── AddCityButton.tsx
        │   │   ├── CitySearch.tsx
        │   │   ├── SearchInput.tsx
        │   │   ├── SearchDropdown.tsx
        │   │   ├── SearchResultItem.tsx
        │   │   ├── CityTreeView.tsx
        │   │   ├── CityTreeItem.tsx
        │   │   ├── ContextMenu.tsx
        │   │   └── EmptyState.tsx
        │   └── weather/
        │       ├── WeatherCardGrid.tsx
        │       ├── WeatherCard.tsx
        │       ├── WeatherCardSkeleton.tsx
        │       ├── CardHeader.tsx
        │       ├── TempDisplay.tsx
        │       ├── ConditionDisplay.tsx
        │       ├── WeatherStats.tsx
        │       └── LastUpdated.tsx
        ├── types/
        │   └── index.ts           # City, WeatherData, GeoResult, AppState types
        └── utils/
            └── weatherConditions.ts  # WMO code → { condition, emoji } lookup table
```

---

## Key Conventions

### General
- **No host OS dependencies** — every command runs inside a Docker container.
- **Single-stage Dockerfiles only** — no multi-stage builds.
- The backend non-root user (`appuser`) is created in the Dockerfile for security.
- The database schema is created automatically at backend startup via `Base.metadata.create_all(bind=engine)` — no manual migration step needed for development.

### Backend (Python / FastAPI)

- **Python version:** 3.12 (matches `python:3.12-slim` base image).
- **Framework:** FastAPI with Pydantic v2 schemas.
- **ORM:** SQLAlchemy 2.x with synchronous sessions (no async ORM).
- **Dependency injection:** Database sessions provided via `Depends(get_db)` in all routers.
- **Router prefix:** All feature routers are mounted under `/api` prefix in `main.py`.
- **External HTTP calls:** Use `httpx` (sync client) inside services for Open-Meteo API calls.
- **Error handling:** Return `HTTPException` with appropriate status codes (404, 400, 502).
- **Duplicate city guard:** `POST /api/cities` catches `IntegrityError` on the unique constraint and returns the existing row with `200 OK` instead of `201 Created`.
- **Environment:** `DATABASE_URL` is read from `os.environ` (never hardcoded).
- **Test database:** `conftest.py` overrides `get_db` dependency with an in-memory SQLite session so tests never touch PostgreSQL.
- **WMO weather codes:** Mapped to human-readable conditions and emoji in `utils/weatherConditions.py` (shared logic between weather service and response schema).

### Frontend (React / TypeScript / Vite)

- **TypeScript strict mode** is enabled in `tsconfig.json`.
- **API base URL:** Always read from `import.meta.env.VITE_API_URL` — never hardcoded.
- **Vite dev proxy:** `vite.config.ts` proxies `/api` → `http://backend:8000` so the frontend container can reach the backend container by Docker service name.
- **Global state:** Managed via a single React Context (`AppContext`) with `useReducer`. No external state library.
- **Auto-refresh:** `useWeather` hook sets up a `setInterval` (60 000 ms) that re-fetches weather for all cities in parallel using `Promise.all`. Interval is cleared on unmount.
- **Debounce:** `useGeocode` hook debounces the geocoding API call by 300 ms using `setTimeout`/`clearTimeout`. The API is called only when input is ≥ 3 characters.
- **Duplicate guard (frontend):** Before calling `POST /api/cities`, check if a city with the same `latitude`/`longitude` already exists in local state and silently skip.
- **Animations:**
  - Card enter: Tailwind CSS classes `opacity-0 translate-y-2` → `opacity-100 translate-y-0` with `transition-all duration-300`.
  - Card exit: `opacity-100` → `opacity-0 -translate-y-2` with `transition-all duration-200`, then remove from DOM.
- **Context menu:** Rendered via a fixed-position `div` on `contextmenu` event; dismissed on `click` or `Escape` anywhere in document.
- **Styling:** Tailwind CSS utility classes only — no custom CSS files except `index.css` (Tailwind directives + base reset).
- **Component naming:** PascalCase for components, camelCase for hooks (`useCities`, `useWeather`), camelCase for utility functions.
- **Test files:** Co-located with source files using the `*.test.ts` / `*.test.tsx` naming convention.
- **Vitest config:** In `vite.config.ts` under the `test` key; uses `jsdom` environment and `@testing-library/jest-dom` setup file.

### API Client (`src/api/client.ts`)

All backend calls are centralized here as typed async functions:

```typescript
// Example shapes
getCities(): Promise<City[]>
addCity(payload: CityCreate): Promise<City>
deleteCity(id: number): Promise<void>
getWeather(lat: number, lon: number): Promise<WeatherData>
geocode(query: string): Promise<GeoResult[]>
```

Throws a typed `ApiError` (with `status` and `message`) on non-2xx responses so callers can handle errors uniformly.

### Milestone Checklist (for tracking progress)

| # | Milestone                                      | Key Deliverables                                                       |
|---|------------------------------------------------|------------------------------------------------------------------------|
| 1 | Infrastructure & Project Scaffold              | `docker compose up --build` green, `/health` responds, DB schema up    |
| 2 | Backend API — All Endpoints Implemented        | All 6 endpoints pass pytest inside container                           |
| 3 | Frontend Shell — Layout & API Integration      | Two-panel layout renders, API client layer tested with Vitest          |
| 4 | City Tree View — Sidebar Add & Remove          | Typeahead search, tree view with flags + temps, right-click remove     |
| 5 | Weather Cards — Full Data & Interactions       | All data fields, skeletons, animations, × remove button                |
| 6 | Polish, Persistence & Deployment Readiness     | Persists on refresh, Render deploy works, full test suite green        |

### Common Development Commands

```bash
# Rebuild only the backend after Python changes
docker compose up --build backend

# Rebuild only the frontend after dependency changes
docker compose up --build frontend

# Tail logs from all services
docker compose logs -f

# Tail logs from backend only
docker compose logs -f backend

# Open a shell in the backend container
docker compose exec backend bash

# Open a shell in the frontend container
docker compose exec frontend sh

# Run a one-off database query
docker compose exec db psql -U weather -d weatherdb -c "SELECT * FROM cities;"

# Install a new Python dependency (then rebuild)
docker compose exec backend pip install <package>
# → add to requirements.txt, then: docker compose up --build backend

# Install a new npm dependency (then rebuild)
docker compose exec frontend npm install <package>
# → package.json is updated; docker compose up --build frontend to persist
```
