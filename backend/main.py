"""FastAPI application entry point.

M1 scaffold scope: app factory, CORS, a /health endpoint, and DB schema
creation on startup. Feature routers (cities, weather, geocode) are added in
later milestones.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import models  # noqa: F401  (registers ORM models on Base before create_all)
from database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Idempotent: creates tables if they don't already exist.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Weather Dashboard API", lifespan=lifespan)

# CORS is open in development; tightened to the frontend origin in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness probe used by the Docker healthcheck and load balancers."""
    return {"status": "ok"}
