# ARCHITECTURE.md — Weather Dashboard: Real-time City Weather Tracker

---

## Table of Contents
1. [System Overview](#system-overview)
2. [Component Tree](#component-tree)
3. [Database Schema](#database-schema)
4. [API Endpoints](#api-endpoints)
5. [Docker Service Definitions](#docker-service-definitions)
6. [Environment Variables](#environment-variables)
7. [External Integrations](#external-integrations)
8. [Data Flow](#data-flow)

---

## System Overview

The Weather Dashboard is a fully containerized, three-tier web application:

```
┌─────────────────────────────────────────────────────────┐
│                     Docker Compose                       │
│                                                         │
│  ┌──────────────┐   ┌──────────────┐   ┌─────────────┐ │
│  │   frontend   │   │   backend    │   │     db      │ │
│  │  React/Vite  │──▶│   FastAPI    │──▶│ PostgreSQL  │ │
│  │  Port 5173   │   │  Port 8000   │   │  Port 5432  │ │
│  └──────────────┘   └──────┬───────┘   └─────────────┘ │
│                             │                           │
└─────────────────────────────┼───────────────────────────┘
                              │ HTTP
                    ┌─────────▼──────────┐
                    │   Open-Meteo APIs  │
                    │  (Weather + Geo)   │
                    └────────────────────┘
```

---

## Component Tree

```
App
├── AppProvider                         # React context: cities state, add/remove actions
│   └── Layout
│       ├── Sidebar                     # Left panel (fixed width, full height)
│       │   ├── AddCityButton           # Triggers inline search mode
│       │   ├── CitySearch              # Inline search input + autocomplete dropdown
│       │   │   └── CitySearchResult   # Individual autocomplete result row
│       │   ├── CityTreeView            # Scrollable list of saved cities
│       │   │   ├── CityTreeItem        # Single city row (name, flag, live temp)
│       │   │   │   └── ContextMenu     # Right-click Remove menu
│       │   │   └── EmptyState          # "Add a city to get started" with arrow
│       │   └── SidebarSkeleton         # Skeleton loader for initial city fetch
│       └── MainGrid                    # Right panel
│           ├── WeatherCardGrid         # Responsive CSS grid wrapper
│           │   ├── WeatherCard         # Full weather card for one city
│           │   │   ├── CardHeader      # City name, country, remove (×) button
│           │   │   ├── WeatherIcon     # Emoji icon mapped from WMO code
│           │   │   ├── TemperatureDisplay  # °F and °C
│           │   │   ├── WeatherDetails  # Humidity, wind speed, feels like
│           │   │   └── LastUpdated     # Timestamp
│           │   └── WeatherCardSkeleton # Skeleton shown while fetching
│           └── EmptyGridState          # Shown when no cities saved
│
├── hooks/
│   ├── useCities.ts                    # Fetch/add/remove cities from backend
│   ├── useWeather.ts                   # Fetch weather for a lat/lon; auto-refresh 60s
│   ├── useGeocode.ts                   # Debounced geocoding search (300ms)
│   └── useContextMenu.ts               # Right-click context menu position/state
│
├── api/
│   └── client.ts                       # Axios/fetch wrapper; reads VITE_API_URL
│
└── types/
    └── index.ts                        # Shared TypeScript interfaces
```

---

## Database Schema

### PostgreSQL 16 — Database: `weather_dashboard`

#### Table: `cities`

| Column       | Type                        | Constraints                        | Notes                              |
|--------------|-----------------------------|------------------------------------|------------------------------------|
| `id`         | `SERIAL`                    | `PRIMARY KEY`                      | Auto-incrementing integer PK       |
| `name`       | `VARCHAR(255)`              | `NOT NULL`                         | City display name (e.g. "Paris")   |
| `country`    | `VARCHAR(255)`              | `NOT NULL`                         | Country name (e.g. "France")       |
| `latitude`   | `DOUBLE PRECISION`          | `NOT NULL`                         | Decimal degrees, from geocoding    |
| `longitude`  | `DOUBLE PRECISION`          | `NOT NULL`                         | Decimal degrees, from geocoding    |
| `created_at` | `TIMESTAMP WITH TIME ZONE`  | `NOT NULL`, `DEFAULT NOW()`        | UTC insertion timestamp            |

**Indexes:**
- `PRIMARY KEY` on `id`
- `UNIQUE INDEX` on `(name, country)` — prevents duplicate city entries

**DDL (executed via SQLAlchemy `Base.metadata.create_all`):**
```sql
CREATE TABLE IF NOT EXISTS cities (
    id         SERIAL PRIMARY KEY,
    name       VARCHAR(255)             NOT NULL,
    country    VARCHAR(255)             NOT NULL,
    latitude   DOUBLE PRECISION         NOT NULL,
    longitude  DOUBLE PRECISION         NOT NULL,
    created_at TIMESTAMPTZ              NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_cities_name_country UNIQUE (name, country)
);
```

---

## API Endpoints

**Base URL (local):** `http://localhost:8000`
**Content-Type:** `application/json` for all request/response bodies

---

### `GET /health`
Health check — confirms the API is running.

**Request:** none

**Response `200 OK`:**
```json
{
  "status": "ok"
}
```

---

### `GET /api/cities`
Return all saved cities, ordered by `created_at` ascending.

**Request:** none

**Response `200 OK`:**
```json
[
  {
    "id": 1,
    "name": "Paris",
    "country": "France",
    "latitude": 48.8566,
    "longitude": 2.3522,
    "created_at": "2024-06-01T12:00:00Z"
  }
]
```

---

### `POST /api/cities`
Add a new city. Silently ignores duplicates (returns existing record).

**Request Body:**
```json
{
  "name": "Paris",
  "country": "France",
  "latitude": 48.8566,
  "longitude": 2.3522
}
```

| Field       | Type     | Required | Description                        |
|-------------|----------|----------|------------------------------------|
| `name`      | `string` | ✅        | City name                          |
| `country`   | `string` | ✅        | Country name                       |
| `latitude`  | `number` | ✅        | Decimal degrees latitude           |
| `longitude` | `number` | ✅        | Decimal degrees longitude          |

**Response `201 Created`** (new city):
```json
{
  "id": 1,
  "name": "Paris",
  "country": "France",
  "latitude": 48.8566,
  "longitude": 2.3522,
  "created_at": "2024-06-01T12:00:00Z"
}
```

**Response `200 OK`** (duplicate — existing record returned):
```json
{
  "id": 1,
  "name": "Paris",
  "country": "France",
  "latitude": 48.8566,
  "longitude": 2.3522,
  "created_at": "2024-06-01T12:00:00Z"
}
```

---

### `DELETE /api/cities/{id}`
Remove a city by its integer ID.

**Path Parameter:**
| Param | Type      | Description         |
|-------|-----------|---------------------|
| `id`  | `integer` | City primary key    |

**Response `204 No Content`:** (success, empty body)

**Response `404 Not Found`:**
```json
{
  "detail": "City not found"
}
```

---

### `GET /api/weather/{latitude}/{longitude}`
Fetch current weather conditions from the Open-Meteo API for the given coordinates.

**Path Parameters:**
| Param       | Type     | Example   | Description           |
|-------------|----------|-----------|-----------------------|
| `latitude`  | `number` | `48.8566` | Decimal degrees       |
| `longitude` | `number` | `2.3522`  | Decimal degrees       |

**Response `200 OK`:**
```json
{
  "temperature_c": 18.4,
  "temperature_f": 65.1,
  "feels_like_c": 17.1,
  "feels_like_f": 62.8,
  "humidity_percent": 72,
  "wind_speed_mph": 9.3,
  "weather_code": 2,
  "condition": "Partly Cloudy",
  "weather_emoji": "🌤",
  "last_updated": "2024-06-01T14:30:00Z"
}
```

| Field              | Type      | Description                                      |
|--------------------|-----------|--------------------------------------------------|
| `temperature_c`    | `number`  | Current temperature in Celsius                   |
| `temperature_f`    | `number`  | Current temperature in Fahrenheit                |
| `feels_like_c`     | `number`  | Apparent temperature in Celsius                  |
| `feels_like_f`     | `number`  | Apparent temperature in Fahrenheit               |
| `humidity_percent` | `integer` | Relative humidity (%)                            |
| `wind_speed_mph`   | `number`  | Wind speed in mph                                |
| `weather_code`     | `integer` | WMO Weather Interpretation Code                  |
| `condition`        | `string`  | Human-readable condition label                   |
| `weather_emoji`    | `string`  | Emoji icon matching condition                    |
| `last_updated`     | `string`  | ISO 8601 UTC timestamp of data fetch             |

**Response `502 Bad Gateway`** (Open-Meteo unreachable):
```json
{
  "detail": "Failed to fetch weather data from upstream"
}
```

---

### `GET /api/geocode?q={query}`
Search for cities via the Open-Meteo Geocoding API. Returns up to 5 results.

**Query Parameter:**
| Param | Type     | Required | Min Length | Description              |
|-------|----------|----------|------------|--------------------------|
| `q`   | `string` | ✅        | 3 chars    | City name search string  |

**Response `200 OK`:**
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

**Response `400 Bad Request`** (query too short):
```json
{
  "detail": "Query must be at least 3 characters"
}
```

**Response `502 Bad Gateway`** (Open-Meteo unreachable):
```json
{
  "detail": "Failed to fetch geocoding data from upstream"
}
```

---

## WMO Weather Code → Condition + Emoji Mapping

| WMO Code(s)  | Condition           | Emoji |
|--------------|---------------------|-------|
| 0            | Clear Sky            | ☀️    |
| 1            | Mainly Clear         | 🌤    |
| 2            | Partly Cloudy        | ⛅    |
| 3            | Overcast             | ☁️    |
| 45, 48       | Foggy                | 🌫    |
| 51–67        | Drizzle / Rain       | 🌧    |
| 71–77        | Snow                 | ❄️    |
| 80–82        | Rain Showers         | 🌧    |
| 95–99        | Thunderstorm         | ⛈    |

---

## Docker Service Definitions

### `docker-compose.yml`

```yaml
version: "3.9"

services:

  db:
    image: postgres:16-alpine
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-weather_dashboard}
      POSTGRES_USER: ${POSTGRES_USER:-weather}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-weather_pass}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-weather} -d ${POSTGRES_DB:-weather_dashboard}"]
      interval: 5s
      timeout: 5s
      retries: 10

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    restart: unless-stopped
    environment:
      DATABASE_URL: postgresql://${POSTGRES_USER:-weather}:${POSTGRES_PASSWORD:-weather_pass}@db:5432/${POSTGRES_DB:-weather_dashboard}
      ALLOWED_ORIGINS: ${ALLOWED_ORIGINS:-http://localhost:5173}
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
      VITE_API_URL: ${VITE_API_URL:-http://localhost:8000}
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

---

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

---

### `frontend/Dockerfile`

```dockerfile
FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

EXPOSE 5173

CMD ["npx", "vite", "--host", "0.0.0.0", "--port", "5173"]
```

---

## Environment Variables

### Backend

| Variable          | Required | Default                                                                 | Description                                      |
|-------------------|----------|-------------------------------------------------------------------------|--------------------------------------------------|
| `DATABASE_URL`    | ✅        | `postgresql://weather:weather_pass@db:5432/weather_dashboard`          | Full PostgreSQL connection string                |
| `ALLOWED_ORIGINS` | ✅        | `http://localhost:5173`                                                 | Comma-separated CORS allowed origins            |

### Frontend

| Variable       | Required | Default                   | Description                          |
|----------------|----------|---------------------------|--------------------------------------|
| `VITE_API_URL` | ✅        | `http://localhost:8000`   | Backend base URL (injected at build) |

### Database (Docker Compose only)

| Variable            | Default            | Description                |
|---------------------|--------------------|----------------------------|
| `POSTGRES_DB`       | `weather_dashboard`| Database name              |
| `POSTGRES_USER`     | `weather`          | PostgreSQL username         |
| `POSTGRES_PASSWORD` | `weather_pass`     | PostgreSQL password         |

All secrets should be supplied via a `.env` file at the repo root (gitignored).

---

## External Integrations

### Open-Meteo Weather API
- **URL:** `https://api.open-meteo.com/v1/forecast`
- **Auth:** None (free tier, no API key)
- **Parameters used:** `latitude`, `longitude`, `current=temperature_2m,apparent_temperature,relative_humidity_2m,wind_speed_10m,weather_code`
- **Wind speed unit:** `wind_speed_unit=mph`
- **Called by:** `GET /api/weather/{latitude}/{longitude}`

### Open-Meteo Geocoding API
- **URL:** `https://geocoding-api.open-meteo.com/v1/search`
- **Auth:** None (free tier, no API key)
- **Parameters used:** `name={q}&count=5&language=en&format=json`
- **Called by:** `GET /api/geocode?q={query}`

---

## Data Flow

### Page Load
```
Browser → GET /api/cities → backend → PostgreSQL
       ← [city list]
For each city:
Browser → GET /api/weather/{lat}/{lon} → backend → Open-Meteo
       ← weather payload → render WeatherCard
```

### Add City
```
User types → useGeocode (debounced 300ms)
→ GET /api/geocode?q=... → backend → Open-Meteo Geocoding
← [results] → dropdown

User clicks result:
→ POST /api/cities {name,country,lat,lon} → backend → PostgreSQL INSERT
← city record → add to AppContext state
→ GET /api/weather/{lat}/{lon} → backend → Open-Meteo
← weather → render new WeatherCard (fade+slide-up animation)
```

### Remove City
```
User clicks × on card OR right-click → Remove in sidebar:
→ DELETE /api/cities/{id} → backend → PostgreSQL DELETE
← 204 → remove from AppContext state
→ WeatherCard fades out (200ms), CityTreeItem disappears simultaneously
```

### Auto-Refresh (every 60s)
```
useWeather hook setInterval:
→ GET /api/weather/{lat}/{lon} → backend → Open-Meteo
← updated weather payload → update card in-place
```
