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
┌─────────────────────────────────────────────────────────────┐
│                        Browser                              │
│   React 18 + TypeScript + Tailwind CSS (Vite dev server)   │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP (VITE_API_URL)
┌─────────────────────▼───────────────────────────────────────┐
│              Backend (FastAPI / Uvicorn)                    │
│         Python 3.12  —  port 8000                          │
└────────┬────────────────────────────┬───────────────────────┘
         │ SQLAlchemy (psycopg2)      │ HTTPS
┌────────▼──────────┐    ┌───────────▼───────────────────────┐
│  PostgreSQL 16    │    │  Open-Meteo APIs (external)       │
│  port 5432        │    │  api.open-meteo.com               │
└───────────────────┘    │  geocoding-api.open-meteo.com     │
                         └───────────────────────────────────┘
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
      ALLOWED_ORIGINS: http://localhost:5173
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

### `backend/Dockerfile`

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chown -R appuser:appgroup /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### `frontend/Dockerfile`

```dockerfile
FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
```

> **Note:** Single-stage Dockerfiles only — no multi-stage builds. For production (Render), the frontend CMD becomes `npm run preview -- --host 0.0.0.0 --port 5173` after `npm run build`.

---

## Environment Variables

### Backend

| Variable | Default (local) | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql://weather:weather@db:5432/weatherdb` | PostgreSQL connection string (required) |
| `ALLOWED_ORIGINS` | `http://localhost:5173` | Comma-separated CORS allowed origins |

### Frontend

| Variable | Default (local) | Description |
|---|---|---|
| `VITE_API_URL` | `http://localhost:8000` | Base URL of the FastAPI backend |

### PostgreSQL Service (docker-compose only)

| Variable | Value |
|---|---|
| `POSTGRES_USER` | `weather` |
| `POSTGRES_PASSWORD` | `weather` |
| `POSTGRES_DB` | `weatherdb` |

---

## Database Schema

### Table: `cities`

Managed via SQLAlchemy models + Alembic migrations (or `Base.metadata.create_all` for simplicity in M1).

```sql
CREATE TABLE cities (
    id          SERIAL          PRIMARY KEY,
    name        VARCHAR(255)    NOT NULL,
    country     VARCHAR(100)    NOT NULL,
    latitude    DOUBLE PRECISION NOT NULL,
    longitude   DOUBLE PRECISION NOT NULL,
    created_at  TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

-- Unique constraint to prevent duplicate city entries
CREATE UNIQUE INDEX uix_cities_lat_lon
    ON cities (latitude, longitude);
```

#### Column Details

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `id` | `SERIAL` (integer) | No | auto-increment | Primary key |
| `name` | `VARCHAR(255)` | No | — | City display name (e.g. `"Paris"`) |
| `country` | `VARCHAR(100)` | No | — | Country name or code (e.g. `"France"`) |
| `latitude` | `DOUBLE PRECISION` | No | — | WGS-84 latitude |
| `longitude` | `DOUBLE PRECISION` | No | — | WGS-84 longitude |
| `created_at` | `TIMESTAMPTZ` | No | `NOW()` | Row insertion timestamp |

#### SQLAlchemy Model (`backend/app/models.py`)

```python
from sqlalchemy import Column, Integer, String, Float, DateTime, func
from app.database import Base

class City(Base):
    __tablename__ = "cities"

    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String(255), nullable=False)
    country    = Column(String(100), nullable=False)
    latitude   = Column(Float, nullable=False)
    longitude  = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
```

---

## API Endpoints

Base path: all endpoints served by FastAPI on port `8000`.

---

### `GET /health`

Health check.

**Response `200 OK`**
```json
{ "status": "ok" }
```

---

### `GET /api/cities`

Return all saved cities ordered by `created_at` ascending.

**Response `200 OK`**
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

**Response shape (array of):**

| Field | Type | Description |
|---|---|---|
| `id` | `integer` | DB primary key |
| `name` | `string` | City name |
| `country` | `string` | Country name |
| `latitude` | `number` | WGS-84 latitude |
| `longitude` | `number` | WGS-84 longitude |
| `created_at` | `string` (ISO-8601) | Creation timestamp |

---

### `POST /api/cities`

Add a new city. Silently ignores duplicates (matched by lat/lon uniqueness).

**Request Body `application/json`**
```json
{
  "name": "Paris",
  "country": "France",
  "latitude": 48.8566,
  "longitude": 2.3522
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | `string` | Yes | City display name |
| `country` | `string` | Yes | Country name |
| `latitude` | `number` | Yes | WGS-84 latitude |
| `longitude` | `number` | Yes | WGS-84 longitude |

**Response `201 Created`** — returns the newly created (or existing) city object:
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

**Response `422 Unprocessable Entity`** — validation error (missing/invalid fields).

---

### `DELETE /api/cities/{id}`

Remove a city by primary key.

**Path Parameter**

| Param | Type | Description |
|---|---|---|
| `id` | `integer` | City primary key |

**Response `204 No Content`** — city deleted successfully.

**Response `404 Not Found`**
```json
{ "detail": "City not found" }
```

---

### `GET /api/weather/{latitude}/{longitude}`

Fetch current weather from Open-Meteo for the given coordinates.

**Path Parameters**

| Param | Type | Description |
|---|---|---|
| `latitude` | `number` | WGS-84 latitude |
| `longitude` | `number` | WGS-84 longitude |

**Upstream call:** `https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m&wind_speed_unit=mph&temperature_unit=celsius&timezone=auto`

**Response `200 OK`**
```json
{
  "temperature_c": 18.5,
  "temperature_f": 65.3,
  "feels_like_c": 17.1,
  "feels_like_f": 62.8,
  "humidity": 62,
  "wind_speed_mph": 9.4,
  "weather_code": 2,
  "condition": "Partly Cloudy",
  "icon": "🌤",
  "updated_at": "2024-01-15T10:45:00Z"
}
```

| Field | Type | Description |
|---|---|---|
| `temperature_c` | `number` | Current temp in °C |
| `temperature_f` | `number` | Current temp in °F |
| `feels_like_c` | `number` | Apparent temp in °C |
| `feels_like_f` | `number` | Apparent temp in °F |
| `humidity` | `integer` | Relative humidity % |
| `wind_speed_mph` | `number` | Wind speed in mph |
| `weather_code` | `integer` | WMO weather code |
| `condition` | `string` | Human-readable condition label |
| `icon` | `string` | Emoji icon for condition |
| `updated_at` | `string` (ISO-8601) | Timestamp of Open-Meteo data |

**Response `502 Bad Gateway`** — upstream Open-Meteo call failed.

---

### `GET /api/geocode?q={query}`

Search for cities via Open-Meteo Geocoding API. Returns up to 5 results.

**Query Parameters**

| Param | Type | Required | Description |
|---|---|---|---|
| `q` | `string` | Yes | Search term (min 3 chars enforced on frontend; backend passes through) |

**Upstream call:** `https://geocoding-api.open-meteo.com/v1/search?name={q}&count=5&language=en&format=json`

**Response `200 OK`**
```json
[
  {
    "name": "Paris",
    "country": "France",
    "latitude": 48.8566,
    "longitude": 2.3522
  },
  {
    "name": "Paris",
    "country": "United States",
    "latitude": 33.6609,
    "longitude": -95.5555
  }
]
```

| Field | Type | Description |
|---|---|---|
| `name` | `string` | City name |
| `country` | `string` | Country name |
| `latitude` | `number` | WGS-84 latitude |
| `longitude` | `number` | WGS-84 longitude |

**Response `200 OK` with empty array `[]`** — no results found.

**Response `502 Bad Gateway`** — upstream geocoding call failed.

---

## WMO Weather Code Mapping

Used in `/api/weather` to derive `condition` and `icon`:

| Code(s) | Condition | Icon |
|---|---|---|
| 0 | Clear Sky | ☀️ |
| 1, 2, 3 | Partly Cloudy | 🌤 |
| 45, 48 | Foggy | 🌫 |
| 51, 53, 55, 61, 63, 65, 80, 81, 82 | Rainy | 🌧 |
| 71, 73, 75, 77, 85, 86 | Snowy | ❄️ |
| 95, 96, 99 | Thunderstorm | ⛈ |
| _(fallback)_ | Cloudy | ⛅ |

---

## Frontend Component Tree

```
src/
├── main.tsx                          # React DOM entry point
├── App.tsx                           # Root: layout shell, global state (city list)
│
├── api/
│   └── client.ts                     # Typed API client (fetch wrapper, VITE_API_URL)
│       ├── getCities()               # GET /api/cities
│       ├── addCity(payload)          # POST /api/cities
│       ├── removeCity(id)            # DELETE /api/cities/{id}
│       ├── getWeather(lat, lon)      # GET /api/weather/{lat}/{lon}
│       └── geocodeSearch(q)          # GET /api/geocode?q=
│
├── types/
│   └── index.ts                      # Shared TypeScript interfaces
│       ├── City                      # { id, name, country, latitude, longitude, created_at }
│       ├── WeatherData               # { temperature_c, temperature_f, feels_like_c, ... }
│       └── GeoResult                 # { name, country, latitude, longitude }
│
├── hooks/
│   ├── useCities.ts                  # Manages city list state; add/remove CRUD via API client
│   ├── useWeather.ts                 # Fetches weather for a single city; auto-refreshes every 60s
│   └── useGeocode.ts                 # Debounced geocode search (300ms), min 3 chars
│
├── components/
│   ├── layout/
│   │   ├── AppLayout.tsx             # Two-panel flex wrapper (sidebar + main)
│   │   ├── Sidebar.tsx               # Left panel; composes CityTree + AddCityFlow
│   │   └── MainContent.tsx           # Right panel; composes WeatherCardGrid
│   │
│   ├── sidebar/
│   │   ├── CityTree.tsx              # Scrollable list of CityTreeItem; empty state
│   │   ├── CityTreeItem.tsx          # Single row: flag emoji + name + live temp; right-click context menu
│   │   ├── ContextMenu.tsx           # Right-click popup with Remove option
│   │   ├── AddCityButton.tsx         # "＋ Add City" button that triggers AddCityFlow
│   │   └── AddCityFlow.tsx           # Inline search input + GeoSearchDropdown
│   │
│   ├── geocode/
│   │   └── GeoSearchDropdown.tsx     # Dropdown list of up to 5 GeoResult items
│   │
│   ├── weather/
│   │   ├── WeatherCardGrid.tsx       # Responsive CSS grid; maps cities → WeatherCard
│   │   ├── WeatherCard.tsx           # Full weather card; calls useWeather; animate in/out
│   │   ├── WeatherCardSkeleton.tsx   # Loading placeholder matching card dimensions
│   │   └── WeatherIcon.tsx           # Renders emoji icon + condition label
│   │
│   └── common/
│       ├── EmptyState.tsx            # "Add a city to get started" illustration + arrow
│       └── ErrorBanner.tsx           # Generic inline error display
│
└── styles/
    └── index.css                     # Tailwind base/components/utilities directives
```

### State Management

Global state is lifted into `App.tsx` via `useCities` hook (no Redux/Zustand — React state + context is sufficient given the scope):

```
App.tsx
  └── cities: City[]          ← authoritative list, fetched on mount, mutated by add/remove
        ├── passed to Sidebar (for CityTree display)
        └── passed to MainContent (for WeatherCardGrid)
```

Each `WeatherCard` maintains its own `WeatherData` state via `useWeather(lat, lon)`.

---

## Data Flow

### Page Load
```
App mounts → useCities → GET /api/cities
  → cities[] stored in state
  → CityTree renders items
  → WeatherCardGrid renders cards
  → each WeatherCard mounts → useWeather → GET /api/weather/{lat}/{lon}
```

### Add City
```
User types (≥3 chars) → useGeocode debounce 300ms → GET /api/geocode?q=
  → GeoSearchDropdown shows ≤5 results
User clicks result → POST /api/cities → city appended to cities[]
  → CityTreeItem animates in
  → WeatherCard animates in (fade + slide up)
  → AddCityFlow closes
```

### Remove City (card × or tree right-click)
```
User triggers remove → DELETE /api/cities/{id}
  → city removed from cities[]
  → WeatherCard animates out (fade + slide down 200ms) then unmounts
  → CityTreeItem simultaneously removed
```

### Auto-Refresh
```
useWeather sets interval (60 000ms)
  → GET /api/weather/{lat}/{lon} every 60s
  → WeatherData state updated → card re-renders
  → interval cleared on component unmount
```

---

## Deployment (Render)

### `render.yaml`

```yaml
services:
  - type: web
    name: weather-backend
    runtime: docker
    dockerfilePath: ./backend/Dockerfile
    dockerContext: ./backend
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: weather-db
          property: connectionString
      - key: ALLOWED_ORIGINS
        value: https://weather-frontend.onrender.com

  - type: web
    name: weather-frontend
    runtime: docker
    dockerfilePath: ./frontend/Dockerfile
    dockerContext: ./frontend
    envVars:
      - key: VITE_API_URL
        value: https://weather-backend.onrender.com

databases:
  - name: weather-db
    plan: free
    databaseName: weatherdb
    user: weather
```

### Production Notes
- Backend `CMD` in Dockerfile uses `uvicorn` without `--reload`.
- Backend runs as non-root user (`appuser`).
- Frontend production `CMD`: `npm run build && npm run preview -- --host 0.0.0.0 --port 5173` (or served via nginx).
- `DATABASE_URL` is injected by Render from the managed PostgreSQL service — never hardcoded.
- `VITE_API_URL` must be set at **build time** for Vite to embed it; set as a Render build environment variable.
