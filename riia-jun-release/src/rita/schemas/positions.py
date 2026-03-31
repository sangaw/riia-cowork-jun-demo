"""Pydantic schemas for the positions table (live open positions from broker)."""
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, ConfigDict


class PositionBase(BaseModel):
    instrument: str                          # e.g. BANKNIFTY26APR52000CE
    underlying: Literal["NIFTY", "BANKNIFTY"]
    product: Literal["NRML", "MIS", "CNC"] = "NRML"
    option_type: Optional[Literal["CE", "PE"]] = None
    strike: Optional[float] = None
    expiry: Optional[str] = None             # e.g. 26APR
    quantity: int                            # negative = short
    avg_price: float
    last_traded_price: float
    pnl: float
    pct_change: Optional[float] = None


class PositionCreate(PositionBase):
    pass


class Position(PositionBase):
    model_config = ConfigDict(from_attributes=True)

    position_id: str
    recorded_at: datetime
