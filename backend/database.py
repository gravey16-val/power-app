"""SQLAlchemy engine, session factory, declarative Base, and get_db dependency.

The connection string comes *entirely* from the DATABASE_URL environment
variable. There is intentionally no hardcoded fallback: a missing variable
fails loudly at import time rather than silently trying to reach an
unreachable host (past review feedback). Local dev supplies it via
docker-compose; Render injects it from the managed Postgres instance.
"""
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL environment variable is not set. "
        "Set it via docker-compose (local) or the Render dashboard (prod)."
    )

# SQLite (used by the test suite) needs a couple of extra knobs so a single
# in-memory database is shared across the connection pool / threads.
if DATABASE_URL.startswith("sqlite"):
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
