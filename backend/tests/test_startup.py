"""Startup-resilience tests.

The lifespan must tolerate the database being briefly unavailable on first boot
(so `restart: unless-stopped` does not turn a transient connection error into an
endless restart loop) while still failing fast if the DB is truly unreachable.
"""

import pytest
from sqlalchemy.exc import OperationalError

import main


def _operational_error() -> OperationalError:
    return OperationalError("SELECT 1", {}, Exception("connection refused"))


def test_schema_creation_retries_then_succeeds(monkeypatch):
    """A transient OperationalError should be retried, not crash the app."""
    calls = {"n": 0}

    def flaky_create_all(*_args, **_kwargs):
        calls["n"] += 1
        if calls["n"] < 3:  # fail twice, then succeed
            raise _operational_error()

    monkeypatch.setattr(main.database.Base.metadata, "create_all", flaky_create_all)
    monkeypatch.setattr(main.time, "sleep", lambda _seconds: None)  # no real waiting

    main._create_schema_with_retry()

    assert calls["n"] == 3


def test_schema_creation_fails_fast_when_db_unreachable(monkeypatch):
    """If the DB never becomes reachable, raise after the bounded retries."""

    def always_fail(*_args, **_kwargs):
        raise _operational_error()

    monkeypatch.setattr(main.database.Base.metadata, "create_all", always_fail)
    monkeypatch.setattr(main.time, "sleep", lambda _seconds: None)

    with pytest.raises(RuntimeError, match="Could not connect to the database"):
        main._create_schema_with_retry()
