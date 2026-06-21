"""SQLAlchemy engine, session factory, declarative base, and DB dependency.

Exposes `engine`, `SessionLocal`, `Base`, and the `get_db()` FastAPI dependency.
Route handlers must obtain a session via `Depends(get_db)` — never instantiate
`SessionLocal` directly.
"""
import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

# DATABASE_URL is injected via environment (docker-compose / Render). A local
# default is provided so the module is importable in isolation, but production
# always supplies this explicitly.
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://weather:weather@db:5432/weatherdb"
)

# SQLite (used by the test suite) needs check_same_thread disabled.
connect_args = (
    {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Yield a database session, closing it when the request finishes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
