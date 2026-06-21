"""Tests for the /health endpoint and that the DB schema is applied on startup."""

from sqlalchemy import inspect

from database import engine


def test_health_returns_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_schema_created():
    # M1 DoD: the `cities` table exists after startup/schema creation.
    tables = inspect(engine).get_table_names()
    assert "cities" in tables
