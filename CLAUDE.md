# CLAUDE.md — Weather Dashboard: Real-time City Weather Tracker

## How to Run

### Start the Full Stack
```bash
# Build all images and start all services (db, backend, frontend)
docker compose up --build

# Run in detached mode
docker compose up --build -d

# View logs for a specific service
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f db
```

Once running:
- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **API Docs (Swagger):** http://localhost:8000/docs
- **API Docs (ReDoc):** http://localhost:8000/redoc

### Stop the Stack
```bash
docker compose down

# Stop and remove volumes (wipes database)
docker compose down -v
```

### Rebuild a Single Service
```bash
docker compose up --build backend
docker compose up --build frontend
```

---

## How to Test

> All tests run **inside Docker containers**. No local Python or Node installation required.

### Backend Tests (pytest)
```bash
# Run all backend tests
docker compose exec backend pytest

# Run with verbose output
docker compose exec backend pytest -v

# Run a specific test file
docker compose exec backend pytest tests/test_cities.py -v

# Run a specific test function
docker compose exec backend pytest tests/test_weather.py::test_get_weather_success -v

# Run with coverage report
docker compose exec backend pytest --cov=app --cov-report=term-missing
```

### Frontend Tests (Vitest + React Testing Library)
```bash
# Run all frontend tests
docker compose exec frontend npx vitest run

# Run with verbose output
docker compose exec frontend npx vitest run --reporter=verbose

# Run a specific test file
docker compose exec frontend npx vitest run src/components/weather/WeatherCard.test.tsx

# Run tests matching a pattern
docker compose exec frontend npx vitest run --grep "CityTree"

# Run with coverage
docker compose exec frontend npx vitest run --coverage
```

### Run All Tests (Backend + Frontend)
```bash
# Both test suites sequentially
docker compose exec backend pytest && docker compose exec frontend npx vitest run
```

---

## Project Structure

```
weather-dashboard/
├── docker-compose.yml               # Orchestrates db, backend, frontend services
├── render.yaml                      # Render deployment configuration
├── README.md
├── ARCHITECTURE.md
├── CLAUDE.md
│
├── backend/
│   ├── Dockerfile                   # Single-stage, python:3.12-slim, non-root user
│   ├── requirements.txt             # FastAPI, uvicorn, sqlalchemy, psycopg2-binary, httpx, pytest, etc.
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                  # FastAPI app factory, CORS, router registration, startup event
│   │   ├── database.py              # SQLAlchemy engine, SessionLocal, Base, get_db dependency
│   │   ├── models.py                # City ORM model
│   │   ├── schemas.py               # Pydantic request/response schemas
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── cities.py            # GET/POST /api/cities, DELETE /api/cities/{id}
│   │   │   ├── weather.py           # GET /api/weather/{latitude}/{longitude}
│   │   │   └── geocode.py           # GET /api/geocode?q=
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── open_meteo.py        # HTTP client for Open-Meteo weather API
│   │       └── geocoding.py         # HTTP client for Open-Meteo Geocoding API
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py              # pytest fixtures: test DB, test client, sample data
│       ├── test_health.py           # GET /health
│       ├── test_cities.py           # CRUD city endpoints
│       ├── test_weather.py          # Weather endpoint (httpx mock)
│       └── test_geocode.py          # Geocode endpoint (httpx mock)
│
└── frontend/
    ├── Dockerfile                   # Single-stage, node:20-alpine, vite dev server
    ├── package.json                 # React 18, TypeScript 5, Tailwind, Vite, Vitest, RTL
    ├── vite.config.ts               # Vite config: proxy /api → backend, test config
    ├── tailwind.config.ts           # Tailwind content paths, custom theme extensions
    ├── tsconfig.json                # TypeScript strict mode config
    ├── index.html                   # HTML entry point
    └── src/
        ├── main.tsx                 # createRoot entry point
        ├── App.tsx                  # Root layout: <Sidebar> + <MainContent>
        ├── types/
        │   └── index.ts             # City, GeocodingResult, WeatherData, WeatherCardState
        ├── api/
        │   └── client.ts            # Base fetch/axios client using VITE_API_URL
        ├── hooks/
        │   ├── useCities.ts         # Fetch + mutate city list from /api/cities
        │   ├── useAddCity.ts        # POST /api/cities with optimistic update
        │   ├── useRemoveCity.ts     # DELETE /api/cities/{id} with optimistic update
        │   ├── useWeather.ts        # GET /api/weather/{lat}/{lon} for one city
        │   ├── useGeocode.ts        # GET /api/geocode?q= with 300ms debounce
        │   └── useAutoRefresh.ts    # setInterval(60_000) refresh trigger
        ├── components/
        │   ├── layout/
        │   │   ├── Sidebar.tsx
        │   │   └── MainContent.tsx
        │   ├── sidebar/
        │   │   ├── CityTree.tsx
        │   │   ├── CityTreeItem.tsx
        │   │   ├── AddCityButton.tsx
        │   │   ├── CitySearch.tsx
        │   │   ├── CitySearchDropdown.tsx
        │   │   └── EmptyState.tsx
        │   ├── weather/
        │   │   ├── WeatherCardGrid.tsx
        │   │   ├── WeatherCard.tsx
        │   │   ├── WeatherCardSkeleton.tsx
        │   │   └── WeatherIcon.tsx
        │   └── common/
        │       ├── ContextMenu.tsx
        │       └── ErrorBoundary.tsx
        ├── styles/
        │   └── index.css            # @tailwind base; @tailwind components; @tailwind utilities;
        └── __tests__/               # Mirrors src/ structure
            ├── setup.ts             # RTL setup: @testing-library/jest-dom
            ├── App.test.tsx
            ├── hooks/
            │   ├── useCities.test.ts
            │   ├── useAddCity.test.ts
            │   ├── useRemoveCity.test.ts
            │   ├── useWeather.test.ts
            │   └── useGeocode.test.ts
            └── components/
                ├── sidebar/
                │   ├── CityTree.test.tsx
                │   ├── CityTreeItem.test.tsx
                │   ├── CitySearch.test.tsx
                │   └── EmptyState.test.tsx
                └── weather/
                    ├── WeatherCard.test.tsx
                    ├── WeatherCardGrid.test.tsx
                    └── WeatherCardSkeleton.test.tsx
```

---

## Key Conventions

### General
- **No host dependencies** — Python, Node, pip, and npm are never run directly on the host. Use `docker compose exec` for all commands.
- **Single-stage Dockerfiles only** — no multi-stage builds anywhere.
- **Non-root container user** — backend Dockerfile creates and switches to `appuser` before CMD.
- **Environment variables** — never hardcode URLs or credentials. Always read from env vars (`DATABASE_URL`, `VITE_API_URL`, `ALLOWED_ORIGINS`).

### Backend Conventions
- **Framework:** FastAPI with automatic OpenAPI docs at `/docs`
- **Python version:** 3.12 (enforced in Dockerfile base image)
- **ORM:** SQLAlchemy with declarative `Mapped[]` type annotations (SQLAlchemy 2.0 style)
- **Schemas:** Pydantic v2 models in `app/schemas.py`; separate `CityCreate`, `CityRead` schemas
- **Dependency injection:** Use FastAPI's `Depends(get_db)` for all DB session access
- **Router organization:** One router per domain in `app/routers/`; mounted with prefix `/api` in `main.py`
- **External HTTP calls:** Use `httpx.AsyncClient` (async) for Open-Meteo requests; handle timeouts (10s default)
- **Error handling:** Raise `HTTPException` with appropriate status codes (404, 400, 502); never let external API errors crash unhandled
- **DB schema creation:** `Base.metadata.create_all(bind=engine)` called in a `startup` event handler in `main.py`
- **Duplicate cities:** Catch `IntegrityError` on POST `/api/cities` and return the existing record with `200 OK`
- **CORS:** Configured via `CORSMiddleware` using `ALLOWED_ORIGINS` env var

### Backend Testing Conventions
- **Test DB:** Use an in-memory SQLite database (`sqlite:///:memory:`) in `conftest.py`; override `get_db` dependency
- **HTTP mocking:** Use `pytest-mock` or `respx` to mock `httpx` calls to Open-Meteo in `test_weather.py` and `test_geocode.py`
- **Test client:** Use FastAPI's `TestClient` (synchronous) from `starlette.testclient`
- **Fixtures:** `conftest.py` provides `db_session`, `client`, and `sample_city` fixtures
- **Naming:** Test files named `test_<router>.py`; functions named `test_<action>_<scenario>`

### Frontend Conventions
- **Framework:** React 18 functional components only — no class components
- **Language:** TypeScript strict mode (`"strict": true` in `tsconfig.json`)
- **Styling:** Tailwind CSS utility classes only — no custom CSS except `index.css` Tailwind directives; no inline `style=` props
- **State management:** React built-in (`useState`, `useEffect`, `useCallback`, `useMemo`) — no Redux or Zustand
- **Data fetching:** Custom hooks in `src/hooks/` wrapping native `fetch` with `VITE_API_URL` base; no React Query
- **API base URL:** Always read from `import.meta.env.VITE_API_URL` via `src/api/client.ts`
- **Optimistic updates:** `useAddCity` and `useRemoveCity` update local state immediately before API call resolves
- **Auto-refresh:** `useAutoRefresh(60_000)` triggers weather re-fetch via a counter state increment
- **Animations:** Tailwind `transition`, `opacity`, and `translate` utilities for fade+slide; use `duration-200` for remove, `duration-300` for add
- **Debounce:** `useGeocode` implements a 300ms debounce via `useEffect` + `setTimeout` cleanup — no lodash
- **Context menu:** `ContextMenu.tsx` uses a React portal (`ReactDOM.createPortal`) to `document.body`; dismissed on `mousedown` outside or `Escape`
- **Responsive grid:** `WeatherCardGrid` uses `grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3` Tailwind classes
- **Emoji flags:** Country flags rendered as Unicode flag emojis derived from `country_code` (regional indicator symbols)
- **File naming:** PascalCase for components (`.tsx`), camelCase for hooks and utilities (`.ts`)
- **Exports:** Named exports for all components and hooks (no default exports except `App.tsx` and `main.tsx`)

### Frontend Testing Conventions
- **Runner:** Vitest with `jsdom` environment
- **Setup file:** `src/__tests__/setup.ts` imports `@testing-library/jest-dom` for extended matchers
- **Mocking:** `vi.mock()` for `src/api/client.ts`; `vi.fn()` for individual hook returns; `msw` (Mock Service Worker) optionally for integration-level tests
- **Queries:** Prefer `getByRole`, `getByLabelText`, `getByText` — avoid `getByTestId` unless no semantic alternative exists
- **User events:** Use `@testing-library/user-event` (`userEvent.type`, `userEvent.click`) over `fireEvent`
- **Async:** Use `waitFor` and `findBy*` queries for async state updates
- **Test structure:** `describe` block per component; `it` statements in plain English ("it renders the city name")
- **Coverage target:** All hooks and components introduced in each milestone have at least one happy-path and one error/edge-case test

### Git / Milestone Conventions
- Each milestone is developed on a feature branch: `milestone/1-infrastructure`, `milestone/2-backend-api`, etc.
- PRs merged to `main` only when all tests pass inside Docker
- Commit messages: `feat:`, `fix:`, `test:`, `chore:`, `docs:` prefixes
- `render.yaml` lives at repo root and is updated during Milestone 6

### Vite Dev Server Proxy
`vite.config.ts` proxies `/api` and `/health` to the backend container to avoid CORS issues in development:
```typescript
server: {
  proxy: {
    '/api': 'http://backend:8000',
    '/health': 'http://backend:8000',
  },
  host: '0.0.0.0',   // Required for Docker networking
  port: 5173,
}
```
Note: The proxy target uses the Docker Compose service name `backend`, not `localhost`.
