"""FastAPI application entry point.

M1 scope: app factory, env-driven CORS, DB schema creation on startup, and a
health check. The city/weather/geocode routers are M2 (Backend API) and are
intentionally not implemented here.
"""

import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError

import database
import models  # noqa: F401  (import registers the City table on Base.metadata)

# On first `docker compose up` the db healthcheck can briefly report ready on
# Postgres' temporary bootstrap server, so the backend may attempt to create the
# schema a moment before the real server accepts connections. Without a retry the
# resulting OperationalError crashes uvicorn, and `restart: unless-stopped` turns
# that one transient failure into an endless restart loop (which blocks
# `docker compose exec`). Retry a bounded number of times, then fail fast.
_DB_CONNECT_ATTEMPTS = 10
_DB_CONNECT_BACKOFF_SECONDS = 1.0


def _create_schema_with_retry() -> None:
    # Reference database.engine at call time (not import time) so tests can
    # patch it with an in-memory SQLite engine before the schema is created.
    last_error: OperationalError | None = None
    for attempt in range(1, _DB_CONNECT_ATTEMPTS + 1):
        try:
            database.Base.metadata.create_all(bind=database.engine)
            return
        except OperationalError as exc:  # DB not accepting connections yet
            last_error = exc
            if attempt < _DB_CONNECT_ATTEMPTS:
                time.sleep(_DB_CONNECT_BACKOFF_SECONDS)
    # Genuinely unreachable after retries — fail fast with the original error.
    raise RuntimeError(
        "Could not connect to the database to create the schema after "
        f"{_DB_CONNECT_ATTEMPTS} attempts. Check DATABASE_URL and that the "
        "database is reachable."
    ) from last_error


@asynccontextmanager
async def lifespan(_app: FastAPI):
    _create_schema_with_retry()
    yield


def _cors_origins() -> list[str]:
    """Allowed CORS origins, read from the CORS_ORIGINS env var.

    Defaults to the local frontend origin rather than "*", because pairing a
    wildcard with allow_credentials=True is both invalid per the CORS spec and
    a security risk in production (reviewer feedback).
    """
    raw = os.environ.get("CORS_ORIGINS", "http://localhost:5173")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def create_app() -> FastAPI:
    app = FastAPI(title="Weather Dashboard API", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()
