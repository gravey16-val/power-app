import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://weather:weather@db:5432/weatherdb"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a scoped DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
