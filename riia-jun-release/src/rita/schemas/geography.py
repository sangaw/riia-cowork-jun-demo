from __future__ import annotations

from pydantic import BaseModel


class GeoInstrument(BaseModel):
    id: str
    name: str
    flag: str
    close: float | None
    daily_return_pct: float | None
    signal: str           # "bullish" | "bearish" | "neutral"
    return_1y_pct: float | None = None   # Phase 2: (close_latest/close_252d_ago-1)*100
    risk_score: int | None = None        # Phase 2: annualized-vol bucket 1–5
    sector: str | None = None            # Phase 2: static lookup (no DB column yet)


class GeoRegion(BaseModel):
    region: str
    flag: str
    instruments: list[GeoInstrument]


class GeographyOverviewResponse(BaseModel):
    regions: list[GeoRegion]
