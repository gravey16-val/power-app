"""SQLAlchemy engine, session factory, declarative base, and DB dependency.

The connection string comes from the ``DATABASE_URL`` environment variable so
that the same code runs locally (docker-compose) and on Render without changes.
"""
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Default points at the docker-compose `db` service. Never hardcode in code that
# ships to production — Render injects its own DATABASE_URL.
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://weather:weather@db:5432/weatherdb",
)

# SQLite (used by the test suite) needs a special connect arg; Postgres does not.
connect_args = (
    {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

engine = create_engine(DATABASE_URL, connect_args=connect_args, future=True)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a DB session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
