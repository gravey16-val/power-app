"""Pytest fixtures: in-memory SQLite DB and a FastAPI TestClient.

The real `get_db` dependency is overridden with a session bound to an in-memory
SQLite database, so tests never touch PostgreSQL or the network.
"""
import os
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure the backend root (parent of tests/) is importable as `main`/`database`.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database import Base, get_db  # noqa: E402
from main import app  # noqa: E402


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=engine
    )
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    # No `with` block: lifespan startup (which targets the real engine) is
    # intentionally skipped to keep tests DB-isolated.
    yield TestClient(app)
    app.dependency_overrides.clear()
