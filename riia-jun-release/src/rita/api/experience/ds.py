"""Experience router for DS dashboard aggregated initial-load payload.

ADR-001 Tier 3: aggregated experience endpoint — instruments list,
last 10 training runs, training split dates. No DB writes.
URL: GET /api/experience/ds/
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from rita.database import get_db

router = APIRouter(prefix="/api/experience/ds", tags=["experience:ds"])


@router.get("/", summary="DS dashboard aggregated payload")
def ds_payload(instrument: str = "NIFTY", db: Session = Depends(get_db)) -> dict[str, Any]:
    from rita.repositories.instrument import InstrumentRepository
    from rita.repositories.training import TrainingRunsRepository
    from rita.repositories.backtest import BacktestRunsRepository
    from rita.core.data_understanding import find_instrument_csv
    from rita.core.data_loader import load_nifty_csv
    from rita.core.technical_analyzer import calculate_indicators

    instruments = [{"id": i.instrument_id, "name": i.name, "exchange": i.exchange,
                    "data_ready": i.is_available} for i in InstrumentRepository(db).read_all()]

    runs = sorted(TrainingRunsRepository(db).read_all(), key=lambda r: r.recorded_at, reverse=True)
    history = [{"run_id": r.run_id, "status": r.status, "instrument": r.instrument or "NIFTY",
                "model_version": r.model_version, "recorded_at": r.recorded_at.isoformat(),
                "backtest_sharpe": r.backtest_sharpe} for r in runs[:10]]

    split = {"train_start": None, "train_end": None, "val_start": None, "val_end": None,
             "backtest_start": None, "backtest_end": None}
    try:
        csv_path = find_instrument_csv(instrument)
        df = calculate_indicators(load_nifty_csv(str(csv_path)))
        idx = int(len(df) * 0.8)
        split.update({"train_start": str(df.index[0].date()), "train_end": str(df.index[idx - 1].date()),
                      "val_start": str(df.index[idx].date()), "val_end": str(df.index[-1].date())})
    except Exception:
        pass
    try:
        bts = [r for r in BacktestRunsRepository(db).read_all()
               if r.status in ("complete", "completed") and (r.instrument or "NIFTY") == instrument]
        if bts:
            latest = max(bts, key=lambda r: r.ended_at or r.recorded_at)
            split.update({"backtest_start": str(latest.start_date), "backtest_end": str(latest.end_date)})
    except Exception:
        pass

    return {"instruments": instruments, "training_context": {"history": history, "split": split}}
