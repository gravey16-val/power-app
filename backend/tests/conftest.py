"""Shared pytest fixtures.

Uses an in-memory SQLite database and overrides the get_db dependency so tests
never touch the real Postgres instance or the network. The TestClient is created
without a context manager on purpose: that keeps the FastAPI startup event (which
calls create_all against the real Postgres engine) from firing during tests.
"""
import os
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Make the backend package importable when running `pytest` from /app.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Base, get_db  # noqa: E402
import models  # noqa: E402,F401  (registers models on Base)
from main import app  # noqa: E402

# Single shared in-memory SQLite connection across sessions.
test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=test_engine
)


@pytest.fixture()
def db_session():
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()
