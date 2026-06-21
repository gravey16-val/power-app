"""FastAPI application entry point.

M1 scope: app factory, CORS, DB schema creation on startup, and the /health
endpoint. The cities/weather/geocode routers are M2 and are not wired up here.
"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine

# Importing models registers them on Base.metadata so create_all builds them.
import models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Idempotent: creates the cities table if it does not already exist.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Weather Dashboard API", version="0.1.0", lifespan=lifespan)

# CORS origins are read from the environment so production can be locked down.
# Default "*" is for local dev only. allow_credentials is False because a "*"
# origin combined with credentials is invalid per the CORS spec and unsafe
# (past review feedback). The app uses no cookies/auth, so this is correct.
cors_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    """Liveness probe used by the Docker healthcheck and Render."""
    return {"status": "ok"}
