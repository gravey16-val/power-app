# CLAUDE.md — Weather Dashboard: Real-time City Weather Tracker

---

## How to Run

### Prerequisites
- Docker Desktop (or Docker Engine + Docker Compose v2) installed
- No other host-OS dependencies — everything runs inside containers

### Start the full stack
```bash
# From the repo root:
docker compose up --build
```

Services started:
| Service    | URL                        | Notes                          |
|------------|----------------------------|--------------------------------|
| Frontend   | http://localhost:5173       | Vite dev server (hot reload)   |
| Backend    | http://localhost:8000       | FastAPI + Uvicorn              |
| Docs (API) | http://localhost:8000/docs  | Swagger UI (auto-generated)    |
| Database   | localhost:5432              | PostgreSQL 16 (internal only)  |

### Stop the stack
```bash
docker compose down          # stop containers, keep volumes
docker compose down -v       # stop containers, destroy DB volume
```

### Rebuild after dependency changes
```bash
# Backend (new pip packages):
docker compose build backend

# Frontend (new npm packages):
docker compose build frontend
```

---

## How to Test

All tests run **inside Docker containers**. Do not run pytest or vitest on your host machine.

### Backend tests (pytest)
```bash
# Run all backend tests:
docker compose exec backend pytest

# Run with verbose output:
docker compose exec backend pytest -v

# Run a specific test file:
docker compose exec backend pytest tests/test_cities.py -v

# Run a specific test by name:
docker compose exec backend pytest tests/test_weather.py::test_get_weather_success -v

# Run with coverage report:
docker compose exec backend pytest --cov=app --cov-report=term-missing
```

### Frontend tests (Vitest + React Testing Library)
```bash
# Run all frontend tests:
docker compose exec frontend npx vitest run

# Run with verbose output:
docker compose exec frontend npx vitest run --reporter=verbose

# Run a specific test file:
docker compose exec frontend npx vitest run src/components/WeatherCard.test.tsx

# Run tests matching a pattern:
docker compose exec frontend npx vitest run --reporter=verbose -t "renders city name"

# Run in watch mode (interactive, dev only):
docker compose exec frontend npx vitest
```

> **Note:** The stack must be running (`docker compose up --build`) before executing `exec` commands.

---

## Project Structure

```
weather-dashboard/
├── docker-compose.yml              # Orchestrates all three services
├── .env                            # Local secrets (gitignored)
├── .env.example                    # Committed template for .env
├── render.yaml                     # Render deployment manifest
├── README.md
├── ARCHITECTURE.md
├── CLAUDE.md
│
├── backend/
│   ├── Dockerfile                  # Single-stage, python:3.12-slim, non-root user
│   ├── requirements.txt            # pip dependencies
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app factory, CORS, lifespan, router mount
│   │   ├── database.py             # SQLAlchemy engine, SessionLocal, Base, get_db()
│   │   ├── models.py               # City ORM model
│   │   ├── schemas.py              # Pydantic request/response schemas
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── cities.py           # /api/cities CRUD endpoints
│   │   │   ├── weather.py          # /api/weather/{lat}/{lon} endpoint
│   │   │   └── geocode.py          # /api/geocode endpoint
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── weather_service.py  # Open-Meteo weather fetch + WMO code mapping
│   │       └── geocode_service.py  # Open-Meteo geocoding fetch
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py             # pytest fixtures: test DB, TestClient, override get_db
│       ├── test_health.py          # GET /health
│       ├── test_cities.py          # CRUD city endpoints
│       ├── test_weather.py         # Weather endpoint (mocked httpx calls)
│       └── test_geocode.py         # Geocode endpoint (mocked httpx calls)
│
└── frontend/
    ├── Dockerfile                  # Single-stage, node:20-alpine, Vite dev server
    ├── package.json
    ├── package-lock.json
    ├── vite.config.ts              # Vite config; proxy /api → backend:8000
    ├── tailwind.config.ts          # Tailwind config
    ├── tsconfig.json
    ├── index.html
    └── src/
        ├── main.tsx                # React 18 createRoot entry
        ├── App.tsx                 # AppProvider + Layout mount
        ├── types/
        │   └── index.ts            # City, WeatherData, GeocodeResult interfaces
        ├── api/
        │   └── client.ts           # fetch wrapper; base URL from VITE_API_URL
        ├── context/
        │   └── AppContext.tsx      # Cities state, addCity/removeCity actions
        ├── hooks/
        │   ├── useCities.ts        # Load cities on mount, expose add/remove
        │   ├── useWeather.ts       # Fetch weather; setInterval 60s auto-refresh
        │   ├── useGeocode.ts       # Debounced geocode search (300ms)
        │   └── useContextMenu.ts   # Right-click menu position + open/close state
        ├── components/
        │   ├── Layout/
        │   │   ├── Layout.tsx
        │   │   └── Layout.test.tsx
        │   ├── Sidebar/
        │   │   ├── Sidebar.tsx
        │   │   ├── Sidebar.test.tsx
        │   │   ├── AddCityButton.tsx
        │   │   ├── CitySearch.tsx
        │   │   ├── CitySearch.test.tsx
        │   │   ├── CitySearchResult.tsx
        │   │   ├── CityTreeView.tsx
        │   │   ├── CityTreeView.test.tsx
        │   │   ├── CityTreeItem.tsx
        │   │   ├── CityTreeItem.test.tsx
        │   │   ├── ContextMenu.tsx
        │   │   ├── ContextMenu.test.tsx
        │   │   └── EmptyState.tsx
        │   ├── WeatherCard/
        │   │   ├── WeatherCard.tsx
        │   │   ├── WeatherCard.test.tsx
        │   │   ├── WeatherCardSkeleton.tsx
        │   │   ├── CardHeader.tsx
        │   │   ├── WeatherIcon.tsx
        │   │   ├── TemperatureDisplay.tsx
        │   │   ├── WeatherDetails.tsx
        │   │   └── LastUpdated.tsx
        │   └── MainGrid/
        │       ├── MainGrid.tsx
        │       ├── MainGrid.test.tsx
        │       ├── WeatherCardGrid.tsx
        │       └── EmptyGridState.tsx
        └── test/
            └── setup.ts            # Vitest + RTL setup (extend matchers, etc.)
```

---

## Key Conventions

### General
- **No host dependencies.** All commands (`pytest`, `npx vitest`, `pip install`, etc.) run inside containers via `docker compose exec`.
- **Single-stage Dockerfiles only.** No multi-stage builds.
- **`.env` file** at repo root supplies secrets locally. Never commit it. Use `.env.example` as the template.
- **Ports:** Frontend `5173`, Backend `8000`, PostgreSQL `5432`.

---

### Backend Conventions

#### File layout
- `app/main.py` — creates the FastAPI app, registers CORS middleware, mounts all routers, and runs `Base.metadata.create_all()` in the `lifespan` startup handler.
- `app/database.py` — single source of truth for `DATABASE_URL`, SQLAlchemy `engine`, `SessionLocal`, `Base`, and the `get_db()` dependency.
- `app/models.py` — SQLAlchemy ORM models only (no business logic).
- `app/schemas.py` — Pydantic v2 models for request bodies and response shapes.
- `app/routers/` — one file per router; each file uses `APIRouter(prefix=..., tags=...)`.
- `app/services/` — all outbound HTTP calls to Open-Meteo live here; routers call services, not `httpx` directly.

#### Coding rules
- Use `httpx` (async-capable) for all outbound HTTP calls to Open-Meteo.
- Use `get_db()` as a FastAPI `Depends()` for all database sessions — never instantiate `SessionLocal` directly in a router.
- Return `HTTP 409` is **not** used for duplicates — `POST /api/cities` silently returns the existing city with `200 OK`.
- Return `HTTP 404` with `{"detail": "City not found"}` for `DELETE /api/cities/{id}` when the ID doesn't exist.
- Return `HTTP 502` with a descriptive `detail` when upstream Open-Meteo calls fail.
- All response models must be declared on route decorators (`response_model=...`) for automatic OpenAPI docs.
- WMO weather code→condition→emoji mapping lives in `app/services/weather_service.py` as a plain dict constant.

#### Dependency versions (requirements.txt must include at minimum)
```
fastapi
uvicorn[standard]
sqlalchemy
psycopg2-binary
httpx
pydantic
pytest
pytest-cov
httpx          # also used as AsyncClient in tests
```

#### Testing rules
- `tests/conftest.py` creates an **in-memory SQLite** test database and overrides the `get_db` dependency so tests never touch the real PostgreSQL container.
- All Open-Meteo outbound calls are mocked with `unittest.mock.patch` or `respx` — tests must not make real network requests.
- Every router file has a corresponding test file.

---

### Frontend Conventions

#### Coding rules
- All API calls go through `src/api/client.ts`. No component or hook calls `fetch`/`axios` directly.
- `VITE_API_URL` is the only environment variable the frontend reads. In development, Vite proxies `/api/*` to the backend, so `client.ts` prefixes all paths with `/api/`.
- Global cities state lives in `AppContext`. Local UI state (search input, dropdown open, context menu) lives in component state or custom hooks.
- Custom hooks (`useCities`, `useWeather`, `useGeocode`, `useContextMenu`) contain all side-effect logic. Components are purely presentational.
- `useWeather` sets up a `setInterval` (60 000 ms) to refetch weather for its city on mount and clears it on unmount via the `useEffect` cleanup.
- `useGeocode` uses `setTimeout`/`clearTimeout` for 300 ms debounce — not a library.
- Animations use Tailwind CSS transition utilities (`transition`, `duration-200`, `opacity-0`, `translate-y-2`, etc.). No animation library.
- `WeatherCard` and `CityTreeItem` both accept an `onRemove` callback prop — they do not call the API directly.

#### TypeScript rules
- `strict: true` in `tsconfig.json`. No `any` types — use `unknown` and narrow.
- All API response shapes are typed via interfaces in `src/types/index.ts` and must match the backend Pydantic schemas exactly.
- Props interfaces are defined inline (co-located) in each component file unless shared across multiple components.

#### Tailwind rules
- Use Tailwind utility classes exclusively — no custom CSS files except `src/index.css` for the `@tailwind` directives.
- Responsive grid: `grid-cols-1 sm:grid-cols-2 lg:grid-cols-3` on `WeatherCardGrid`.
- Dark mode is not required — design for light mode only.

#### Testing rules
- Every component in `src/components/` has a co-located `.test.tsx` file.
- Tests use React Testing Library's `render`, `screen`, `userEvent` — no Enzyme, no shallow rendering.
- Mock API calls with `vi.mock('../../api/client')` or `vi.fn()` — tests must not make real HTTP requests.
- Use `vi.useFakeTimers()` in `useWeather` tests to control the 60-second interval without waiting.
- `src/test/setup.ts` is referenced in `vite.config.ts` as `test.setupFiles` and imports `@testing-library/jest-dom/vitest`.

#### `vite.config.ts` essentials
```ts
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',   // required for Docker
    port: 5173,
    proxy: {
      '/api': 'http://backend:8000',   // Docker service name, not localhost
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
  },
});
```

> **Important:** The Vite proxy uses `http://backend:8000` (Docker service name), not `http://localhost:8000`. This works because both `frontend` and `backend` are on the same Docker Compose network.

---

### Git Conventions
- Branch naming: `milestone/<number>-<short-slug>` (e.g. `milestone/1-scaffold`)
- Commit messages: `feat:`, `fix:`, `test:`, `chore:`, `docs:` prefixes (Conventional Commits)
- Never commit `.env`, `__pycache__/`, `node_modules/`, `.venv/`

---

### Render Deployment

#### `render.yaml` defines three services:
1. **`weather-backend`** — Web Service, Docker runtime, `backend/` dir, env var `DATABASE_URL` (from Render Postgres), `ALLOWED_ORIGINS` set to the frontend URL.
2. **`weather-frontend`** — Web Service, Docker runtime, `frontend/` dir, env var `VITE_API_URL` set to the backend service URL. CMD overridden to `npx vite preview --host 0.0.0.0 --port 10000` (Render expects port 10000).
3. **`weather-db`** — Render managed PostgreSQL (or referenced as an existing DB).

#### Production notes
- Backend `CMD` in Dockerfile does **not** include `--reload` (already correct).
- Backend runs as non-root user `appuser` (already correct in Dockerfile).
- `DATABASE_URL` is injected by Render at runtime — not hardcoded anywhere.
- Frontend reads `VITE_API_URL` as a build arg on Render: set it to the backend's public URL before the first deploy.
