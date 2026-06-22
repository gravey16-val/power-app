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
┌─────────────────────────────────────────────────────────────────┐
│                        Docker Compose                           │
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐  │
│  │   frontend   │    │   backend    │    │       db         │  │
│  │  (Vite/React)│───▶│  (FastAPI)   │───▶│  (PostgreSQL 16) │  │
│  │  Port: 5173  │    │  Port: 8000  │    │   Port: 5432     │  │
│  └──────────────┘    └──────┬───────┘    └──────────────────┘  │
│                             │                                   │
│                             ▼                                   │
│                   ┌──────────────────┐                         │
│                   │  Open-Meteo API  │                         │
│                   │  (external, free)│                         │
│                   └──────────────────┘                         │
└─────────────────────────────────────────────────────────────────┘
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
      - postgres_data:/var/lib/postgresql/data
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
    volumes:
      - ./backend:/app

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
      - ./frontend:/app
      - /app/node_modules

volumes:
  postgres_data:
```

### `backend/Dockerfile` (single-stage)

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chown -R appuser:appgroup /app
USER appuser

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### `frontend/Dockerfile` (single-stage)

```dockerfile
FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
```

---

## Environment Variables

### Backend

| Variable       | Description                              | Default (dev)                                        |
|----------------|------------------------------------------|------------------------------------------------------|
| `DATABASE_URL` | PostgreSQL connection string (SQLAlchemy) | `postgresql://weather:weather@db:5432/weatherdb`    |
| `PYTHONUNBUFFERED` | Force stdout/stderr flush            | `1`                                                  |

### Frontend

| Variable        | Description                          | Default (dev)               |
|-----------------|--------------------------------------|-----------------------------|
| `VITE_API_URL`  | Base URL of the FastAPI backend      | `http://localhost:8000`     |

### PostgreSQL Service

| Variable            | Value      |
|---------------------|------------|
| `POSTGRES_USER`     | `weather`  |
| `POSTGRES_PASSWORD` | `weather`  |
| `POSTGRES_DB`       | `weatherdb`|

---

## Database Schema

### Table: `cities`

```sql
CREATE TABLE cities (
    id          SERIAL          PRIMARY KEY,
    name        VARCHAR(255)    NOT NULL,
    country     VARCHAR(255)    NOT NULL,
    latitude    DOUBLE PRECISION NOT NULL,
    longitude   DOUBLE PRECISION NOT NULL,
    created_at  TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Prevent duplicate city entries by coordinates
CREATE UNIQUE INDEX uq_cities_lat_lon
    ON cities (latitude, longitude);
```

| Column      | Type                        | Constraints                        |
|-------------|-----------------------------|------------------------------------|
| `id`        | `SERIAL`                    | PRIMARY KEY                        |
| `name`      | `VARCHAR(255)`              | NOT NULL                           |
| `country`   | `VARCHAR(255)`              | NOT NULL                           |
| `latitude`  | `DOUBLE PRECISION`          | NOT NULL                           |
| `longitude` | `DOUBLE PRECISION`          | NOT NULL                           |
| `created_at`| `TIMESTAMP WITH TIME ZONE`  | NOT NULL, DEFAULT `now()`          |

**SQLAlchemy Model** (`backend/app/models.py`):
```python
class City(Base):
    __tablename__ = "cities"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    name       = Column(String(255), nullable=False)
    country    = Column(String(255), nullable=False)
    latitude   = Column(Float, nullable=False)
    longitude  = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("latitude", "longitude", name="uq_cities_lat_lon"),
    )
```

Schema is applied at startup via `Base.metadata.create_all(bind=engine)` in `app/main.py`.

---

## API Endpoints

Base URL (dev): `http://localhost:8000`

### `GET /health`
Health check.

**Response `200 OK`:**
```json
{ "status": "ok" }
```

---

### `GET /api/cities`
Return all saved cities ordered by `created_at ASC`.

**Response `200 OK`:**
```json
[
  {
    "id": 1,
    "name": "New York",
    "country": "United States",
    "latitude": 40.7128,
    "longitude": -74.006,
    "created_at": "2024-06-01T12:00:00Z"
  }
]
```

---

### `POST /api/cities`
Add a new city. Silently returns the existing record if coordinates already exist (duplicate guard).

**Request Body:**
```json
{
  "name": "New York",
  "country": "United States",
  "latitude": 40.7128,
  "longitude": -74.006
}
```

| Field       | Type    | Required | Notes                          |
|-------------|---------|----------|--------------------------------|
| `name`      | string  | ✅       | City display name              |
| `country`   | string  | ✅       | Country display name           |
| `latitude`  | float   | ✅       | Decimal degrees                |
| `longitude` | float   | ✅       | Decimal degrees                |

**Response `201 Created`:**
```json
{
  "id": 1,
  "name": "New York",
  "country": "United States",
  "latitude": 40.7128,
  "longitude": -74.006,
  "created_at": "2024-06-01T12:00:00Z"
}
```

**Response `200 OK`** (duplicate — city already exists, return existing record):
```json
{
  "id": 1,
  "name": "New York",
  "country": "United States",
  "latitude": 40.7128,
  "longitude": -74.006,
  "created_at": "2024-06-01T12:00:00Z"
}
```

---

### `DELETE /api/cities/{id}`
Remove a city by ID.

**Path Parameter:**

| Param | Type    | Description       |
|-------|---------|-------------------|
| `id`  | integer | City primary key  |

**Response `204 No Content`** — on success (empty body).

**Response `404 Not Found`:**
```json
{ "detail": "City not found" }
```

---

### `GET /api/weather/{latitude}/{longitude}`
Fetch current weather from the Open-Meteo API for the given coordinates.

**Path Parameters:**

| Param       | Type  | Description      |
|-------------|-------|------------------|
| `latitude`  | float | Decimal degrees  |
| `longitude` | float | Decimal degrees  |

**Response `200 OK`:**
```json
{
  "temperature_c": 22.5,
  "temperature_f": 72.5,
  "feels_like_c": 21.0,
  "feels_like_f": 69.8,
  "humidity": 58,
  "wind_speed_mph": 12.4,
  "condition": "Partly Cloudy",
  "condition_emoji": "🌤",
  "last_updated": "2024-06-01T12:45:00Z"
}
```

| Field            | Type    | Description                                          |
|------------------|---------|------------------------------------------------------|
| `temperature_c`  | float   | Current temperature in Celsius                       |
| `temperature_f`  | float   | Current temperature in Fahrenheit                    |
| `feels_like_c`   | float   | Apparent temperature in Celsius                      |
| `feels_like_f`   | float   | Apparent temperature in Fahrenheit                   |
| `humidity`       | integer | Relative humidity %                                  |
| `wind_speed_mph` | float   | Wind speed in mph                                    |
| `condition`      | string  | Human-readable weather condition                     |
| `condition_emoji`| string  | Emoji icon matching condition                        |
| `last_updated`   | string  | ISO 8601 UTC timestamp of data retrieval             |

**Response `502 Bad Gateway`** — if Open-Meteo is unreachable:
```json
{ "detail": "Failed to fetch weather data from upstream provider" }
```

---

### `GET /api/geocode?q={query}`
Search for cities via Open-Meteo Geocoding API. Returns up to 5 results.

**Query Parameter:**

| Param | Type   | Required | Notes                          |
|-------|--------|----------|--------------------------------|
| `q`   | string | ✅       | Search string (min 3 chars)    |

**Response `200 OK`:**
```json
[
  {
    "name": "New York",
    "country": "United States",
    "latitude": 40.7128,
    "longitude": -74.006
  },
  {
    "name": "New Orleans",
    "country": "United States",
    "latitude": 29.9511,
    "longitude": -90.0715
  }
]
```

**Response `400 Bad Request`** — query shorter than 3 characters:
```json
{ "detail": "Query must be at least 3 characters" }
```

**Response `502 Bad Gateway`** — if Open-Meteo Geocoding is unreachable:
```json
{ "detail": "Failed to fetch geocoding data from upstream provider" }
```

---

## Frontend Component Tree

```
App
├── AppProvider  (React Context: cities state, weather state, loading, actions)
│
├── Layout
│   ├── Sidebar
│   │   ├── AddCityButton
│   │   ├── CitySearch          (inline search bar, shown conditionally)
│   │   │   ├── SearchInput     (debounced, 300ms)
│   │   │   └── SearchDropdown
│   │   │       └── SearchResultItem  (× N, up to 5)
│   │   ├── CityTreeView
│   │   │   ├── CityTreeItem    (× N — name, flag emoji, live temp)
│   │   │   │   └── ContextMenu (right-click → Remove)
│   │   │   └── EmptyState      (shown when cities list is empty)
│   │   └── [EmptyState arrow hint]
│   │
│   └── MainContent
│       ├── WeatherCardGrid     (responsive: 1/2/3 cols)
│       │   ├── WeatherCard     (× N — full weather data)
│       │   │   ├── CardHeader  (city name, country, × remove button)
│       │   │   ├── TempDisplay (°C and °F, feels like)
│       │   │   ├── ConditionDisplay (emoji + label)
│       │   │   ├── WeatherStats     (humidity, wind speed)
│       │   │   └── LastUpdated      (timestamp)
│       │   └── WeatherCardSkeleton (× N — loading placeholder)
│       └── EmptyState          (shown when no cities saved)
│
└── Toast / Notification        (optional: ephemeral feedback)
```

### Key Frontend Files

```
frontend/
├── src/
│   ├── main.tsx                  # React entry point
│   ├── App.tsx                   # Root component, AppProvider wrapper
│   ├── context/
│   │   └── AppContext.tsx        # Global state: cities[], weather map, actions
│   ├── api/
│   │   └── client.ts             # All fetch() calls to backend (typed)
│   ├── hooks/
│   │   ├── useCities.ts          # CRUD operations against /api/cities
│   │   ├── useWeather.ts         # Fetch + auto-refresh (60s) weather data
│   │   └── useGeocode.ts         # Debounced geocoding search hook
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Layout.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   └── MainContent.tsx
│   │   ├── sidebar/
│   │   │   ├── AddCityButton.tsx
│   │   │   ├── CitySearch.tsx
│   │   │   ├── SearchInput.tsx
│   │   │   ├── SearchDropdown.tsx
│   │   │   ├── SearchResultItem.tsx
│   │   │   ├── CityTreeView.tsx
│   │   │   ├── CityTreeItem.tsx
│   │   │   ├── ContextMenu.tsx
│   │   │   └── EmptyState.tsx
│   │   └── weather/
│   │       ├── WeatherCardGrid.tsx
│   │       ├── WeatherCard.tsx
│   │       ├── WeatherCardSkeleton.tsx
│   │       ├── CardHeader.tsx
│   │       ├── TempDisplay.tsx
│   │       ├── ConditionDisplay.tsx
│   │       ├── WeatherStats.tsx
│   │       └── LastUpdated.tsx
│   ├── types/
│   │   └── index.ts              # City, WeatherData, GeoResult interfaces
│   └── utils/
│       └── weatherConditions.ts  # WMO code → condition string + emoji map
├── index.html
├── vite.config.ts
├── tailwind.config.ts
├── tsconfig.json
└── package.json
```

### Backend File Structure

```
backend/
├── app/
│   ├── main.py           # FastAPI app init, startup (create_all), router mounts
│   ├── database.py       # SQLAlchemy engine, SessionLocal, Base
│   ├── models.py         # City ORM model
│   ├── schemas.py        # Pydantic schemas: CityCreate, CityResponse, WeatherResponse, GeoResult
│   ├── routers/
│   │   ├── cities.py     # GET/POST /api/cities, DELETE /api/cities/{id}
│   │   ├── weather.py    # GET /api/weather/{latitude}/{longitude}
│   │   └── geocode.py    # GET /api/geocode
│   └── services/
│       ├── weather.py    # Open-Meteo API call + WMO code mapping logic
│       └── geocode.py    # Open-Meteo Geocoding API call
├── tests/
│   ├── conftest.py       # pytest fixtures: test DB, TestClient
│   ├── test_health.py
│   ├── test_cities.py
│   ├── test_weather.py
│   └── test_geocode.py
├── requirements.txt
└── Dockerfile
```

---

## Data Flow

### Page Load
```
Browser → GET /api/cities → backend → PostgreSQL
       ← [cities array]
Browser → GET /api/weather/{lat}/{lon} (for each city, parallel)
       ← [weather data per city]
```

### Add City
```
User types (≥3 chars, 300ms debounce)
→ GET /api/geocode?q={query}
← [up to 5 GeoResult]
User selects result
→ POST /api/cities {name, country, lat, lon}
← CityResponse (201 or 200)
→ GET /api/weather/{lat}/{lon}
← WeatherData
→ UI updates: tree view + card grid
```

### Remove City
```
User clicks × or right-click → Remove
→ DELETE /api/cities/{id}
← 204 No Content
→ UI removes card (fade+slide-down 200ms) + tree item simultaneously
```

### Auto-refresh
```
Every 60 seconds (setInterval in useWeather hook):
→ GET /api/weather/{lat}/{lon} for all visible cities (parallel)
← Updated WeatherData per city
→ Cards re-render with fresh data + updated timestamp
```

---

## Deployment (Render)

### `render.yaml`

```yaml
services:
  - type: web
    name: weather-backend
    env: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "uvicorn app.main:app --host 0.0.0.0 --port 10000"
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: weather-db
          property: connectionString

  - type: web
    name: weather-frontend
    env: static
    buildCommand: "npm ci && npm run build"
    staticPublishPath: "./dist"
    envVars:
      - key: VITE_API_URL
        value: https://weather-backend.onrender.com

databases:
  - name: weather-db
    databaseName: weatherdb
    user: weather
    plan: free
```

### Required Environment Variables on Render

| Service   | Variable        | Source                       |
|-----------|-----------------|------------------------------|
| Backend   | `DATABASE_URL`  | Render managed PostgreSQL    |
| Frontend  | `VITE_API_URL`  | Backend web service URL      |
