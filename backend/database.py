"""SQLAlchemy engine, session factory, declarative Base, and get_db dependency.

DATABASE_URL is read strictly from the environment with no fallback. A hardcoded
fallback (e.g. ``postgresql://weather:weather@db:5432/weatherdb``) would embed
plaintext credentials in source and, on Render, silently try to reach an
unreachable ``db`` host. Instead we fail fast with a clear error so a missing
configuration is caught immediately. Local-dev defaults live only in ``.env`` /
``.env.example``.
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL environment variable is not set. "
        "Copy .env.example to .env (local dev) or configure it in your "
        "deployment environment."
    )

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency yielding a request-scoped DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
