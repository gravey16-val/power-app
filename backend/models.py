"""SQLAlchemy ORM models.

The schema here is the source of truth used by ``Base.metadata.create_all`` on
startup (see ``main.py``). It mirrors the `cities` table documented in
ARCHITECTURE.md exactly.
"""
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    String,
    UniqueConstraint,
    func,
)

from database import Base


class City(Base):
    """A city the user is tracking weather for.

    Columns map 1:1 to the PostgreSQL `cities` table:
      - id          SERIAL PRIMARY KEY
      - name        VARCHAR(255) NOT NULL
      - country     VARCHAR(100) NOT NULL
      - latitude    DOUBLE PRECISION NOT NULL
      - longitude   DOUBLE PRECISION NOT NULL
      - created_at  TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
    """

    __tablename__ = "cities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    country = Column(String(100), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Prevents duplicate city entries (e.g. "Paris, France" twice).
    __table_args__ = (
        UniqueConstraint("name", "country", name="uq_city_name_country"),
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<City id={self.id} name={self.name!r} country={self.country!r}>"
