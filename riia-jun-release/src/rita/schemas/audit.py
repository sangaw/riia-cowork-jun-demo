"""Pydantic schemas for the audit_log table (API and agent action log)."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class AuditLogBase(BaseModel):
    timestamp: datetime
    source: str                             # api / agent / mcp
    method: Optional[str] = None           # GET, POST, etc.
    path: Optional[str] = None             # API path or tool name
    status_code: Optional[int] = None
    duration_ms: Optional[float] = None
    args_summary: Optional[str] = None
    result_summary: Optional[str] = None


class AuditLogCreate(AuditLogBase):
    pass


class AuditLog(AuditLogBase):
    model_config = ConfigDict(from_attributes=True)

    log_id: str
    recorded_at: datetime
