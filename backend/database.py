"""SQLAlchemy engine, session factory, and FastAPI DB dependency.

The connection string is read from the ``DATABASE_URL`` environment variable so
nothing is hardcoded. In Docker Compose this points at the ``db`` service; on
Render it is injected from the managed Postgres instance. Tests override it with
an in-memory SQLite URL (see ``tests/conftest.py``).
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

# Default matches docker-compose.yml so local `docker compose up` works without
# extra config. Any real deployment (Render) sets DATABASE_URL explicitly.
DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://weather:weather@db:5432/weatherdb"
)

if DATABASE_URL.startswith("sqlite"):
    # In-memory SQLite needs a single shared connection across threads (tests).
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a request-scoped DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
