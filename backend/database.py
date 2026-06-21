"""SQLAlchemy engine, session factory, declarative Base, and get_db dependency."""
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

# DATABASE_URL is injected via environment (docker-compose / Render). Falls back
# to a local default only so tooling can import this module outside a container.
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://weather:weather@db:5432/weatherdb"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a DB session and always closes it."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
