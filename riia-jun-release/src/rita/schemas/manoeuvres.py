"""Pydantic schemas for the manoeuvres table (manoeuvre group actions)."""
from datetime import date, datetime
from typing import Optional, Literal
from pydantic import BaseModel, ConfigDict


class ManoeuvreBase(BaseModel):
    timestamp: datetime
    date: date
    month: str
    action: str                              # e.g. remove, add, roll, adjust
    lot_key: str                             # e.g. NIFTY26APR22700PE_L1
    from_group: Optional[str] = None
    to_group: Optional[str] = None
    nifty_spot: Optional[float] = None
    banknifty_spot: Optional[float] = None


class ManoeuvreCreate(ManoeuvreBase):
    pass


class Manoeuvre(ManoeuvreBase):
    model_config = ConfigDict(from_attributes=True)

    manoeuvre_id: str
    recorded_at: datetime
