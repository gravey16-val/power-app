"""Pytest fixtures.

Tests run against an in-memory SQLite database and must never touch the real
Postgres instance. To guarantee that we:

1. Set DATABASE_URL to a SQLite URL *before* importing the app, so
   ``database.py`` (which fails fast on a missing DATABASE_URL) imports cleanly.
2. Replace ``database.engine`` / ``database.SessionLocal`` with the SQLite
   engine. The app's lifespan calls ``Base.metadata.create_all(bind=
   database.engine)`` at startup; patching the module attribute (not just the
   ``get_db`` dependency) ensures that schema creation hits SQLite, not Postgres
   (reviewer feedback).
3. Override the ``get_db`` dependency so request handlers use the same engine.
"""

import os

# Must be set before importing `database` (it raises if DATABASE_URL is unset).
os.environ.setdefault("DATABASE_URL", "sqlite://")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import database

# A single shared in-memory SQLite database (StaticPool keeps one connection so
# the schema persists across sessions within a test).
test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=test_engine
)

# Patch the app's engine/session factory so startup schema creation and request
# handlers both use the test database.
database.engine = test_engine
database.SessionLocal = TestingSessionLocal

import main  # noqa: E402  (imported after patching database)
from database import Base, get_db  # noqa: E402


def _override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


main.app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture()
def client():
    """A TestClient with a freshly created schema for each test.

    Using the context manager form runs the app lifespan (which creates the
    schema against the patched SQLite engine).
    """
    Base.metadata.create_all(bind=test_engine)
    with TestClient(main.app) as test_client:
        yield test_client
    Base.metadata.drop_all(bind=test_engine)
