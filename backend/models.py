"""ORM models. Tables are created via Base.metadata.create_all on startup.

The City model is defined here so M1's "DB schema created" goal is satisfied.
The CRUD endpoints that operate on it belong to M2 and are not implemented yet.
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
    __tablename__ = "cities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    country = Column(String(100), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("name", "country", name="uq_city_name_country"),
    )
