from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import models  # noqa: F401  (ensures City model is registered on Base)
from database import Base, engine


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Create tables idempotently on startup (no Alembic in M1).
    Base.metadata.create_all(bind=engine)
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Weather Dashboard API", lifespan=lifespan)

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

    return app


app = create_app()
