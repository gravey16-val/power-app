"""FastAPI application entry point.

Milestone 1 scope: app factory, CORS, DB schema creation on startup, and the
/health endpoint used by the Docker healthcheck. Feature routers (cities,
weather, geocode) are added in Milestone 2.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import models  # noqa: F401  (registers ORM models on Base before create_all)
from database import Base, engine


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Create tables if they do not yet exist (idempotent) on startup."""
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Weather Dashboard API", version="0.1.0", lifespan=lifespan)

# CORS is open in development; locked down per-environment for production.
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
