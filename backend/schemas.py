"""Pydantic v2 request/response schemas.

Only the City schemas are defined in this milestone (M1). Endpoint-specific
request bodies (POST /api/cities, etc.) are added in M2.
"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CityBase(BaseModel):
    name: str
    country: str
    latitude: float
    longitude: float


class CityOut(CityBase):
    """City as returned by the API (includes server-generated fields)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
