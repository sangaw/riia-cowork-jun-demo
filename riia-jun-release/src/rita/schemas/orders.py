"""Pydantic schemas for the orders table (broker order log)."""
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict


class OrderBase(BaseModel):
    instrument: str
    underlying: Literal["NIFTY", "BANKNIFTY"]
    product: Literal["NRML", "MIS", "CNC"] = "NRML"
    order_type: Literal["BUY", "SELL"]
    quantity: int                            # total/filled e.g. "65/65"
    quantity_filled: int
    avg_price: float
    status: Literal["COMPLETE", "PENDING", "CANCELLED", "REJECTED"]
    placed_at: datetime


class OrderCreate(OrderBase):
    pass


class Order(OrderBase):
    model_config = ConfigDict(from_attributes=True)

    order_id: str
    recorded_at: datetime
