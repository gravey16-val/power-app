"""FastAPI application entry point.

Responsibilities for M1:
  - create the FastAPI app and configure CORS
  - create database tables on startup via ``Base.metadata.create_all`` (idempotent)
  - expose a ``/health`` endpoint for the Docker/Render healthcheck

Routers (cities, weather, geocode) are wired up in later milestones.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine

# Importing models registers them on ``Base.metadata`` so create_all sees them.
import models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create any missing tables on startup. Safe to run repeatedly (idempotent)."""
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Weather Dashboard API", version="1.0.0", lifespan=lifespan)

# Dev CORS: allow all origins. Tightened to the Render frontend domain in prod.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
