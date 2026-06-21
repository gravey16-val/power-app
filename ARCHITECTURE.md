# ARCHITECTURE.md — Weather Dashboard

## Table of Contents
1. [System Overview](#system-overview)
2. [Docker Services](#docker-services)
3. [Environment Variables](#environment-variables)
4. [Database Schema](#database-schema)
5. [API Endpoints](#api-endpoints)
6. [Frontend Component Tree](#frontend-component-tree)
7. [Data Flow](#data-flow)
8. [Render Deployment](#render-deployment)

---

## System Overview

```
┌─────────────────────────────────────────────────────────┐
│                     Docker Compose                       │
│                                                         │
│  ┌──────────────┐   ┌──────────────┐   ┌────────────┐  │
│  │   frontend   │   │   backend    │   │     db     │  │
│  │  (Vite/React)│──▶│  (FastAPI)   │──▶│ (Postgres) │  │
│  │   Port 5173  │   │   Port 8000  │   │  Port 5432 │  │
│  └──────────────┘   └──────┬───────┘   └────────────┘  │
│                             │                           │
│                             ▼                           │
│                    Open-Meteo APIs                      │
│               (Weather + Geocoding — no key)            │
└─────────────────────────────────────────────────────────┘
```

The app is a two-panel weather dashboard:
- **Left panel:** City tree view sidebar (search, add, remove cities; live temps)
- **Right panel:** Weather card grid (full weather data, auto-refresh 60s)
- **Backend:** FastAPI proxies Open-Meteo calls and persists city list in PostgreSQL
- **No auth:** Single shared city list, session-agnostic

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
  pg_data:
```

### Service Definitions

| Service    | Base Image              | Port  | Role                                      |
|------------|-------------------------|-------|-------------------------------------------|
| `db`       | `postgres:16-alpine`    | 5432  | PostgreSQL 16 — persists city list        |
| `backend`  | `python:3.12-slim`      | 8000  | FastAPI + SQLAlchemy — REST API + proxy   |
| `frontend` | `node:20-alpine`        | 5173  | Vite dev server — React 18 + TypeScript   |

### Backend `Dockerfile` (single-stage)

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

### Frontend `Dockerfile` (single-stage)

```dockerfile
FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
```

---

## Environment Variables

### Backend

| Variable       | Required | Default (dev)                                        | Description                          |
|----------------|----------|------------------------------------------------------|--------------------------------------|
| `DATABASE_URL` | ✅ Yes   | `postgresql://weather:weather@db:5432/weatherdb`     | PostgreSQL connection string         |
| `PYTHONUNBUFFERED` | No   | `1`                                                  | Unbuffered Python stdout             |

### Frontend

| Variable       | Required | Default (dev)             | Description                          |
|----------------|----------|---------------------------|--------------------------------------|
| `VITE_API_URL` | ✅ Yes   | `http://localhost:8000`   | Base URL of the FastAPI backend      |

> **Note:** All env vars are supplied via `docker-compose.yml` for local dev and via Render service environment for production. No `.env` files are required to start the stack.

---

## Database Schema

### PostgreSQL 16 — Database: `weatherdb`

#### Table: `cities`

```sql
CREATE TABLE cities (
    id          SERIAL          PRIMARY KEY,
    name        VARCHAR(255)    NOT NULL,
    country     VARCHAR(100)    NOT NULL,
    latitude    DOUBLE PRECISION NOT NULL,
    longitude   DOUBLE PRECISION NOT NULL,
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Prevent duplicate city entries by coordinates (rounded to 2 decimal places)
CREATE UNIQUE INDEX cities_lat_lon_unique
    ON cities (ROUND(latitude::numeric, 2), ROUND(longitude::numeric, 2));
```

#### SQLAlchemy Model (`backend/app/models.py`)

```python
class City(Base):
    __tablename__ = "cities"

    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String(255), nullable=False)
    country    = Column(String(100), nullable=False)
    latitude   = Column(Float, nullable=False)
    longitude  = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
```

#### Schema Initialization

Tables are created on backend startup via `Base.metadata.create_all(bind=engine)` in `app/main.py`. No external migration tool is required for the current scope (Alembic can be added later).

---

## API Endpoints

Base URL (local): `http://localhost:8000`

All endpoints return `Content-Type: application/json`. Errors follow the shape:
```json
{ "detail": "<error message>" }
```

---

### `GET /health`

Health check. Used by Docker and Render to verify service liveness.

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
    "name": "New York",
    "country": "United States",
    "latitude": 40.71,
    "longitude": -74.01,
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```

---

### `POST /api/cities`

Add a new city. Silently ignores duplicates (returns the existing record).

**Request Body**
```json
{
  "name": "New York",
  "country": "United States",
  "latitude": 40.7128,
  "longitude": -74.0060
}
```

| Field       | Type    | Required | Description                        |
|-------------|---------|----------|------------------------------------|
| `name`      | string  | ✅       | City name                          |
| `country`   | string  | ✅       | Country full name                  |
| `latitude`  | float   | ✅       | Decimal latitude (-90 to 90)       |
| `longitude` | float   | ✅       | Decimal longitude (-180 to 180)    |

**Response `201 Created`**
```json
{
  "id": 1,
  "name": "New York",
  "country": "United States",
  "latitude": 40.7128,
  "longitude": -74.0060,
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Response `200 OK`** (duplicate — existing record returned silently)

**Response `422 Unprocessable Entity`** — validation error

---

### `DELETE /api/cities/{id}`

Remove a city by ID.

**Path Parameters**

| Parameter | Type    | Description       |
|-----------|---------|-------------------|
| `id`      | integer | City's primary key |

**Response `204 No Content`** — city deleted

**Response `404 Not Found`**
```json
{ "detail": "City not found" }
```

---

### `GET /api/weather/{latitude}/{longitude}`

Fetch current weather conditions from Open-Meteo for the given coordinates. The backend proxies this call to avoid CORS issues and to cache/shape the response.

**Path Parameters**

| Parameter   | Type  | Example  | Description          |
|-------------|-------|----------|----------------------|
| `latitude`  | float | `40.71`  | Decimal latitude     |
| `longitude` | float | `-74.01` | Decimal longitude    |

**Upstream call (Open-Meteo):**
```
GET https://api.open-meteo.com/v1/forecast
  ?latitude={lat}
  &longitude={lon}
  &current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m
  &temperature_unit=celsius
  &wind_speed_unit=mph
  &timezone=auto
```

**Response `200 OK`**
```json
{
  "temperature_c": 22.5,
  "temperature_f": 72.5,
  "feels_like_c": 21.0,
  "feels_like_f": 69.8,
  "humidity": 65,
  "wind_speed_mph": 12.3,
  "weather_code": 2,
  "weather_condition": "Partly Cloudy",
  "weather_emoji": "🌤",
  "last_updated": "2024-01-15T10:45:00Z"
}
```

| Field               | Type    | Description                              |
|---------------------|---------|------------------------------------------|
| `temperature_c`     | float   | Current temp in Celsius                  |
| `temperature_f`     | float   | Current temp in Fahrenheit               |
| `feels_like_c`      | float   | Apparent temp in Celsius                 |
| `feels_like_f`      | float   | Apparent temp in Fahrenheit              |
| `humidity`          | integer | Relative humidity %                      |
| `wind_speed_mph`    | float   | Wind speed in mph                        |
| `weather_code`      | integer | WMO weather interpretation code          |
| `weather_condition` | string  | Human-readable condition label           |
| `weather_emoji`     | string  | Matching emoji (☀️ 🌤 ⛅ 🌧 ❄️ ⛈ 🌫)  |
| `last_updated`      | string  | ISO 8601 timestamp of the observation    |

**WMO Code → Emoji/Condition Mapping (backend utility)**

| WMO Codes    | Condition         | Emoji |
|--------------|-------------------|-------|
| 0            | Clear Sky         | ☀️    |
| 1, 2         | Partly Cloudy     | 🌤    |
| 3            | Overcast          | ⛅    |
| 45, 48       | Foggy             | 🌫    |
| 51–67        | Drizzle/Rain      | 🌧    |
| 71–77        | Snow              | ❄️    |
| 80–82        | Rain Showers      | 🌧    |
| 85, 86       | Snow Showers      | ❄️    |
| 95–99        | Thunderstorm      | ⛈    |

**Response `502 Bad Gateway`** — upstream Open-Meteo call failed

---

### `GET /api/geocode?q={query}`

Search for cities by name via Open-Meteo Geocoding API.

**Query Parameters**

| Parameter | Type   | Required | Description                          |
|-----------|--------|----------|--------------------------------------|
| `q`       | string | ✅       | City search term (minimum 3 chars)   |

**Upstream call (Open-Meteo Geocoding):**
```
GET https://geocoding-api.open-meteo.com/v1/search
  ?name={q}
  &count=5
  &language=en
  &format=json
```

**Response `200 OK`**
```json
[
  {
    "name": "New York",
    "country": "United States",
    "latitude": 40.7128,
    "longitude": -74.0060,
    "display": "New York, United States"
  },
  {
    "name": "New York Mills",
    "country": "United States",
    "latitude": 43.1048,
    "longitude": -75.2910,
    "display": "New York Mills, United States"
  }
]
```

**Response `400 Bad Request`** — `q` is missing or fewer than 3 characters
```json
{ "detail": "Query must be at least 3 characters" }
```

**Response `200 OK`** with `[]` — no results found

**Response `502 Bad Gateway`** — upstream geocoding call failed

---

## Frontend Component Tree

```
App (app/App.tsx)
├── AppProvider (context/AppContext.tsx)        # Global state: cities[], loading, error
│
└── Layout (components/Layout.tsx)             # flex row, full-height
    ├── Sidebar (components/Sidebar/Sidebar.tsx)
    │   ├── AddCityButton (components/Sidebar/AddCityButton.tsx)
    │   │   └── SearchInput (components/Sidebar/SearchInput.tsx)
    │   │       └── GeocodeDropdown (components/Sidebar/GeocodeDropdown.tsx)
    │   │           └── GeocodeDropdownItem (components/Sidebar/GeocodeDropdownItem.tsx)
    │   ├── CityTree (components/Sidebar/CityTree.tsx)
    │   │   └── CityTreeItem (components/Sidebar/CityTreeItem.tsx)
    │   │       └── ContextMenu (components/Sidebar/ContextMenu.tsx)
    │   └── EmptyState (components/Sidebar/EmptyState.tsx)
    │
    └── MainPanel (components/MainPanel/MainPanel.tsx)
        ├── WeatherGrid (components/MainPanel/WeatherGrid.tsx)
        │   └── WeatherCard (components/MainPanel/WeatherCard.tsx)  [× N cities]
        │       ├── WeatherCardSkeleton (components/MainPanel/WeatherCardSkeleton.tsx)
        │       └── WeatherIcon (components/MainPanel/WeatherIcon.tsx)
        └── EmptyState (components/Sidebar/EmptyState.tsx)          [reused]
```

### State Management

All state lives in `AppContext` (React Context + `useReducer`). No external state library.

```typescript
// context/AppContext.tsx

interface City {
  id: number;
  name: string;
  country: string;
  latitude: number;
  longitude: number;
  created_at: string;
}

interface WeatherData {
  temperature_c: number;
  temperature_f: number;
  feels_like_c: number;
  feels_like_f: number;
  humidity: number;
  wind_speed_mph: number;
  weather_code: number;
  weather_condition: string;
  weather_emoji: string;
  last_updated: string;
}

interface AppState {
  cities: City[];
  weather: Record<number, WeatherData | null>;   // keyed by city.id
  weatherLoading: Record<number, boolean>;        // keyed by city.id
  isSearchOpen: boolean;
  geocodeResults: GeocodeResult[];
  geocodeLoading: boolean;
}

type AppAction =
  | { type: "SET_CITIES"; payload: City[] }
  | { type: "ADD_CITY"; payload: City }
  | { type: "REMOVE_CITY"; payload: number }         // city id
  | { type: "SET_WEATHER"; payload: { cityId: number; data: WeatherData } }
  | { type: "SET_WEATHER_LOADING"; payload: { cityId: number; loading: boolean } }
  | { type: "SET_SEARCH_OPEN"; payload: boolean }
  | { type: "SET_GEOCODE_RESULTS"; payload: GeocodeResult[] }
  | { type: "SET_GEOCODE_LOADING"; payload: boolean };
```

### API Client (`frontend/src/api/client.ts`)

```typescript
const BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export const api = {
  getCities():                  Promise<City[]>
  addCity(payload):             Promise<City>
  deleteCity(id: number):       Promise<void>
  getWeather(lat, lon):         Promise<WeatherData>
  geocode(query: string):       Promise<GeocodeResult[]>
}
```

### Key Custom Hooks

| Hook                     | File                               | Purpose                                           |
|--------------------------|------------------------------------|---------------------------------------------------|
| `useWeatherRefresh`      | `hooks/useWeatherRefresh.ts`       | Polls weather for all cities every 60s            |
| `useGeocodeSearch`       | `hooks/useGeocodeSearch.ts`        | Debounced (300ms) geocode API calls               |
| `useContextMenu`         | `hooks/useContextMenu.ts`          | Right-click position tracking + outside-click close |
| `useAnimatedList`        | `hooks/useAnimatedList.ts`         | Tracks add/remove animation state per city id     |

---

## Data Flow

### Page Load
```
App mount
  → AppContext init
  → GET /api/cities
  → SET_CITIES
  → for each city: GET /api/weather/{lat}/{lon}
  → SET_WEATHER per city
  → render Sidebar + WeatherGrid
```

### Add City
```
User types ≥3 chars in SearchInput
  → debounce 300ms
  → GET /api/geocode?q={query}
  → render GeocodeDropdown
User clicks result
  → POST /api/cities {name, country, lat, lon}
  → ADD_CITY (optimistic UI update)
  → GET /api/weather/{lat}/{lon}
  → SET_WEATHER
  → animate card in (fade + slide up)
  → close search
```

### Remove City
```
User clicks × on card  OR  right-click → Remove in tree
  → animate out (fade + slide down, 200ms)
  → DELETE /api/cities/{id}
  → REMOVE_CITY (remove from state)
  → card and tree item disappear simultaneously
```

### Auto-Refresh
```
useWeatherRefresh (setInterval 60000ms)
  → for each city in state: GET /api/weather/{lat}/{lon}
  → SET_WEATHER per city
  → last_updated timestamp updates on card
```

---

## Render Deployment

### `render.yaml`

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
    healthCheckPath: /health

  - type: web
    name: weather-frontend
    runtime: docker
    dockerfilePath: ./frontend/Dockerfile
    envVars:
      - key: VITE_API_URL
        value: https://weather-backend.onrender.com

databases:
  - name: weather-postgres
    databaseName: weatherdb
    user: weather
    plan: free
```

> For production, the backend Dockerfile CMD must **not** include `--reload`. The frontend Dockerfile for production should run `npm run build && npx serve dist` or use an nginx image to serve static files.

---

## Project Directory Layout

```
weather-dashboard/
├── docker-compose.yml
├── render.yaml
├── README.md
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py              # FastAPI app, startup, CORS
│       ├── models.py            # SQLAlchemy City model
│       ├── database.py          # engine, SessionLocal, Base
│       ├── schemas.py           # Pydantic request/response models
│       ├── routers/
│       │   ├── cities.py        # GET/POST/DELETE /api/cities
│       │   ├── weather.py       # GET /api/weather/{lat}/{lon}
│       │   └── geocode.py       # GET /api/geocode
│       └── utils/
│           └── weather_codes.py # WMO code → condition/emoji map
│
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── tsconfig.json
    ├── vite.config.ts
    ├── tailwind.config.ts
    ├── index.html
    └── src/
        ├── main.tsx
        ├── App.tsx
        ├── api/
        │   └── client.ts
        ├── context/
        │   └── AppContext.tsx
        ├── hooks/
        │   ├── useWeatherRefresh.ts
        │   ├── useGeocodeSearch.ts
        │   ├── useContextMenu.ts
        │   └── useAnimatedList.ts
        ├── components/
        │   ├── Layout.tsx
        │   ├── Sidebar/
        │   │   ├── Sidebar.tsx
        │   │   ├── AddCityButton.tsx
        │   │   ├── SearchInput.tsx
        │   │   ├── GeocodeDropdown.tsx
        │   │   ├── GeocodeDropdownItem.tsx
        │   │   ├── CityTree.tsx
        │   │   ├── CityTreeItem.tsx
        │   │   ├── ContextMenu.tsx
        │   │   └── EmptyState.tsx
        │   └── MainPanel/
        │       ├── MainPanel.tsx
        │       ├── WeatherGrid.tsx
        │       ├── WeatherCard.tsx
        │       ├── WeatherCardSkeleton.tsx
        │       └── WeatherIcon.tsx
        └── tests/
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
