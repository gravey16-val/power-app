# ARCHITECTURE.md — Weather Dashboard: Real-time City Weather Tracker

## Table of Contents
1. [System Overview](#system-overview)
2. [Docker Services](#docker-services)
3. [Environment Variables](#environment-variables)
4. [Database Schema](#database-schema)
5. [API Endpoints](#api-endpoints)
6. [External APIs](#external-apis)
7. [Frontend Component Tree](#frontend-component-tree)
8. [Data Flow](#data-flow)
9. [Deployment (Render)](#deployment-render)

---

## System Overview

```
┌─────────────────────────────────────────────────────────┐
│                     Browser Client                      │
│          React 18 + TypeScript + Tailwind + Vite        │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP (VITE_API_URL)
┌────────────────────────▼────────────────────────────────┐
│                   Backend Service                       │
│           FastAPI (Python 3.12) + Uvicorn               │
│                  Port 8000                              │
└──────────┬──────────────────────────┬───────────────────┘
           │ SQLAlchemy (DATABASE_URL) │ HTTP (Open-Meteo)
┌──────────▼──────────┐  ┌────────────▼───────────────────┐
│  PostgreSQL 16      │  │  Open-Meteo APIs (external)    │
│  Port 5432          │  │  api.open-meteo.com            │
│  "weather_db"       │  │  geocoding-api.open-meteo.com  │
└─────────────────────┘  └────────────────────────────────┘
```

---

## Docker Services

### `docker-compose.yml`

| Service    | Image / Build          | Internal Port | External Port | Depends On |
|------------|------------------------|---------------|---------------|------------|
| `db`       | `postgres:16-alpine`   | 5432          | 5432          | —          |
| `backend`  | `./backend/Dockerfile` | 8000          | 8000          | `db`       |
| `frontend` | `./frontend/Dockerfile`| 5173          | 5173          | `backend`  |

```yaml
# docker-compose.yml (canonical definition)
version: "3.9"

services:
  db:
    image: postgres:16-alpine
    restart: unless-stopped
    environment:
      POSTGRES_DB: weather_db
      POSTGRES_USER: weather_user
      POSTGRES_PASSWORD: weather_pass
    volumes:
      - pg_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U weather_user -d weather_db"]
      interval: 5s
      timeout: 5s
      retries: 10

  backend:
    build: ./backend
    restart: unless-stopped
    environment:
      DATABASE_URL: postgresql://weather_user:weather_pass@db:5432/weather_db
      ALLOWED_ORIGINS: "http://localhost:5173"
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy

  frontend:
    build: ./frontend
    restart: unless-stopped
    environment:
      VITE_API_URL: "http://localhost:8000"
    ports:
      - "5173:5173"
    depends_on:
      - backend

volumes:
  pg_data:
```

### Backend Dockerfile (`./backend/Dockerfile`)
- Base image: `python:3.12-slim`
- Single-stage build
- Runs as non-root user `appuser`
- Installs dependencies from `requirements.txt`
- CMD: `uvicorn app.main:app --host 0.0.0.0 --port 8000` (no `--reload` in production)

### Frontend Dockerfile (`./frontend/Dockerfile`)
- Base image: `node:20-alpine`
- Single-stage build
- Installs dependencies, runs `vite` dev server (or `vite preview` for prod build)
- Exposes port `5173`

---

## Environment Variables

### Backend
| Variable          | Required | Default (dev)                                               | Description                         |
|-------------------|----------|-------------------------------------------------------------|-------------------------------------|
| `DATABASE_URL`    | ✅ Yes   | `postgresql://weather_user:weather_pass@db:5432/weather_db` | PostgreSQL connection string        |
| `ALLOWED_ORIGINS` | ✅ Yes   | `http://localhost:5173`                                     | Comma-separated CORS allowed origins|

### Frontend
| Variable       | Required | Default (dev)            | Description                     |
|----------------|----------|--------------------------|---------------------------------|
| `VITE_API_URL` | ✅ Yes   | `http://localhost:8000`  | Base URL of the FastAPI backend |

### Database (Docker Compose only)
| Variable            | Value          |
|---------------------|----------------|
| `POSTGRES_DB`       | `weather_db`   |
| `POSTGRES_USER`     | `weather_user` |
| `POSTGRES_PASSWORD` | `weather_pass` |

---

## Database Schema

### Table: `cities`

```sql
CREATE TABLE cities (
    id          SERIAL          PRIMARY KEY,
    name        VARCHAR(255)    NOT NULL,
    country     VARCHAR(100)    NOT NULL,
    latitude    DOUBLE PRECISION NOT NULL,
    longitude   DOUBLE PRECISION NOT NULL,
    created_at  TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

-- Unique constraint to prevent duplicate cities
CREATE UNIQUE INDEX uix_cities_name_country_lat_lon
    ON cities (name, country, latitude, longitude);
```

### SQLAlchemy Model (`app/models.py`)

```python
class City(Base):
    __tablename__ = "cities"

    id         : Mapped[int]      # Integer, primary key, autoincrement
    name       : Mapped[str]      # String(255), not null
    country    : Mapped[str]      # String(100), not null
    latitude   : Mapped[float]    # Double precision, not null
    longitude  : Mapped[float]    # Double precision, not null
    created_at : Mapped[datetime] # DateTime(timezone=True), server_default=now()
```

> Schema is applied via `SQLAlchemy Base.metadata.create_all()` on startup (Milestone 1).
> Alembic migrations are introduced in Milestone 2+.

---

## API Endpoints

### Base URL
- Development: `http://localhost:8000`
- Production: Set via `VITE_API_URL` / Render service URL

### `GET /health`
Health check for load balancers and Render deploy checks.

**Response `200 OK`**
```json
{ "status": "ok" }
```

---

### `GET /api/cities`
Returns all saved cities ordered by `created_at ASC`.

**Response `200 OK`**
```json
[
  {
    "id": 1,
    "name": "New York",
    "country": "United States",
    "latitude": 40.7128,
    "longitude": -74.0060,
    "created_at": "2024-01-15T12:00:00Z"
  }
]
```

**Error responses:** none (returns empty array `[]` when no cities saved)

---

### `POST /api/cities`
Adds a new city to the database. Silently ignores duplicates (returns existing record).

**Request Body**
```json
{
  "name": "London",
  "country": "United Kingdom",
  "latitude": 51.5074,
  "longitude": -0.1278
}
```

| Field       | Type   | Required | Description                          |
|-------------|--------|----------|--------------------------------------|
| `name`      | string | ✅       | City name                            |
| `country`   | string | ✅       | Country name (full, e.g. "France")   |
| `latitude`  | float  | ✅       | Decimal latitude  (-90 to 90)        |
| `longitude` | float  | ✅       | Decimal longitude (-180 to 180)      |

**Response `201 Created`** (or `200 OK` if duplicate)
```json
{
  "id": 2,
  "name": "London",
  "country": "United Kingdom",
  "latitude": 51.5074,
  "longitude": -0.1278,
  "created_at": "2024-01-15T12:05:00Z"
}
```

**Error `422 Unprocessable Entity`** — missing or invalid fields (FastAPI default validation)

---

### `DELETE /api/cities/{id}`
Removes a city by its primary key.

**Path Parameters**
| Param | Type | Description     |
|-------|------|-----------------|
| `id`  | int  | City primary key|

**Response `204 No Content`** — success, empty body

**Error `404 Not Found`**
```json
{ "detail": "City not found" }
```

---

### `GET /api/weather/{latitude}/{longitude}`
Fetches current weather conditions from Open-Meteo for the given coordinates.
Results are **not cached** (always fresh from Open-Meteo).

**Path Parameters**
| Param       | Type  | Description           |
|-------------|-------|-----------------------|
| `latitude`  | float | Decimal latitude      |
| `longitude` | float | Decimal longitude     |

**Response `200 OK`**
```json
{
  "temperature_c": 18.4,
  "temperature_f": 65.1,
  "feels_like_c": 16.9,
  "feels_like_f": 62.4,
  "humidity": 72,
  "wind_speed_mph": 11.2,
  "condition": "Partly Cloudy",
  "condition_emoji": "🌤",
  "weather_code": 2,
  "last_updated": "2024-01-15T12:00:00Z"
}
```

| Field             | Type   | Description                                   |
|-------------------|--------|-----------------------------------------------|
| `temperature_c`   | float  | Current temperature in Celsius                |
| `temperature_f`   | float  | Current temperature in Fahrenheit             |
| `feels_like_c`    | float  | Apparent temperature in Celsius               |
| `feels_like_f`    | float  | Apparent temperature in Fahrenheit            |
| `humidity`        | int    | Relative humidity percentage (0–100)          |
| `wind_speed_mph`  | float  | Wind speed in miles per hour                  |
| `condition`       | string | Human-readable weather condition              |
| `condition_emoji` | string | Matching emoji for the condition              |
| `weather_code`    | int    | Raw WMO weather interpretation code           |
| `last_updated`    | string | ISO 8601 timestamp of the Open-Meteo reading  |

**WMO Code → Condition + Emoji Mapping (backend)**
| WMO Codes     | Condition        | Emoji |
|---------------|-----------------|-------|
| 0             | Clear Sky        | ☀️    |
| 1             | Mainly Clear     | 🌤    |
| 2             | Partly Cloudy    | ⛅    |
| 3             | Overcast         | ☁️    |
| 45, 48        | Foggy            | 🌫    |
| 51–67         | Drizzle / Rain   | 🌧    |
| 71–77         | Snow             | ❄️    |
| 80–82         | Rain Showers     | 🌧    |
| 95–99         | Thunderstorm     | ⛈    |

**Error `502 Bad Gateway`** — Open-Meteo unreachable
```json
{ "detail": "Failed to fetch weather data from Open-Meteo" }
```

---

### `GET /api/geocode?q={query}`
Searches cities using Open-Meteo's Geocoding API. Returns up to 5 results.

**Query Parameters**
| Param | Type   | Required | Description                      |
|-------|--------|----------|----------------------------------|
| `q`   | string | ✅       | Search query (min 3 characters)  |

**Response `200 OK`**
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

**Error `400 Bad Request`** — query shorter than 3 characters
```json
{ "detail": "Query must be at least 3 characters" }
```

**Error `502 Bad Gateway`** — Open-Meteo Geocoding unreachable
```json
{ "detail": "Failed to fetch geocoding data from Open-Meteo" }
```

---

## External APIs

### Open-Meteo Weather
- **URL:** `https://api.open-meteo.com/v1/forecast`
- **No API key required**
- **Params used:** `latitude`, `longitude`, `current=temperature_2m,apparent_temperature,relative_humidity_2m,wind_speed_10m,weather_code`, `wind_speed_unit=mph`, `timezone=auto`

### Open-Meteo Geocoding
- **URL:** `https://geocoding-api.open-meteo.com/v1/search`
- **No API key required**
- **Params used:** `name={query}`, `count=5`, `language=en`, `format=json`

---

## Frontend Component Tree

```
src/
├── main.tsx                          # React 18 createRoot entry point
├── App.tsx                           # Root component — two-panel layout shell
│
├── components/
│   ├── layout/
│   │   ├── Sidebar.tsx               # Left panel wrapper (fixed width)
│   │   └── MainContent.tsx           # Right panel wrapper (flex-grow)
│   │
│   ├── sidebar/
│   │   ├── CityTree.tsx              # Scrollable list of CityTreeItem components
│   │   ├── CityTreeItem.tsx          # Single city row: flag, name, live temp; right-click menu
│   │   ├── AddCityButton.tsx         # "＋ Add City" button that opens search
│   │   ├── CitySearch.tsx            # Inline search bar with debounced input
│   │   ├── CitySearchDropdown.tsx    # Dropdown list of up to 5 geocode results
│   │   └── EmptyState.tsx            # "Add a city to get started" illustration
│   │
│   ├── weather/
│   │   ├── WeatherCardGrid.tsx       # Responsive CSS grid wrapper
│   │   ├── WeatherCard.tsx           # Full weather card: all data fields + × button
│   │   ├── WeatherCardSkeleton.tsx   # Loading placeholder matching card dimensions
│   │   └── WeatherIcon.tsx           # Renders condition emoji (memoized)
│   │
│   └── common/
│       ├── ContextMenu.tsx           # Positioned right-click context menu portal
│       └── ErrorBoundary.tsx         # React error boundary for card/sidebar failures
│
├── hooks/
│   ├── useCities.ts                  # GET /api/cities — fetch + mutate city list
│   ├── useAddCity.ts                 # POST /api/cities — optimistic add
│   ├── useRemoveCity.ts              # DELETE /api/cities/{id} — optimistic remove
│   ├── useWeather.ts                 # GET /api/weather/{lat}/{lon} — single city weather
│   ├── useGeocode.ts                 # GET /api/geocode?q= — debounced search
│   └── useAutoRefresh.ts             # 60-second interval trigger for weather re-fetch
│
├── api/
│   └── client.ts                     # Axios (or fetch) base client — reads VITE_API_URL
│
├── types/
│   └── index.ts                      # Shared TypeScript interfaces
│
└── styles/
    └── index.css                     # Tailwind CSS directives (@tailwind base/components/utilities)
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

export interface GeocodingResult {
  name: string;
  country: string;
  latitude: number;
  longitude: number;
  country_code: string;
}

export interface WeatherData {
  temperature_c: number;
  temperature_f: number;
  feels_like_c: number;
  feels_like_f: number;
  humidity: number;
  wind_speed_mph: number;
  condition: string;
  condition_emoji: string;
  weather_code: number;
  last_updated: string;
}

export interface WeatherCardState {
  city: City;
  weather: WeatherData | null;
  loading: boolean;
  error: string | null;
}
```

---

## Data Flow

### Page Load
```
App mounts
  → useCities() → GET /api/cities
  → for each city: useWeather(lat, lon) → GET /api/weather/{lat}/{lon}
  → WeatherCardGrid renders cards; CityTree renders sidebar items
```

### Add City
```
User types in CitySearch (≥3 chars, 300ms debounce)
  → useGeocode() → GET /api/geocode?q={query}
  → CitySearchDropdown renders results
User clicks result
  → useAddCity() → POST /api/cities
  → optimistic update: city added to local state
  → new useWeather() subscription created
  → CitySearch closes
```

### Remove City
```
User clicks × on WeatherCard OR right-click → Remove in CityTreeItem
  → useRemoveCity(id) → DELETE /api/cities/{id}
  → optimistic update: city removed from local state
  → WeatherCard animates out (fade + slide down, 200ms)
  → CityTreeItem simultaneously removed
```

### Auto-Refresh
```
useAutoRefresh(60_000)
  → fires every 60 seconds
  → invalidates weather query cache for all active cities
  → each useWeather() re-fetches from GET /api/weather/{lat}/{lon}
  → cards update in place (no layout shift)
```

---

## Deployment (Render)

### `render.yaml` Services

```yaml
services:
  - type: web
    name: weather-backend
    runtime: docker
    dockerfilePath: ./backend/Dockerfile
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: weather-postgres
          property: connectionString
      - key: ALLOWED_ORIGINS
        value: "https://weather-frontend.onrender.com"

  - type: web
    name: weather-frontend
    runtime: docker
    dockerfilePath: ./frontend/Dockerfile
    envVars:
      - key: VITE_API_URL
        value: "https://weather-backend.onrender.com"

databases:
  - name: weather-postgres
    databaseName: weather_db
    user: weather_user
    plan: free
```

### Production Checklist
- [ ] `DATABASE_URL` injected by Render managed PostgreSQL
- [ ] `VITE_API_URL` points to backend Render URL
- [ ] `ALLOWED_ORIGINS` includes frontend Render URL
- [ ] Uvicorn started without `--reload`
- [ ] Backend runs as non-root `appuser`
- [ ] Frontend served via `nginx` or `vite preview`
