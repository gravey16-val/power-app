"""Tests for environment-variable-driven configuration (this ticket).

These lock in the behaviour the ticket and prior reviews require:
- DATABASE_URL is mandatory and fails fast when missing (no hardcoded fallback).
- CORS origins come from CORS_ORIGINS and never default to a wildcard.
"""

import importlib
import sys

import pytest


def test_database_url_is_required(monkeypatch):
    """Importing database with no DATABASE_URL must raise, not fall back."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    sys.modules.pop("database", None)
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        importlib.import_module("database")
    # Restore a importable state for any later imports in this process.
    sys.modules.pop("database", None)
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    importlib.import_module("database")


def test_cors_origins_parsed_from_env(monkeypatch):
    import main

    monkeypatch.setenv(
        "CORS_ORIGINS", "http://localhost:5173, https://example.com"
    )
    assert main._cors_origins() == [
        "http://localhost:5173",
        "https://example.com",
    ]


def test_cors_origins_default_is_not_wildcard(monkeypatch):
    import main

    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    origins = main._cors_origins()
    assert "*" not in origins
    assert origins == ["http://localhost:5173"]
