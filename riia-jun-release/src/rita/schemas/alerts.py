"""Pydantic schemas for the alerts table."""
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, ConfigDict


class AlertBase(BaseModel):
    timestamp: datetime
    query_text: Optional[str] = None
    intent_name: Optional[str] = None
    handler: Optional[str] = None
    confidence: Optional[float] = None
    low_confidence: bool = False
    latency_ms: Optional[float] = None
    response_preview: Optional[str] = None
    status: Literal["success", "error", "warning"] = "success"


class AlertCreate(AlertBase):
    pass


class Alert(AlertBase):
    model_config = ConfigDict(from_attributes=True)

    alert_id: str
    recorded_at: datetime
