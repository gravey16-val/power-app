# Weather Dashboard — Real-time City Weather Tracker

## Overview

A real-time weather dashboard enabling users to track live weather conditions across multiple cities. Users manage a personal city list via a persistent left-sidebar tree view and view weather data in a responsive card grid, with all city selections stored in PostgreSQL. The app is fully containerized with Docker Compose and deployable to Render.

## Features

- Persistent left sidebar with city tree/list view showing city name, country flag emoji, and live current temperature
- Add City button that opens an inline search bar with debounced typeahead autocomplete against Open-Meteo Geocoding API (min 3 chars, 300ms debounce, up to 5 results)
- City search result selection: adds city card, adds to tree view, persists city to PostgreSQL, closes search input
- Right-click context menu on tree city entries with a Remove option
- Empty state in sidebar displaying friendly message and directional arrow when no cities are saved
- Responsive weather card grid (3 columns desktop, 2 tablet, 1 mobile) showing city name, country, temperature in °F and °C, weather condition with emoji icon, humidity, wind speed, feels like temperature, and last updated timestamp
- Auto-refresh of all weather cards every 60 seconds
- Loading skeleton UI for weather cards during data fetch
- Remove button (×) in top-right corner of each weather card
- Simultaneous removal of city from both card grid and tree view when removed via card × or tree context menu, with fade+slide-down animation (200ms)
- Fade+slide-up animation for newly added weather cards
- Duplicate city detection: silently ignore attempts to add an already-saved city
- Data persistence layer: PostgreSQL cities table with id, name, country, latitude, longitude, created_at columns
- On page load, fetch all saved cities from backend and load weather data for each
- GET /health endpoint returning {status: ok}
- GET /api/cities endpoint returning all saved cities
- POST /api/cities endpoint accepting {name, country, latitude, longitude}
- DELETE /api/cities/{id} endpoint removing a city
- GET /api/weather/{latitude}/{longitude} endpoint proxying Open-Meteo current weather
- GET /api/geocode?q={query} endpoint proxying Open-Meteo Geocoding API
- Docker Compose configuration defining frontend, backend, and postgres services startable with a single command
- Backend reads DATABASE_URL from environment variable
- Frontend reads VITE_API_URL from environment variable for backend base URL
- Production backend Dockerfile with no --reload flag and non-root user
- Frontend production build served via nginx or Vite preview as static files
- render.yaml committed to repo defining all Render services

## Acceptance Criteria

- [ ] User can type a city name in the search bar and see up to 5 autocomplete suggestions after 3+ characters with 300ms debounce
- [ ] Clicking a search result adds the city card and tree entry, and the city is still present after a full page refresh
- [ ] Weather card temperature values match real data returned from Open-Meteo API (not hardcoded or mocked)
- [ ] Weather cards automatically re-fetch and display updated data every 60 seconds without any user interaction
- [ ] Clicking × on a weather card removes both the card and the corresponding tree entry simultaneously
- [ ] Right-clicking a city in the tree and selecting Remove removes both the tree entry and the corresponding card simultaneously
- [ ] Removal of a city triggers a fade+slide-down animation completing within 200ms
- [ ] Layout renders correctly at 1440px (3-column grid), 768px (2-column grid), and 375px (1-column grid) viewport widths
- [ ] Sidebar displays the empty state message with directional arrow when the cities list is empty
- [ ] Attempting to add a city that already exists in the list results in no duplicate entry and no error message shown to the user
- [ ] GET /api/cities returns HTTP 200, POST /api/cities returns HTTP 201, DELETE /api/cities/{id} returns HTTP 204 or 200, GET /health returns HTTP 200
- [ ] Running docker compose up starts the full stack (frontend, backend, postgres) with no additional manual configuration steps
- [ ] App deploys successfully to Render when DATABASE_URL and VITE_API_URL environment variables are set
- [ ] GET /health endpoint returns {status: ok}
- [ ] Loading skeleton UI is visible on weather cards while weather data is being fetched

## Tech Constraints

- **Frontend:** React 18, TypeScript 5, Tailwind CSS, Vite
- **Backend:** Python 3.12, FastAPI, Uvicorn
- **Database:** PostgreSQL 16
- **Weather API:** Open-Meteo API (no API key required)
- **Geocoding API:** Open-Meteo Geocoding API (no API key required)
- **Containerization:** Docker Compose (frontend, backend, postgres services)
- **Deploy Target:** Render (frontend as Static Site or Web Service, backend as Web Service, Postgres as managed DB)
- **Frontend Env Var:** VITE_API_URL for backend base URL
- **Backend Env Var:** DATABASE_URL for PostgreSQL connection string
- **Production Backend:** Non-root user in Dockerfile, no --reload flag in CMD
- **Frontend Production:** Static files served by nginx or Vite preview
- **IaC:** render.yaml committed to repository

## Open Questions

_None_
