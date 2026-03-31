"""Pydantic schemas for the trades table (closed/executed positions)."""
from datetime import date, datetime
from typing import Optional, Literal
from pydantic import BaseModel, ConfigDict


class TradeBase(BaseModel):
    instrument: str
    underlying: Literal["NIFTY", "BANKNIFTY"]
    expiry: str                              # e.g. 24-Apr-26
    option_type: Literal["CE", "PE"]
    strike: float
    side: Literal["Long", "Short"]
    pnl: float
    notes: Optional[str] = None
    closed_date: Optional[date] = None


class TradeCreate(TradeBase):
    pass


class Trade(TradeBase):
    model_config = ConfigDict(from_attributes=True)

    trade_id: str
    recorded_at: datetime
