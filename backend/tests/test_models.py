"""Tests for the City model / `cities` table schema (ticket acceptance criteria).

These directly verify the ticket's acceptance criteria:
  - table exists after schema creation
  - all six columns present with correct types/constraints
  - created_at defaults to the current timestamp
  - schema creation is idempotent
  - the SQLAlchemy model matches the table definition
"""
from datetime import datetime, timezone

import pytest
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError

from database import Base
from models import City


def test_cities_table_exists(engine):
    """`cities` table is created by create_all."""
    inspector = inspect(engine)
    assert "cities" in inspector.get_table_names()


def test_all_six_columns_present(engine):
    """All six documented columns exist on the table."""
    inspector = inspect(engine)
    columns = {col["name"] for col in inspector.get_columns("cities")}
    assert columns == {
        "id",
        "name",
        "country",
        "latitude",
        "longitude",
        "created_at",
    }


def test_column_constraints(engine):
    """Nullability and primary-key constraints match the spec."""
    inspector = inspect(engine)
    cols = {c["name"]: c for c in inspector.get_columns("cities")}

    # NOT NULL on every business column.
    assert cols["name"]["nullable"] is False
    assert cols["country"]["nullable"] is False
    assert cols["latitude"]["nullable"] is False
    assert cols["longitude"]["nullable"] is False
    assert cols["created_at"]["nullable"] is False

    # id is the primary key.
    pk = inspector.get_pk_constraint("cities")
    assert pk["constrained_columns"] == ["id"]


def test_unique_name_country_constraint(engine):
    """UNIQUE(name, country) is present to prevent duplicate cities."""
    inspector = inspect(engine)
    unique_cols = {
        tuple(uc["column_names"]) for uc in inspector.get_unique_constraints("cities")
    }
    assert ("name", "country") in unique_cols


def test_model_columns_match_table(engine):
    """The SQLAlchemy model's column set matches the physical table."""
    model_cols = {c.name for c in City.__table__.columns}
    db_cols = {c["name"] for c in inspect(engine).get_columns("cities")}
    assert model_cols == db_cols


def test_created_at_defaults_to_now(db_session):
    """Inserting a row without created_at populates it with ~now (UTC)."""
    before = datetime.now(timezone.utc)
    city = City(name="Paris", country="France", latitude=48.8566, longitude=2.3522)
    db_session.add(city)
    db_session.commit()
    db_session.refresh(city)

    assert city.created_at is not None

    created = city.created_at
    # SQLite may return a naive datetime; treat it as UTC for comparison.
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    # The server default fires at insert time (~now). Allow a few seconds of
    # slack: SQLite's CURRENT_TIMESTAMP truncates to whole seconds, so it can
    # land just *before* `before`. Postgres now() has microsecond precision.
    assert abs((created - before).total_seconds()) < 5


def test_insert_and_read_back(db_session):
    """A city round-trips through the DB with all fields intact."""
    city = City(name="Tokyo", country="Japan", latitude=35.6762, longitude=139.6503)
    db_session.add(city)
    db_session.commit()
    db_session.refresh(city)

    assert city.id is not None  # serial PK assigned
    fetched = db_session.get(City, city.id)
    assert fetched.name == "Tokyo"
    assert fetched.country == "Japan"
    assert fetched.latitude == pytest.approx(35.6762)
    assert fetched.longitude == pytest.approx(139.6503)


def test_duplicate_name_country_rejected(db_session):
    """The UNIQUE(name, country) constraint is enforced at insert time."""
    db_session.add(City(name="Paris", country="France", latitude=48.8, longitude=2.3))
    db_session.commit()

    db_session.add(City(name="Paris", country="France", latitude=48.8, longitude=2.3))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_same_name_different_country_allowed(db_session):
    """`Paris, France` and `Paris, United States` can coexist."""
    db_session.add(City(name="Paris", country="France", latitude=48.8, longitude=2.3))
    db_session.add(
        City(name="Paris", country="United States", latitude=33.66, longitude=-95.55)
    )
    db_session.commit()  # should not raise
    assert db_session.query(City).filter_by(name="Paris").count() == 2


def test_create_all_is_idempotent(engine):
    """Running create_all repeatedly is safe (no error, table unchanged)."""
    Base.metadata.create_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    assert "cities" in inspect(engine).get_table_names()
