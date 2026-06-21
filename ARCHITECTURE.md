# ARCHITECTURE.md — Weather Dashboard: Real-time City Weather Tracker

## Table of Contents
1. [System Overview](#system-overview)
2. [Docker Services](#docker-services)
3. [Environment Variables](#environment-variables)
4. [Database Schema](#database-schema)
5. [API Endpoints](#api-endpoints)
6. [Frontend Component Tree](#frontend-component-tree)
7. [Data Flow](#data-flow)
8. [Deployment (Render)](#deployment-render)

---

## System Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Compose Network               │
│                                                         │
│  ┌──────────────┐    ┌──────────────┐   ┌───────────┐  │
│  │   frontend   │───▶│   backend    │──▶│    db     │  │
│  │  (React/Vite)│    │  (FastAPI)   │   │(Postgres) │  │
│  │  Port: 5173  │    │  Port: 8000  │   │ Port:5432 │  │
│  └──────────────┘    └──────┬───────┘   └───────────┘  │
│                             │                           │
│                    ┌────────▼────────┐                  │
│                    │  Open-Meteo API │ (external)        │
│                    │  - Weather      │                  │
│                    │  - Geocoding    │                  │
│                    └─────────────────┘                  │
└─────────────────────────────────────────────────────────┘
```

---

## Docker Services

### `docker-compose.yml`

```yaml
version: "3.9"
services:

  db:
    image: postgres:16-alpine
    restart: unless-stopped
    environment:
      POSTGRES_USER: weather
      POSTGRES_PASSWORD: weather
      POSTGRES_DB: weatherdb
    volumes:
      - pg_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U weather -d weatherdb"]
      interval: 5s
      timeout: 5s
      retries: 10

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    restart: unless-stopped
    environment:
      DATABASE_URL: postgresql://weather:weather@db:5432/weatherdb
      PYTHONUNBUFFERED: "1"
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    restart: unless-stopped
    environment:
      VITE_API_URL: http://localhost:8000
    ports:
      - "5173:5173"
    depends_on:
      - backend

volumes:
  pg_data:
```

### Service Definitions

| Service    | Base Image              | Port | Role                                      |
|------------|-------------------------|------|-------------------------------------------|
| `db`       | `postgres:16-alpine`    | 5432 | PostgreSQL 16 — persists city list        |
| `backend`  | `python:3.12-slim`      | 8000 | FastAPI + Uvicorn — API + weather proxy   |
| `frontend` | `node:20-alpine`        | 5173 | React 18 + Vite dev server (dev) / nginx (prod) |

### `backend/Dockerfile`
```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chown -R app:app /app
USER app

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### `frontend/Dockerfile`
```dockerfile
FROM node:20-alpine

WORKDIR /app

# VITE_API_URL is inlined into the bundle at build time, so it is a build ARG
# (passed via Compose build.args / docker-bake.hcl) promoted to ENV for the dev
# server. It is a public URL, not a secret.
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
```

### `docker-bake.hcl`
`docker buildx bake` builds the same two images as `docker compose build` and is
the canonical place to declare build args explicitly. The `frontend` target
forwards the `VITE_API_URL` variable (default `http://localhost:8000`); the
`backend` target declares no build args — its runtime secrets are never baked.

---

## Environment Variables

### Backend

| Variable       | Required | Default (dev)                                        | Description                              |
|----------------|----------|------------------------------------------------------|------------------------------------------|
| `DATABASE_URL` | ✅ Yes   | `postgresql://weather:weather@db:5432/weatherdb`     | PostgreSQL connection string             |
| `PYTHONUNBUFFERED` | No   | `1`                                                  | Ensures logs flush immediately           |

### Frontend

| Variable       | Required | Default (dev)          | Description                              |
|----------------|----------|------------------------|------------------------------------------|
| `VITE_API_URL` | ✅ Yes   | `http://localhost:8000` | Base URL of the FastAPI backend. **Build-time** — passed as a Docker build ARG (Compose `build.args` / `docker-bake.hcl`) because Vite inlines it into the bundle. |

> **Note:** All env vars come from the gitignored `.env` file (template:
> `.env.example`), which `docker compose` loads automatically. `VITE_API_URL` is
> additionally forwarded as a build arg so it reaches Vite at build time. For
> Render, vars are set via the dashboard or `render.yaml`.

---

## Database Schema

### PostgreSQL 16 — Database: `weatherdb`

#### Table: `cities`

| Column       | Type                        | Constraints                       | Description                             |
|--------------|-----------------------------|-----------------------------------|-----------------------------------------|
| `id`         | `SERIAL`                    | `PRIMARY KEY`                     | Auto-incrementing integer PK            |
| `name`       | `VARCHAR(255)`              | `NOT NULL`                        | City name (e.g. "Paris")                |
| `country`    | `VARCHAR(100)`              | `NOT NULL`                        | Country name (e.g. "France")            |
| `latitude`   | `DOUBLE PRECISION`          | `NOT NULL`                        | Geographic latitude (-90 to 90)         |
| `longitude`  | `DOUBLE PRECISION`          | `NOT NULL`                        | Geographic longitude (-180 to 180)      |
| `created_at` | `TIMESTAMP WITH TIME ZONE`  | `NOT NULL, DEFAULT NOW()`         | UTC timestamp of when city was added    |

**Unique constraint:** `UNIQUE(name, country)` — prevents duplicate city entries.

#### SQLAlchemy Model (Python)
```python
class City(Base):
    __tablename__ = "cities"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    name       = Column(String(255), nullable=False)
    country    = Column(String(100), nullable=False)
    latitude   = Column(Float, nullable=False)
    longitude  = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (UniqueConstraint("name", "country", name="uq_city_name_country"),)
```

#### Migration Strategy
- Tables are created via `Base.metadata.create_all(engine)` on backend startup (no Alembic for simplicity in Milestone 1).
- In production, this is idempotent — existing tables are not dropped.

---

## API Endpoints

All backend endpoints are prefixed with the FastAPI app root. CORS is enabled for all origins in development.

### `GET /health`
Health check for load balancer and Docker healthcheck.

**Response `200 OK`:**
```json
{ "status": "ok" }
```

---

### `GET /api/cities`
Returns all saved cities ordered by `created_at ASC`.

**Response `200 OK`:**
```json
[
  {
    "id": 1,
    "name": "Paris",
    "country": "France",
    "latitude": 48.8566,
    "longitude": 2.3522,
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```

---

### `POST /api/cities`
Adds a new city. Silently ignores duplicates (returns existing record).

**Request Body:**
```json
{
  "name": "Paris",
  "country": "France",
  "latitude": 48.8566,
  "longitude": 2.3522
}
```

**Response `201 Created`:**
```json
{
  "id": 1,
  "name": "Paris",
  "country": "France",
  "latitude": 48.8566,
  "longitude": 2.3522,
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Response `200 OK`** (duplicate — city already exists, returns existing record):
```json
{
  "id": 1,
  "name": "Paris",
  "country": "France",
  "latitude": 48.8566,
  "longitude": 2.3522,
  "created_at": "2024-01-15T10:30:00Z"
}
```

---

### `DELETE /api/cities/{id}`
Removes a city by its integer ID.

**Path Parameter:** `id` — integer, city primary key.

**Response `204 No Content`:** (empty body on success)

**Response `404 Not Found`:**
```json
{ "detail": "City not found" }
```

---

### `GET /api/weather/{latitude}/{longitude}`
Fetches current weather for the given coordinates from the Open-Meteo API. Acts as a backend proxy to avoid CORS issues and to enable future caching.

**Path Parameters:**
- `latitude` — float, e.g. `48.8566`
- `longitude` — float, e.g. `2.3522`

**Open-Meteo request (internal):**
```
GET https://api.open-meteo.com/v1/forecast
  ?latitude={lat}
  &longitude={lon}
  &current=temperature_2m,relative_humidity_2m,apparent_temperature,
            weather_code,wind_speed_10m
  &wind_speed_unit=mph
  &temperature_unit=celsius
  &timezone=auto
```

**Response `200 OK`:**
```json
{
  "temperature_c": 18.4,
  "temperature_f": 65.1,
  "feels_like_c": 16.2,
  "feels_like_f": 61.2,
  "humidity": 72,
  "wind_speed_mph": 8.3,
  "weather_code": 2,
  "weather_description": "Partly Cloudy",
  "weather_emoji": "🌤",
  "last_updated": "2024-01-15T10:45:00Z"
}
```

**Response `502 Bad Gateway`** (if Open-Meteo is unreachable):
```json
{ "detail": "Weather service unavailable" }
```

#### WMO Weather Code → Emoji + Description Mapping (used internally)

| Code Range | Description       | Emoji |
|------------|-------------------|-------|
| 0          | Clear Sky         | ☀️    |
| 1          | Mainly Clear      | 🌤    |
| 2          | Partly Cloudy     | ⛅    |
| 3          | Overcast          | ☁️    |
| 45, 48     | Fog               | 🌫    |
| 51–67      | Drizzle / Rain    | 🌧    |
| 71–77      | Snow              | ❄️    |
| 80–82      | Rain Showers      | 🌧    |
| 95–99      | Thunderstorm      | ⛈    |

---

### `GET /api/geocode?q={query}`
Proxies a search to the Open-Meteo Geocoding API. Returns up to 5 results.

**Query Parameter:** `q` — string, minimum 3 characters.

**Response `200 OK`:**
```json
[
  {
    "name": "Paris",
    "country": "France",
    "latitude": 48.8566,
    "longitude": 2.3522,
    "country_code": "FR"
  },
  {
    "name": "Paris",
    "country": "United States",
    "latitude": 33.6609,
    "longitude": -95.5555,
    "country_code": "US"
  }
]
```

**Response `400 Bad Request`** (query < 3 chars):
```json
{ "detail": "Query must be at least 3 characters" }
```

**Response `502 Bad Gateway`** (if geocoding service unavailable):
```json
{ "detail": "Geocoding service unavailable" }
```

---

## Frontend Component Tree

```
src/
├── main.tsx                         # React 18 root, mounts <App />
├── App.tsx                          # Root component — layout shell, global state
│
├── components/
│   ├── layout/
│   │   ├── Sidebar.tsx              # Left panel wrapper (w-64, fixed height)
│   │   └── MainContent.tsx          # Right panel wrapper (flex-grow, scroll)
│   │
│   ├── sidebar/
│   │   ├── CityTree.tsx             # Scrollable city list container
│   │   ├── CityTreeItem.tsx         # Single city row (flag, name, temp) + right-click
│   │   ├── ContextMenu.tsx          # Floating right-click menu with Remove option
│   │   ├── AddCityButton.tsx        # "＋ Add City" button
│   │   ├── CitySearchInput.tsx      # Inline search input with debounce
│   │   ├── CitySearchDropdown.tsx   # Autocomplete results list (max 5)
│   │   └── EmptyState.tsx           # "Add a city to get started" message + arrow
│   │
│   ├── weather/
│   │   ├── WeatherCardGrid.tsx      # Responsive grid wrapper (3/2/1 cols)
│   │   ├── WeatherCard.tsx          # Full weather card with all data fields
│   │   ├── WeatherCardSkeleton.tsx  # Loading skeleton matching card dimensions
│   │   └── WeatherIcon.tsx          # Renders emoji icon from weather_code
│   │
│   └── common/
│       └── ErrorBanner.tsx          # Inline error message component
│
├── hooks/
│   ├── useCities.ts                 # CRUD ops for city list (fetch, add, remove)
│   ├── useWeather.ts                # Fetch weather for one city; manages loading state
│   ├── useGeocode.ts                # Debounced geocoding search (300ms)
│   └── useAutoRefresh.ts           # setInterval wrapper — triggers refetch every 60s
│
├── api/
│   ├── client.ts                    # Axios instance with baseURL = VITE_API_URL
│   ├── cities.ts                    # API calls: getCities, addCity, deleteCity
│   ├── weather.ts                   # API call: getWeather(lat, lon)
│   └── geocode.ts                   # API call: searchCities(query)
│
├── types/
│   └── index.ts                     # Shared TypeScript interfaces:
│                                    #   City, WeatherData, GeocodeResult
│
└── styles/
    └── index.css                    # Tailwind CSS directives (@tailwind base/components/utilities)
```

### Key TypeScript Interfaces (`src/types/index.ts`)

```typescript
export interface City {
  id: number;
  name: string;
  country: string;
  latitude: number;
  longitude: number;
  created_at: string;
}

export interface WeatherData {
  temperature_c: number;
  temperature_f: number;
  feels_like_c: number;
  feels_like_f: number;
  humidity: number;
  wind_speed_mph: number;
  weather_code: number;
  weather_description: string;
  weather_emoji: string;
  last_updated: string;
}

export interface GeocodeResult {
  name: string;
  country: string;
  latitude: number;
  longitude: number;
  country_code: string;
}
```

### State Management

Global state lives in `App.tsx` and is passed via props / context:

| State Slice       | Type        | Location         | Description                                  |
|-------------------|-------------|------------------|----------------------------------------------|
| `cities`          | `City[]`    | `App.tsx`        | Master list of saved cities                  |
| `weatherMap`      | `Map<number, WeatherData>` | `App.tsx` | Weather keyed by city ID               |
| `isSearchOpen`    | `boolean`   | `Sidebar.tsx`    | Controls search input visibility             |
| `searchQuery`     | `string`    | `CitySearchInput` | Current debounced search string             |
| `geocodeResults`  | `GeocodeResult[]` | `CitySearchInput` | Current autocomplete results           |
| `contextMenu`     | `{cityId, x, y} \| null` | `CityTree.tsx` | Right-click context menu state    |
| `removingCityIds` | `Set<number>` | `App.tsx`      | IDs currently animating out                  |

---

## Data Flow

### Page Load
```
App mounts
  → useCities.fetchAll() → GET /api/cities
  → for each city: useWeather.fetch(lat, lon) → GET /api/weather/{lat}/{lon}
  → render CityTree + WeatherCardGrid
```

### Add City
```
User types (≥3 chars, 300ms debounce)
  → useGeocode → GET /api/geocode?q={query}
  → dropdown renders GeocodeResult[]
User clicks result
  → useCities.add(result) → POST /api/cities
  → city added to cities[] state
  → useWeather.fetch(lat, lon) → GET /api/weather/{lat}/{lon}
  → WeatherCard animates in (fade + slide-up, CSS transition)
```

### Remove City
```
User clicks × on card OR right-click → Remove
  → city ID added to removingCityIds (triggers exit animation, 200ms)
  → after 200ms: useCities.remove(id) → DELETE /api/cities/{id}
  → city removed from cities[] state
  → WeatherCard + CityTreeItem disappear simultaneously
```

### Auto-Refresh
```
useAutoRefresh(60_000)
  → every 60s: for each city in cities[]
    → GET /api/weather/{lat}/{lon}
    → weatherMap updated → WeatherCard re-renders with new data
```

---

## Deployment (Render)

### `render.yaml`
```yaml
services:
  - type: web
    name: weather-backend
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: weather-db
          property: connectionString

  - type: web
    name: weather-frontend
    env: static
    buildCommand: npm ci && npm run build
    staticPublishPath: ./dist
    envVars:
      - key: VITE_API_URL
        value: https://weather-backend.onrender.com

databases:
  - name: weather-db
    databaseName: weatherdb
    user: weather
    plan: free
```

### Production Notes
- Backend Dockerfile uses non-root user (`app`) — Render-compatible.
- No `--reload` flag in production CMD.
- `DATABASE_URL` injected by Render from managed Postgres; never hardcoded.
- Frontend built as static files via `npm run build` → served by Render's CDN.
- CORS configured in FastAPI to allow the Render frontend domain.
