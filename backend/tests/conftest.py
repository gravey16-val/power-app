"""Pytest fixtures: an in-memory SQLite DB and a FastAPI TestClient.

Why this is set up the way it is (addresses prior review feedback):

* DATABASE_URL is forced to in-memory SQLite *before* the app package is
  imported. Because ``database.engine`` is built at import time from
  DATABASE_URL, this guarantees the engine — and therefore the lifespan's
  ``Base.metadata.create_all(bind=engine)`` — runs against SQLite, never the
  real Postgres instance. Overriding only the ``get_db`` dependency would not
  be enough on its own.
* The ``get_db`` dependency is additionally overridden so any request-scoped
  session also uses the SQLite engine.
* The TestClient is entered with a ``with`` block so the lifespan startup
  (table creation) actually runs against SQLite during tests.
"""
import os
import sys
from pathlib import Path

# Make the backend package importable when running pytest from the repo root
# or from inside the backend/ directory.
BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

# Must be set BEFORE importing database/main, since the engine is built on import.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ.setdefault("CORS_ORIGINS", "*")

import pytest
from fastapi.testclient import TestClient

import database  # noqa: E402
import main  # noqa: E402
from database import Base, engine, get_db  # noqa: E402

# Sanity check: confirm the test engine is the in-memory SQLite one and not a
# stray Postgres connection that would hit the network during create_all.
assert engine.url.get_backend_name() == "sqlite"


@pytest.fixture
def client():
    """Yield a TestClient backed by a fresh in-memory SQLite schema."""
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = database.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    main.app.dependency_overrides[get_db] = override_get_db

    with TestClient(main.app) as test_client:
        yield test_client

    main.app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
