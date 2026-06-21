"""Shared pytest fixtures.

Tests run against an in-memory SQLite DB so they never touch Postgres or the
network. ``DATABASE_URL`` is forced here *before* importing the app so the
engine in ``database.py`` binds to SQLite.
"""

import os

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"

import pytest
from fastapi.testclient import TestClient

from database import Base, engine  # noqa: E402  (must follow env override)
from main import app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _schema():
    """Create the schema once for the test session, drop it at the end."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
