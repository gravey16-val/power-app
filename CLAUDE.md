# CLAUDE.md — Weather Dashboard: Real-time City Weather Tracker

## How to Run

### Start the Full Stack
```bash
# Build images and start all services (db, backend, frontend)
docker compose up --build

# Run in detached mode
docker compose up --build -d

# View logs (all services)
docker compose logs -f

# View logs (specific service)
docker compose logs -f backend
docker compose logs -f frontend
```

### Service URLs (local dev)
| Service  | URL                          |
|----------|------------------------------|
| Frontend | http://localhost:5173        |
| Backend  | http://localhost:8000        |
| API Docs | http://localhost:8000/docs   |
| Health   | http://localhost:8000/health |

### Stop / Teardown
```bash
# Stop services (preserve volumes)
docker compose down

# Stop and delete database volume (full reset)
docker compose down -v
```

---

## How to Test

> ⚠️ All tests run **inside Docker containers**. No local Python or Node installation required.

### Backend Tests (pytest)
```bash
# Run full pytest suite
docker compose exec backend pytest

# Run with verbose output
docker compose exec backend pytest -v

# Run a specific test file
docker compose exec backend pytest tests/test_cities.py -v

# Run a specific test
docker compose exec backend pytest tests/test_cities.py::test_add_city -v

# Run with coverage report
docker compose exec backend pytest --cov=. --cov-report=term-missing
```

### Frontend Tests (Vitest + React Testing Library)
```bash
# Run full Vitest suite (single run, no watch)
docker compose exec frontend npx vitest run

# Run with verbose output
docker compose exec frontend npx vitest run --reporter=verbose

# Run a specific test file
docker compose exec frontend npx vitest run src/components/weather/WeatherCard.test.tsx

# Run with coverage
docker compose exec frontend npx vitest run --coverage
```

### Running Tests Against a Fresh Stack
```bash
# Ensure stack is running before exec commands
docker compose up --build -d
docker compose exec backend pytest
docker compose exec frontend npx vitest run
```

---

## Project Structure

```
weather-dashboard/
├── docker-compose.yml          # Orchestrates db, backend, frontend services
├── render.yaml                 # Render deployment config
├── README.md
├── ARCHITECTURE.md
├── CLAUDE.md
│
├── backend/
│   ├── Dockerfile              # Single-stage: python:3.12-slim, non-root user
│   ├── requirements.txt        # fastapi, uvicorn, sqlalchemy, psycopg2-binary,
│   │                           #   httpx, pydantic, pytest, pytest-cov, httpx (test client)
│   ├── main.py                 # FastAPI app factory, CORS, router includes, DB init
│   ├── database.py             # SQLAlchemy engine, SessionLocal, Base
│   ├── models.py               # City ORM model
│   ├── schemas.py              # Pydantic request/response schemas
│   ├── routers/
│   │   ├── cities.py           # GET/POST /api/cities, DELETE /api/cities/{id}
│   │   ├── weather.py          # GET /api/weather/{latitude}/{longitude}
│   │   └── geocode.py          # GET /api/geocode?q=
│   └── tests/
│       ├── conftest.py         # pytest fixtures: test DB, test client (TestClient)
│       ├── test_health.py      # Tests: GET /health → 200
│       ├── test_cities.py      # Tests: list, add, add duplicate, delete, delete 404
│       ├── test_weather.py     # Tests: valid coords (mocked httpx), bad gateway
│       └── test_geocode.py     # Tests: valid query, short query 400, proxied results
│
└── frontend/
    ├── Dockerfile              # Single-stage: node:20-alpine, vite --host
    ├── package.json            # react, react-dom, axios, tailwindcss, vite,
    │                           #   vitest, @testing-library/react, @testing-library/user-event
    ├── package-lock.json
    ├── vite.config.ts          # Vite config: React plugin, test config (jsdom)
    ├── tailwind.config.ts      # Tailwind content paths
    ├── tsconfig.json           # TypeScript strict mode
    ├── index.html              # Vite HTML entry point
    └── src/
        ├── main.tsx            # ReactDOM.createRoot, renders <App />
        ├── App.tsx             # Root layout, global state, useCities hook
        ├── types/
        │   └── index.ts        # City, WeatherData, GeocodeResult interfaces
        ├── api/
        │   ├── client.ts       # Axios instance: baseURL = import.meta.env.VITE_API_URL
        │   ├── cities.ts       # getCities(), addCity(), deleteCity()
        │   ├── weather.ts      # getWeather(lat, lon)
        │   └── geocode.ts      # searchCities(query)
        ├── hooks/
        │   ├── useCities.ts    # Manages cities[] state + CRUD API calls
        │   ├── useWeather.ts   # Fetches weather for one city, loading/error state
        │   ├── useGeocode.ts   # Debounced search (300ms) → GeocodeResult[]
        │   └── useAutoRefresh.ts # setInterval-based refresh trigger
        ├── components/
        │   ├── layout/
        │   │   ├── Sidebar.tsx
        │   │   └── MainContent.tsx
        │   ├── sidebar/
        │   │   ├── CityTree.tsx
        │   │   ├── CityTreeItem.tsx
        │   │   ├── ContextMenu.tsx
        │   │   ├── AddCityButton.tsx
        │   │   ├── CitySearchInput.tsx
        │   │   ├── CitySearchDropdown.tsx
        │   │   └── EmptyState.tsx
        │   ├── weather/
        │   │   ├── WeatherCardGrid.tsx
        │   │   ├── WeatherCard.tsx
        │   │   ├── WeatherCardSkeleton.tsx
        │   │   └── WeatherIcon.tsx
        │   └── common/
        │       └── ErrorBanner.tsx
        ├── styles/
        │   └── index.css       # @tailwind base; @tailwind components; @tailwind utilities;
        └── tests/
            ├── setup.ts        # @testing-library/jest-dom/vitest matchers
            ├── App.test.tsx    # Integration: renders layout, empty state
            ├── components/
            │   ├── WeatherCard.test.tsx        # Renders all weather fields
            │   ├── WeatherCardSkeleton.test.tsx
            │   ├── CityTreeItem.test.tsx       # Right-click context menu
            │   ├── CitySearchInput.test.tsx    # Debounce, dropdown, Escape key
            │   ├── EmptyState.test.tsx
            │   └── ContextMenu.test.tsx
            └── hooks/
                ├── useCities.test.ts           # Add, remove, dedup logic
                └── useGeocode.test.ts          # Debounce timing (vi.useFakeTimers)
```

---

## Key Conventions

### General
- **Everything runs in Docker** — never install Python or Node on the host for runtime.
- **Single-stage Dockerfiles only** — no multi-stage builds. Keep it simple.
- **Non-root user in backend container** — required by Render; user `app` is created in Dockerfile.
- **No `--reload` in production CMD** — only use `--reload` locally via `docker compose override` if needed.

### Backend (Python / FastAPI)

#### File & Module Layout
- `main.py` is the FastAPI app entry point. It calls `Base.metadata.create_all(engine)` on startup.
- All routers live in `routers/` and are included in `main.py` with their prefix (`/api`).
- `database.py` exposes: `engine`, `SessionLocal`, `Base`, and a `get_db()` dependency.
- `schemas.py` uses Pydantic v2 (`model_config = ConfigDict(from_attributes=True)`).

#### Coding Standards
- All route functions use `Depends(get_db)` for DB sessions — never instantiate `SessionLocal` directly in route handlers.
- External HTTP calls (Open-Meteo) use `httpx.AsyncClient` with a 10-second timeout.
- Return `HTTPException(status_code=404)` for missing resources, `502` for upstream failures.
- Duplicate city handling: catch `IntegrityError` on `UNIQUE(name, country)` violation → return existing record with `200`.

#### Testing Conventions
- `tests/conftest.py` creates an **in-memory SQLite DB** for tests (overrides `get_db` dependency).
- External API calls (Open-Meteo) are mocked using `pytest-mock` / `httpx` mock transports — tests never make real network calls.
- Test files are named `test_*.py`; test functions `test_*`.
- Each test file focuses on one router module.

#### `requirements.txt` (key packages)
```
fastapi>=0.111.0
uvicorn[standard]>=0.29.0
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.9
httpx>=0.27.0
pydantic>=2.0.0
pytest>=8.0.0
pytest-cov>=5.0.0
pytest-mock>=3.14.0
```

### Frontend (React / TypeScript / Vite)

#### Coding Standards
- **TypeScript strict mode** is enabled (`"strict": true` in `tsconfig.json`).
- All components are **function components** with explicit return type annotations where helpful.
- No `any` types — use `unknown` + type guards if type is genuinely unknown.
- Props interfaces are defined inline (`interface Props { ... }`) at the top of each component file.
- Hooks follow the naming convention `use*` and live in `src/hooks/`.

#### API Layer
- All backend calls go through `src/api/client.ts` (Axios instance).
- Never call `fetch()` or `axios` directly in components — always use the typed functions in `src/api/`.
- `VITE_API_URL` is accessed via `import.meta.env.VITE_API_URL`. This is baked in at build time.

#### Styling
- **Tailwind CSS utility classes only** — no custom CSS except in `index.css` for Tailwind directives.
- Responsive grid breakpoints: `grid-cols-1 md:grid-cols-2 lg:grid-cols-3`.
- Animation classes for card enter: `animate-fade-slide-up` (defined in `tailwind.config.ts` as a custom keyframe).
- Animation classes for card exit: `animate-fade-slide-down` applied when city ID is in `removingCityIds`.

#### State Management
- **No Redux / Zustand** — state is managed with `useState` and `useReducer` in `App.tsx` and passed via props.
- If prop drilling becomes deeper than 3 levels, use React Context (e.g., for `removeCity` callback).
- `weatherMap` is a `Map<number, WeatherData>` stored in state — use `new Map(prev).set(...)` pattern for immutable updates.

#### Testing Conventions
- Test files colocated under `src/tests/` mirroring the component/hook structure.
- `src/tests/setup.ts` is referenced in `vite.config.ts` under `test.setupFiles`.
- All API calls are mocked using `vi.mock('../../api/cities')` etc. — no real HTTP in tests.
- Use `@testing-library/user-event` for simulating user interactions (typing, clicking, right-clicking).
- Use `vi.useFakeTimers()` for testing debounce in `useGeocode` and auto-refresh in `useAutoRefresh`.
- Prefer `findBy*` queries (async) over `getBy*` when testing async state updates.

#### `package.json` (key dependencies)
```json
{
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "axios": "^1.7.0"
  },
  "devDependencies": {
    "typescript": "^5.4.0",
    "vite": "^5.2.0",
    "@vitejs/plugin-react": "^4.3.0",
    "tailwindcss": "^3.4.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0",
    "vitest": "^1.6.0",
    "jsdom": "^24.0.0",
    "@testing-library/react": "^16.0.0",
    "@testing-library/user-event": "^14.5.0",
    "@testing-library/jest-dom": "^6.4.0"
  }
}
```

#### `vite.config.ts` (test configuration)
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/tests/setup.ts'],
    globals: true,
  },
})
```

### Deployment (Render)
- `render.yaml` (repo root) is a Render Blueprint defining three resources:
  - **weather-backend** — Python Web Service, `rootDir: backend`, build `pip install -r requirements.txt`, start `uvicorn main:app --host 0.0.0.0 --port $PORT`, health check `GET /health`.
  - **weather-frontend** — static site, `rootDir: frontend`, build `npm ci && npm run build`, publish `./dist`, with an SPA `/* → /index.html` rewrite.
  - **weather-db** — managed PostgreSQL 16.
- `DATABASE_URL` is injected into the backend via `fromDatabase` (the `weather-db` connection string) — never hardcoded.
- `VITE_API_URL` is baked into the frontend build (`https://weather-backend.onrender.com`); Vite reads `VITE_*` at build time, so it must be a full `https://` URL.
- Validate locally with the Render CLI (`render blueprint validate`) or any YAML linter. See `DECISIONS.md` for why `render.yaml` extends the ARCHITECTURE.md §Deployment template (`runtime:` key, `rootDir`, SPA rewrite).

### Git Conventions
- Branch naming: `milestone/{number}-{short-description}` (e.g., `milestone/1-scaffold`)
- Commit messages: imperative mood, e.g. `Add DELETE /api/cities/{id} endpoint`
- `docker-compose.yml`, `render.yaml`, both `Dockerfile`s, and `ARCHITECTURE.md` are always committed.
- Never commit `.env` files — use `docker-compose.yml` env vars for local dev.

### Milestone Development Order
Each milestone is self-contained and leaves the app in a working state:

| Milestone | Focus                        | Definition of Done                                      |
|-----------|------------------------------|---------------------------------------------------------|
| 1         | Infrastructure & Scaffold    | `docker compose up` → health check passes, DB schema created, test harnesses run |
| 2         | Backend API                  | All 6 endpoints pass pytest; correct status codes       |
| 3         | Frontend Shell               | Two-panel layout renders; API data flows in; empty state visible |
| 4         | Add City Feature             | Search → autocomplete → add → persists in DB + UI       |
| 5         | Remove City Feature          | × button + right-click remove → simultaneous UI update + DB delete + animation |
| 6         | Polish                       | Auto-refresh (60s), page-reload persistence, responsive at 375/768/1440px |
