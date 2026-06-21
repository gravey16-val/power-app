"""FastAPI application entry point.

Bootstraps the app, configures CORS for the frontend origin, and creates the
database schema on startup. Routers (cities, weather, geocode) are added in
later milestones.
"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine


def get_cors_origins() -> list[str]:
    """Frontend origins allowed by CORS.

    Configurable via the comma-separated `CORS_ORIGINS` env var so staging /
    production origins can be supplied without code changes. Defaults to the
    local Vite dev server origin.
    """
    raw = os.getenv("CORS_ORIGINS", "http://localhost:5173")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Idempotent: creates tables registered on Base.metadata if they don't exist.
    Base.metadata.create_all(bind=engine)
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Weather Dashboard API", version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["health"])
    def health() -> dict[str, str]:
        """Health check for the load balancer and Docker healthcheck."""
        return {"status": "ok"}

    return app


app = create_app()
