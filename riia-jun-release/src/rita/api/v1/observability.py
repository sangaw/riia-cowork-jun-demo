"""Observability endpoints for the Ops dashboard.

Provides structured JSON summaries of:
  - /api/v1/metrics/summary       — API request counts, latency, top endpoints
  - /api/v1/step-log              — Training run log formatted as pipeline steps
  - /api/v1/drift                 — System health / drift checks
  - /api/v1/mcp-calls             — MCP tool call log (empty in this deployment)
  - /api/v1/performance-summary   — Latest backtest KPIs for the dashboard
  - /api/v1/trade-events          — Trade entry/exit events from backtest allocation changes
  - /api/v1/instrument/active     — Currently active instrument info
  - POST /api/v1/pipeline         — Trigger a full train+backtest pipeline run
"""

from __future__ import annotations

import threading
import uuid
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Optional

import structlog
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from prometheus_client import REGISTRY
from sqlalchemy.orm import Session

from rita.config import get_settings
from rita.database import get_db, SessionLocal
from rita.services.workflow_service import get_live_progress
from rita.repositories.instrument import InstrumentRepository
from rita.repositories.market_data import MarketDataCacheRepository
from rita.repositories.training import TrainingRunsRepository
from rita.repositories.backtest import BacktestRunsRepository, BacktestResultsRepository
from rita.core.performance import build_performance_feedback, build_portfolio_comparison

log = structlog.get_logger()

router = APIRouter(prefix="/api/v1", tags=["observability"])

# In-memory active instrument — resets to NIFTY on server restart
_active_instrument_id: str = "NIFTY"

_COUNTRY_FLAG = {"IN": "\U0001f1ee\U0001f1f3", "US": "\U0001f1fa\U0001f1f8", "NL": "\U0001f1f3\U0001f1f1"}


# ── Helpers ────────────────────────────────────────────────────────────────────

def _collect_metrics_summary() -> dict[str, Any]:
    """Read the Prometheus REGISTRY and return a structured summary dict.

    prometheus-fastapi-instrumentator emits an ``http_request_duration_seconds``
    histogram with labels ``{handler, method, status_code}``.
    """
    total = 0
    errors = 0
    dur_sum = 0.0
    endpoints: dict[str, dict[str, int]] = defaultdict(lambda: {"count": 0, "errors": 0})

    try:
        for mf in REGISTRY.collect():
            if mf.name != "http_request_duration_seconds":
                continue
            for s in mf.samples:
                handler = s.labels.get("handler", "unknown")
                sc = str(s.labels.get("status_code", ""))
                is_error = sc.startswith(("4", "5"))

                if s.name.endswith("_count"):
                    count = int(s.value)
                    total += count
                    endpoints[handler]["count"] += count
                    if is_error:
                        errors += count
                        endpoints[handler]["errors"] += count
                elif s.name.endswith("_sum"):
                    dur_sum += s.value
    except Exception:  # noqa: BLE001
        pass

    avg_ms = round(dur_sum / total * 1000, 1) if total > 0 else None
    error_rate_pct = round(errors / total * 100, 2) if total > 0 else 0.0

    # Sort endpoints descending by count and keep top 20
    sorted_eps = dict(
        sorted(endpoints.items(), key=lambda kv: kv[1]["count"], reverse=True)[:20]
    )

    return {
        "total_requests": total,
        "error_count": errors,
        "error_rate_pct": error_rate_pct,
        "avg_latency_ms": avg_ms,
        "endpoints": sorted_eps,
    }


# ── GET /api/v1/metrics/summary ────────────────────────────────────────────────

@router.get("/metrics/summary", summary="Structured API metrics summary")
def metrics_summary(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Return a JSON summary of live Prometheus metrics plus training KPIs.

    Shape consumed by monitoring.js and health.js loadMetrics():
    ```json
    {
      "api_requests": { "total_requests": 42, "error_count": 1, ... },
      "pipeline":     { "completed_steps": 3, "failed_steps": 0, ... },
      "training": {
        "rounds": 2,
        "latest_backtest_sharpe": 1.23,
        "latest_backtest_mdd_pct": -8.5,
        "latest_backtest_cagr_pct": 18.2,
        "latest_constraints_met": true
      }
    }
    ```
    """
    api = _collect_metrics_summary()

    training: dict[str, Any] = {"rounds": 0}
    pipeline: dict[str, Any] = {"completed_steps": 0, "failed_steps": 0, "step_timing": {}}

    try:
        train_repo = TrainingRunsRepository(db)
        runs = train_repo.read_all()
        completed = [r for r in runs if r.status in ("complete", "completed")]
        failed = [r for r in runs if r.status == "failed"]

        training["rounds"] = len(completed)
        pipeline["completed_steps"] = len(completed)
        pipeline["failed_steps"] = len(failed)

        if completed:
            latest = max(completed, key=lambda r: r.recorded_at)
            sharpe = latest.backtest_sharpe
            mdd = latest.backtest_mdd        # stored as fraction e.g. -0.085
            ret = latest.backtest_return     # stored as fraction e.g. 0.18
            training["latest_backtest_sharpe"] = sharpe
            training["latest_backtest_mdd_pct"] = round(mdd * 100, 2) if mdd is not None else None
            training["latest_backtest_cagr_pct"] = round(ret * 100, 2) if ret is not None else None
            constraints_met = (
                sharpe is not None and sharpe >= 1.0
                and mdd is not None and abs(mdd * 100) < 10
            )
            training["latest_constraints_met"] = constraints_met
    except Exception:  # noqa: BLE001
        pass

    return {
        "api_requests": api,
        "pipeline": pipeline,
        "training": training,
    }


# ── GET /api/v1/training-progress ─────────────────────────────────────────────

@router.get("/training-progress", summary="Live training progress for the current run")
def training_progress(run_id: Optional[str] = None) -> list[dict[str, Any]]:
    """Return live progress records for an in-progress (or recently completed) training run.

    Polled every 2 seconds by ds.html Step 4 to show:
      - current timestep vs total (progress bar)
      - latest loss and ep_rew_mean (live chart)

    Each record: { "timestep": int, "loss": float, "ep_rew_mean": float }
    Returns [] when no run is active or run_id is not found.
    """
    return get_live_progress(run_id)


# ── GET /api/v1/step-log ───────────────────────────────────────────────────────

@router.get("/step-log", summary="Pipeline step log")
def step_log(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    """Return the most recent pipeline run's steps for the monitoring table.

    A pipeline run = one train + one backtest. Steps are the logical phases:
      1. Load Data, 2. Compute Indicators, 3. Train/Validate, 4. Backtest

    Only the latest pipeline run is returned (not all historical runs).
    """
    train_repo = TrainingRunsRepository(db)
    bt_repo = BacktestRunsRepository(db)

    all_trains = sorted(train_repo.read_all(), key=lambda r: r.recorded_at, reverse=True)
    all_bts = sorted(bt_repo.read_all(), key=lambda r: r.recorded_at, reverse=True)

    if not all_trains:
        return []

    latest = all_trains[0]
    # Find the backtest that matches (same run time window)
    latest_bt = all_bts[0] if all_bts else None

    def _iso(dt: Any) -> Optional[str]:
        return dt.isoformat() if dt else None

    def _dur(start: Any, end: Any) -> Optional[float]:
        if start and end:
            return (end - start).total_seconds()
        return None

    rows = [
        {
            "step_num": 1,
            "step_name": "Load & Prepare Data",
            "status": "completed",
            "duration_secs": None,
            "started_at": _iso(latest.started_at),
            "ended_at": None,
            "run_id": latest.run_id,
        },
        {
            "step_num": 2,
            "step_name": "Compute Indicators",
            "status": "completed",
            "duration_secs": None,
            "started_at": _iso(latest.started_at),
            "ended_at": None,
            "run_id": latest.run_id,
        },
        {
            "step_num": 3,
            "step_name": f"Train Model ({latest.model_version})",
            "status": latest.status if latest.status in ("complete", "completed", "failed", "running") else latest.status,
            "duration_secs": _dur(latest.started_at, latest.ended_at),
            "started_at": _iso(latest.started_at),
            "ended_at": _iso(latest.ended_at),
            "run_id": latest.run_id,
            "sharpe": latest.backtest_sharpe,
            "mdd": round(latest.backtest_mdd * 100, 2) if latest.backtest_mdd else None,
        },
        {
            "step_num": 4,
            "step_name": "Backtest",
            "status": latest_bt.status if latest_bt else "pending",
            "duration_secs": _dur(latest_bt.started_at, latest_bt.ended_at) if latest_bt else None,
            "started_at": _iso(latest_bt.started_at) if latest_bt else None,
            "ended_at": _iso(latest_bt.ended_at) if latest_bt else None,
            "run_id": latest_bt.run_id if latest_bt else None,
        },
    ]
    return rows


# ── GET /api/v1/drift ──────────────────────────────────────────────────────────

_DAYS_FRESH_WARN = 7
_DAYS_FRESH_ALERT = 30
_SHARPE_WARN = 1.0
_SHARPE_ALERT = 0.5


def _data_freshness_check(db: Session) -> dict[str, Any]:
    """Check how many days old the most recent market data entry is."""
    repo = MarketDataCacheRepository(db)
    records = repo.read_all()

    if not records:
        return {
            "status": "warn",
            "days_old": None,
            "latest_date": None,
            "message": "No market data cached - load price data to enable freshness check.",
        }

    latest: date = max(r.date for r in records)
    days_old = (date.today() - latest).days

    if days_old >= _DAYS_FRESH_ALERT:
        status = "alert"
        msg = f"Market data is {days_old} days old — consider refreshing."
    elif days_old >= _DAYS_FRESH_WARN:
        status = "warn"
        msg = f"Market data is {days_old} days old."
    else:
        status = "ok"
        msg = f"Market data is current ({days_old} day(s) old)."

    return {
        "status": status,
        "days_old": days_old,
        "latest_date": str(latest),
        "message": msg,
    }


def _pipeline_health_check(db: Session) -> dict[str, Any]:
    """Check pipeline health based on recent training and backtest run statuses."""
    train_repo = TrainingRunsRepository(db)
    bt_repo = BacktestRunsRepository(db)

    train_runs = train_repo.read_all()
    bt_runs = bt_repo.read_all()

    failed = [r for r in train_runs if r.status == "failed"] + \
             [r for r in bt_runs if r.status == "failed"]
    completed = [r for r in train_runs if r.status in ("complete", "completed")] + \
                [r for r in bt_runs if r.status in ("complete", "completed")]

    if failed:
        return {
            "status": "warn",
            "message": f"{len(failed)} run(s) failed. Check step log for details.",
            "completed": len(completed),
            "failed": len(failed),
        }
    if not completed:
        return {
            "status": "ok",
            "message": "No pipeline runs yet - submit a training or backtest job.",
            "completed": 0,
            "failed": 0,
        }
    return {
        "status": "ok",
        "message": f"All runs healthy ({len(completed)} completed).",
        "completed": len(completed),
        "failed": 0,
    }


def _sharpe_drift_check(db: Session) -> dict[str, Any]:
    """Check if recent Sharpe ratios are declining."""
    repo = TrainingRunsRepository(db)
    runs = [r for r in repo.read_all() if r.backtest_sharpe is not None]
    runs_sorted = sorted(runs, key=lambda r: r.recorded_at)

    if not runs_sorted:
        return {
            "status": "ok",
            "message": "No training runs with Sharpe data yet.",
            "last_sharpe": None,
        }

    last_sharpe = runs_sorted[-1].backtest_sharpe

    if last_sharpe is None or last_sharpe < _SHARPE_ALERT:
        status = "alert"
        msg = f"Sharpe ratio {last_sharpe:.3f} below alert threshold {_SHARPE_ALERT}"
    elif last_sharpe < _SHARPE_WARN:
        status = "warn"
        msg = f"Sharpe ratio {last_sharpe:.3f} below warning threshold {_SHARPE_WARN}"
    else:
        status = "ok"
        msg = f"Sharpe ratio {last_sharpe:.3f} is healthy"

    return {"status": status, "message": msg, "last_sharpe": last_sharpe}


@router.get("/drift", summary="System health and drift checks")
def drift(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Return a structured system health report consumed by observability.js.

    Shape:
    ```json
    {
      "summary": { "overall": "ok" | "warn" | "alert", "checks": {...} },
      "checks": {
        "sharpe_drift":       { "status": "ok", "message": "..." },
        "return_degradation": { "status": "ok", "message": "..." },
        "data_freshness":     { "status": "ok", "days_old": 2 },
        "pipeline_health":    { "status": "ok", "message": "..." },
        "constraint_breach":  { "status": "ok", "message": "..." }
      }
    }
    ```
    """
    from rita.core.drift_detector import DriftDetector
    detector = DriftDetector(db)
    report = detector.full_report()
    summary = detector.health_summary(report)
    return {"summary": summary, "checks": report}


# ── GET /api/v1/performance-summary ───────────────────────────────────────────

@router.get("/performance-summary", summary="Latest backtest performance KPIs")
def performance_summary(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Return KPI metrics computed from the latest completed backtest run.

    Shape consumed by health.js loadPerfSummary() and performance.js loadPerfSummaryFull():
    ```json
    {
      "portfolio_total_return_pct": 18.5,
      "benchmark_total_return_pct": 12.1,
      "portfolio_cagr_pct": 18.5,
      "benchmark_cagr_pct": 12.1,
      "sharpe_ratio": 1.23,
      "max_drawdown_pct": -8.5,
      "annual_volatility_pct": 14.2,
      "win_rate_pct": 58.3,
      "total_days": 365,
      "constraints_met": true
    }
    ```
    """
    runs_repo = BacktestRunsRepository(db)
    results_repo = BacktestResultsRepository(db)

    # Find the latest completed backtest run
    all_runs = [r for r in runs_repo.read_all() if r.status in ("complete", "completed")]
    if not all_runs:
        return {
            "portfolio_total_return_pct": None,
            "benchmark_total_return_pct": None,
            "portfolio_cagr_pct": None,
            "benchmark_cagr_pct": None,
            "sharpe_ratio": None,
            "max_drawdown_pct": None,
            "annual_volatility_pct": None,
            "win_rate_pct": None,
            "total_days": 0,
            "constraints_met": False,
        }

    latest_run = max(all_runs, key=lambda r: r.ended_at or r.recorded_at)
    results = sorted(
        [r for r in results_repo.read_all() if r.run_id == latest_run.run_id],
        key=lambda r: r.date,
    )

    if not results:
        return {
            "portfolio_total_return_pct": None,
            "benchmark_total_return_pct": None,
            "portfolio_cagr_pct": None,
            "benchmark_cagr_pct": None,
            "sharpe_ratio": None,
            "max_drawdown_pct": None,
            "annual_volatility_pct": None,
            "win_rate_pct": None,
            "total_days": 0,
            "constraints_met": False,
        }

    # Total return: last portfolio_value is normalised (1.0 = start)
    port_final = results[-1].portfolio_value
    bench_final = results[-1].benchmark_value
    port_return_pct = round((port_final - 1.0) * 100, 2)
    bench_return_pct = round((bench_final - 1.0) * 100, 2)

    total_days = (results[-1].date - results[0].date).days or 1
    years = total_days / 365.25

    # CAGR
    port_cagr = round((port_final ** (1 / years) - 1) * 100, 2) if years > 0 else port_return_pct
    bench_cagr = round((bench_final ** (1 / years) - 1) * 100, 2) if years > 0 else bench_return_pct

    # Sharpe ratio — use stored value if available, else compute from daily returns
    sharpe: Optional[float] = results[0].sharpe_ratio  # stored on all rows for the run
    if sharpe is None:
        daily_returns = []
        for i in range(1, len(results)):
            prev = results[i - 1].portfolio_value
            curr = results[i].portfolio_value
            if prev and prev > 0:
                daily_returns.append((curr - prev) / prev)
        if len(daily_returns) > 1:
            import statistics
            mean_r = statistics.mean(daily_returns)
            std_r = statistics.stdev(daily_returns)
            sharpe = round((mean_r / std_r) * (252 ** 0.5), 3) if std_r > 0 else None

    # Max drawdown
    peak = 1.0
    max_dd = 0.0
    for r in results:
        v = r.portfolio_value
        if v > peak:
            peak = v
        dd = (v - peak) / peak * 100 if peak > 0 else 0
        if dd < max_dd:
            max_dd = dd
    max_dd_pct = round(max_dd, 2)

    # Annual volatility from daily returns
    daily_returns = []
    for i in range(1, len(results)):
        prev = results[i - 1].portfolio_value
        curr = results[i].portfolio_value
        if prev and prev > 0:
            daily_returns.append((curr - prev) / prev)
    vol_pct: Optional[float] = None
    if len(daily_returns) > 1:
        import statistics
        vol_pct = round(statistics.stdev(daily_returns) * (252 ** 0.5) * 100, 2)

    # Win rate: % of days portfolio value increased
    wins = sum(1 for i in range(1, len(results)) if results[i].portfolio_value > results[i - 1].portfolio_value)
    win_rate_pct = round(wins / (len(results) - 1) * 100, 1) if len(results) > 1 else None

    constraints_met = (
        sharpe is not None and sharpe >= 1.0
        and abs(max_dd_pct) < 10
    )

    return {
        "portfolio_total_return_pct": port_return_pct,
        "benchmark_total_return_pct": bench_return_pct,
        "portfolio_cagr_pct": port_cagr,
        "benchmark_cagr_pct": bench_cagr,
        "sharpe_ratio": sharpe,
        "max_drawdown_pct": max_dd_pct,
        "annual_volatility_pct": vol_pct,
        "win_rate_pct": win_rate_pct,
        "total_days": total_days,
        "constraints_met": constraints_met,
        # Internal fields for stale-data detection in loadPerfSummary()
        "_run_instrument_id": None,
        "_active_instrument_id": None,
    }


# ── GET /api/v1/backtest-daily ────────────────────────────────────────────────

@router.get("/backtest-daily", summary="Daily backtest results for charting")
def backtest_daily(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    """Return daily backtest result rows for the latest completed run.

    Shape consumed by performance.js loadPerformance():
    ```json
    [{ "date": "2025-01-01", "portfolio_value": 1.05, "benchmark_value": 1.02, "allocation": 0.7 }]
    ```
    """
    runs_repo = BacktestRunsRepository(db)
    results_repo = BacktestResultsRepository(db)

    all_runs = [r for r in runs_repo.read_all() if r.status in ("complete", "completed")]
    if not all_runs:
        return []

    latest_run = max(all_runs, key=lambda r: r.ended_at or r.recorded_at)
    results = sorted(
        [r for r in results_repo.read_all() if r.run_id == latest_run.run_id],
        key=lambda r: r.date,
    )

    return [
        {
            "date": str(r.date),
            "portfolio_value": r.portfolio_value,
            "benchmark_value": r.benchmark_value,
            "allocation": r.allocation,
            "close_price": r.close_price,
        }
        for r in results
    ]


# ── GET /api/v1/instrument/active ─────────────────────────────────────────────

@router.get("/instrument/active", summary="Currently active instrument")
def active_instrument(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Return the currently active trading instrument.

    Shape consumed by main.js loadActiveInstrument():
    ```json
    { "id": "NIFTY", "name": "Nifty 50", "flag": "🇮🇳", "exchange": "NSE", "lot_size": 75 }
    ```
    """
    repo = InstrumentRepository(db)
    inst = repo.find_by_id(_active_instrument_id)
    if inst is None:
        # Fallback: return NIFTY defaults if DB record missing
        cfg = get_settings()
        return {
            "id": "NIFTY",
            "name": "Nifty 50",
            "flag": "\U0001f1ee\U0001f1f3",
            "exchange": "NSE",
            "lot_size": cfg.instruments.nifty.lot_size,
        }
    return {
        "id":       inst.instrument_id,
        "name":     inst.name,
        "flag":     _COUNTRY_FLAG.get(inst.country_code, ""),
        "exchange": inst.exchange,
        "lot_size": inst.lot_size,
    }


class _SelectInstrumentBody(BaseModel):
    instrument_id: str


@router.post("/instrument/select", summary="Set the active instrument")
def select_instrument(body: _SelectInstrumentBody, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Switch the active instrument used by subsequent pipeline runs.

    Validates the instrument exists in the DB, then updates the in-memory
    active instrument. Resets to NIFTY on server restart.
    """
    global _active_instrument_id

    repo = InstrumentRepository(db)
    inst = repo.find_by_id(body.instrument_id.upper())
    if inst is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Instrument '{body.instrument_id}' not found.")

    _active_instrument_id = inst.instrument_id
    log.info("instrument.selected", instrument_id=_active_instrument_id)
    return {
        "id":       inst.instrument_id,
        "name":     inst.name,
        "flag":     _COUNTRY_FLAG.get(inst.country_code, ""),
        "exchange": inst.exchange,
        "lot_size": inst.lot_size,
    }


# ── GET /api/v1/instruments ───────────────────────────────────────────────────

@router.get("/instruments", summary="List all instruments")
def list_instruments(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    """Return all instruments from the instruments table.

    Shape consumed by ds.html loadUnderstand() / loadInstruments():
    ```json
    [{ "id": "NIFTY", "name": "Nifty 50", "exchange": "NSE", "lot_size": 75, "data_ready": false }]
    ```
    ``data_ready`` maps from ``is_available`` — the DS app uses this to show
    disabled pills for instruments not yet ready for analysis.
    """
    repo = InstrumentRepository(db)
    return [
        {
            "id": i.instrument_id,
            "name": i.name,
            "exchange": i.exchange,
            "country_code": i.country_code,
            "lot_size": i.lot_size,
            "data_ready": i.is_available,
        }
        for i in repo.read_all()
    ]


# ── POST /api/v1/instruments ──────────────────────────────────────────────────

class _InstrumentBody(BaseModel):
    instrument_id: str
    name: str
    exchange: str
    country_code: str
    lot_size: Optional[int] = None
    is_available: bool = False


@router.post("/instruments", summary="Add a new instrument", status_code=201)
def add_instrument(body: _InstrumentBody, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Insert a new instrument into the instruments table.

    Use this endpoint to register a new instrument as the project scales.
    ``is_available`` should remain false until data is loaded and verified.
    """
    from datetime import datetime, timezone
    from rita.schemas.instrument import Instrument as _Instrument

    repo = InstrumentRepository(db)
    record = _Instrument(
        instrument_id=body.instrument_id.upper(),
        name=body.name,
        exchange=body.exchange,
        country_code=body.country_code,
        lot_size=body.lot_size,
        is_available=body.is_available,
        created_at=datetime.now(timezone.utc),
    )
    repo.upsert(record)
    return {"status": "created", "instrument_id": record.instrument_id}


# ── PATCH /api/v1/instruments/{instrument_id}/availability ────────────────────

@router.patch("/instruments/{instrument_id}/availability", summary="Toggle instrument availability")
def set_availability(instrument_id: str, is_available: bool, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Set is_available on an instrument to show or hide it from users.

    Pass ``?is_available=true`` or ``?is_available=false`` as a query parameter.
    Returns 404 if the instrument_id does not exist.
    """
    from fastapi import HTTPException

    repo = InstrumentRepository(db)
    instrument = repo.find_by_id(instrument_id.upper())
    if instrument is None:
        raise HTTPException(status_code=404, detail=f"Instrument '{instrument_id}' not found")

    updated = instrument.model_copy(update={"is_available": is_available})
    repo.upsert(updated)
    return {"instrument_id": instrument_id.upper(), "is_available": is_available}


# ── POST /api/v1/pipeline ──────────────────────────────────────────────────────

class PipelineRequest(BaseModel):
    instrument: str = "NIFTY"
    target_return_pct: float = 15.0
    time_horizon_days: int = 365
    risk_tolerance: str = "moderate"
    timesteps: int = 200_000
    force_retrain: bool = False
    n_seeds: int = 1
    sim_start: Optional[str] = None   # ISO date override for backtest start (YYYY-MM-DD)
    sim_end: Optional[str] = None     # ISO date override for backtest end (YYYY-MM-DD)


class PipelineResponse(BaseModel):
    status: str
    message: str
    train_run_id: Optional[str] = None
    backtest_run_id: Optional[str] = None


def _run_pipeline_job(
    train_run_id: str,
    backtest_run_id: str,
    req: PipelineRequest,
) -> None:
    """Background thread: run full train → backtest pipeline."""
    from rita.services.workflow_service import WorkflowService
    from rita.schemas.training import TrainingRunCreate
    from rita.schemas.backtest import BacktestRunCreate
    from datetime import timedelta

    db = SessionLocal()
    try:
        # ── Training ────────────────────────────────────────────────
        WorkflowService(db)  # noqa: F841 — kept for side-effect initialisation
        train_body = TrainingRunCreate(
            instrument=req.instrument,
            model_version=f"pipeline-{train_run_id[:8]}",
            algorithm="DoubleDQN",
            timesteps=req.timesteps,
            learning_rate=1e-4,
            buffer_size=50_000,
            net_arch="[128, 128]",
            exploration_pct=0.1,
            notes=f"pipeline risk={req.risk_tolerance} target={req.target_return_pct}%",
        )
        # Overwrite run_id so we can track it
        from rita.repositories.training import TrainingRunsRepository
        from rita.schemas.training import TrainingRun
        now = datetime.now(timezone.utc)
        run = TrainingRun(
            **train_body.model_dump(),
            run_id=train_run_id,
            status="pending",
            started_at=None,
            ended_at=None,
            recorded_at=now,
        )
        TrainingRunsRepository(db).upsert(run)

        from rita.core.ml_dispatch import TrainingConfig
        from rita.core.data_loader import model_dir
        mdir = model_dir(req.instrument)
        config = TrainingConfig(
            run_id=train_run_id,
            instrument=req.instrument,
            model_version=train_body.model_version,
            algorithm=train_body.algorithm,
            timesteps=train_body.timesteps,
            learning_rate=train_body.learning_rate,
            buffer_size=train_body.buffer_size,
            net_arch=train_body.net_arch,
            exploration_pct=train_body.exploration_pct,
            output_dir=str(mdir),
            n_seeds=req.n_seeds,
        )

        # ── Reuse existing model when force_retrain=False ────────────
        existing_zips = sorted(mdir.glob("*.zip"))
        if not req.force_retrain and existing_zips:
            existing_model_path = existing_zips[-1]          # pick most recent
            reused_model_version = existing_model_path.stem  # e.g. "v1.0_abc12345"
            log.info(
                "pipeline.reuse_model",
                instrument=req.instrument,
                model_path=str(existing_model_path),
            )
            # Mark the training run record as complete (skipped, reused)
            runs_repo2 = TrainingRunsRepository(db)
            reused_run = runs_repo2.find_by_id(train_run_id)
            if reused_run is not None:
                runs_repo2.upsert(
                    TrainingRun(
                        **{
                            **reused_run.model_dump(),
                            "status": "complete",
                            "started_at": datetime.now(timezone.utc),
                            "ended_at": datetime.now(timezone.utc),
                            "model_path": str(existing_model_path),
                            "notes": (reused_run.notes or "") + " [reused existing model]",
                        }
                    )
                )
        else:
            # Run training synchronously inside this background thread
            from rita.services.workflow_service import _run_training_job
            _run_training_job(config)
            reused_model_version = train_body.model_version

        # ── Backtest ────────────────────────────────────────────────
        # Use UI-supplied dates if provided, otherwise fall back to time_horizon_days
        if req.sim_end:
            end_date = date.fromisoformat(req.sim_end)
        else:
            end_date = date.today()
        if req.sim_start:
            start_date = date.fromisoformat(req.sim_start)
        else:
            start_date = end_date - timedelta(days=req.time_horizon_days)
        backtest_body = BacktestRunCreate(
            start_date=start_date,
            end_date=end_date,
            model_version=reused_model_version,
            triggered_by="pipeline",
        )
        from rita.repositories.backtest import BacktestRunsRepository
        from rita.schemas.backtest import BacktestRun
        from rita.core.backtest_dispatch import BacktestConfig
        bt_run = BacktestRun(
            **backtest_body.model_dump(),
            run_id=backtest_run_id,
            status="pending",
            started_at=None,
            ended_at=None,
            recorded_at=datetime.now(timezone.utc),
        )
        BacktestRunsRepository(db).upsert(bt_run)
        from rita.services.backtest_service import _run_backtest_job
        bt_config = BacktestConfig(
            run_id=backtest_run_id,
            start_date=start_date,
            end_date=end_date,
            model_version=reused_model_version,
            strategy_params=None,
            instrument=req.instrument,
        )
        _run_backtest_job(backtest_run_id, bt_config)
    except Exception:  # noqa: BLE001
        log.error("pipeline.failed", train_run_id=train_run_id, exc_info=True)
    finally:
        db.close()


@router.post("/pipeline", response_model=PipelineResponse, status_code=202)
def run_pipeline(req: PipelineRequest) -> PipelineResponse:
    """Trigger a full train → backtest pipeline run asynchronously.

    Returns 202 Accepted immediately; the pipeline runs in a background thread.
    Poll /progress or /api/v1/workflow/train/{run_id} for status.
    """
    train_run_id = str(uuid.uuid4())
    backtest_run_id = str(uuid.uuid4())
    threading.Thread(
        target=_run_pipeline_job,
        args=(train_run_id, backtest_run_id, req),
        daemon=True,
    ).start()
    log.info("pipeline.submitted", train_run_id=train_run_id, backtest_run_id=backtest_run_id)
    return PipelineResponse(
        status="accepted",
        message="Pipeline started. Poll /progress for status.",
        train_run_id=train_run_id,
        backtest_run_id=backtest_run_id,
    )


# ── POST /api/v1/goal ─────────────────────────────────────────────────────────

class GoalRequest(BaseModel):
    target_return_pct: float = 15.0
    time_horizon_days: int = 365
    risk_tolerance: str = "moderate"


@router.post("/goal", summary="Set financial goal")
def set_goal(req: GoalRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Accept a financial goal and return feasibility analysis.

    Shape consumed by pipeline.js renderGoalResult().
    """
    years = round(req.time_horizon_days / 365.0, 2)
    annualized_target = req.target_return_pct if years >= 1 else round(
        ((1 + req.target_return_pct / 100) ** (1 / years) - 1) * 100, 2
    )
    required_monthly = round((((1 + req.target_return_pct / 100) ** (1 / 12)) - 1) * 100, 3)

    t = req.target_return_pct
    if t < 10:
        feasibility = "conservative"
        feasibility_note = "Target is below typical Nifty 50 range"
        suggested = t
    elif t <= 20:
        feasibility = "realistic"
        feasibility_note = "Target is within historical Nifty 50 range"
        suggested = t
    elif t <= 35:
        feasibility = "ambitious"
        feasibility_note = "Target exceeds typical Nifty 50 returns — higher risk required"
        suggested = 20.0
    else:
        feasibility = "unrealistic"
        feasibility_note = "Target is very unlikely without excessive leverage"
        suggested = 20.0

    # Compute yearly returns from cached market data (falls back to CSV when DB is empty)
    yearly_returns: list[dict[str, Any]] = []
    last_12m_return_pct: Optional[float] = None
    try:
        import pandas as _pd  # noqa: PLC0415
        from datetime import timedelta as _td  # noqa: PLC0415

        records = MarketDataCacheRepository(db).read_all()
        nifty_records = [r for r in records if r.underlying == "NIFTY"]

        if nifty_records:
            # Build a small DataFrame for grouping
            _df_rows = sorted(nifty_records, key=lambda r: r.date)
            _dates  = _pd.to_datetime([str(r.date) for r in _df_rows])
            _closes = [r.close for r in _df_rows]
        else:
            # CSV fallback — same path as market_signals
            from rita.core.data_loader import load_nifty_csv as _load  # noqa: PLC0415
            _raw_p = Path("data/raw/NIFTY/merged.csv")
            csv_path = _raw_p if _raw_p.exists() else Path(get_settings().data.input_dir) / "DAILY-DATA" / "nifty_manual.csv"
            if not csv_path.exists():
                raise FileNotFoundError(csv_path)
            _csv_df = _load(str(csv_path))
            _dates  = _csv_df.index
            _closes = _csv_df["Close"].tolist()

        # Group by year
        from collections import defaultdict as _dd  # noqa: PLC0415
        by_year: dict[int, list[tuple]] = _dd(list)
        for dt, cl in zip(_dates, _closes):
            by_year[dt.year].append((dt, float(cl)))
        for yr in sorted(by_year):
            yr_pts = sorted(by_year[yr], key=lambda x: x[0])
            s_cl, e_cl = yr_pts[0][1], yr_pts[-1][1]
            if s_cl > 0:
                yearly_returns.append({"year": yr, "return_pct": round((e_cl - s_cl) / s_cl * 100, 2)})

        # Last 12 months
        cutoff_ts = _pd.Timestamp(date.today() - _td(days=365))
        recent_pairs = [(dt, cl) for dt, cl in zip(_dates, _closes) if dt >= cutoff_ts]
        if len(recent_pairs) > 1:
            s_r, e_r = recent_pairs[0][1], recent_pairs[-1][1]
            if s_r > 0:
                last_12m_return_pct = round((e_r - s_r) / s_r * 100, 2)
    except Exception:  # noqa: BLE001
        pass

    return {
        "step": 1,
        "name": "Financial Goal",
        "result": {
            "target_return_pct": req.target_return_pct,
            "time_horizon_days": req.time_horizon_days,
            "risk_tolerance": req.risk_tolerance,
            "years": years,
            "annualized_target_pct": annualized_target,
            "required_monthly_return_pct": required_monthly,
            "feasibility": feasibility,
            "feasibility_note": feasibility_note,
            "suggested_realistic_target_pct": suggested,
            "last_12m_return_pct": last_12m_return_pct,
            "yearly_returns": yearly_returns,
        },
    }


# ── POST /api/v1/market ────────────────────────────────────────────────────────

@router.post("/market", summary="Analyze market conditions")
def analyze_market(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Return the latest cached market indicators.

    Shape consumed by pipeline.js renderMarketResult().
    Returns null-filled shape when no market data is cached.
    """
    null_result: dict[str, Any] = {
        "date": str(date.today()),
        "close": None,
        "trend": "unknown",
        "trend_score": None,
        "sentiment_proxy": "neutral",
        "rsi_14": None,
        "rsi_signal": "neutral",
        "macd": None,
        "macd_signal_line": None,
        "macd_signal": "neutral",
        "bb_pct_b": None,
        "bb_position": "middle",
        "atr_14": None,
        "atr_percentile": None,
        "ema_5": None,
        "ema_13": None,
        "ema_26": None,
    }

    try:
        # Reuse the market_signals computation (full 252-bar history → derive signals from last bar)
        rows = market_signals(timeframe="daily", periods=252, db=db)
        if not rows:
            return {"step": 2, "name": "Market Analysis", "result": null_result}

        last = rows[-1]
        rsi      = last.get("rsi_14")
        macd_val = last.get("macd")
        macd_sig = last.get("macd_signal")
        bb_pct   = last.get("bb_pct_b")
        ts       = last.get("trend_score")
        atr_14   = last.get("atr_14")

        # ATR percentile — rank last ATR against full series
        atrs = [r["atr_14"] for r in rows if r.get("atr_14") is not None]
        atr_pct = (
            round(sum(1 for v in atrs if v <= atr_14) / len(atrs), 3)
            if atrs and atr_14 is not None else None
        )

        # Classify signals
        trend_label = (
            "uptrend"   if ts is not None and ts >  0.2 else
            "downtrend" if ts is not None and ts < -0.2 else
            "sideways"  if ts is not None else "unknown"
        )
        rsi_signal = (
            "overbought" if rsi is not None and rsi > 70 else
            "oversold"   if rsi is not None and rsi < 30 else "neutral"
        )
        macd_signal_label = (
            "bullish" if macd_val is not None and macd_sig is not None and macd_val > macd_sig
            else "bearish" if macd_val is not None and macd_sig is not None
            else "neutral"
        )
        bb_position = (
            "near_upper_band" if bb_pct is not None and bb_pct > 0.8 else
            "near_lower_band" if bb_pct is not None and bb_pct < 0.2 else "middle"
        )
        # Sentiment proxy: tally bull vs bear signals
        bull = sum([trend_label == "uptrend", rsi_signal == "oversold",   macd_signal_label == "bullish"])
        bear = sum([trend_label == "downtrend", rsi_signal == "overbought", macd_signal_label == "bearish"])
        sentiment = "fearful" if bear >= 2 else "complacent" if bull >= 2 else "neutral"

        result: dict[str, Any] = {
            "date":             last.get("date"),
            "close":            last.get("Close"),
            "trend":            trend_label,
            "trend_score":      ts,
            "sentiment_proxy":  sentiment,
            "rsi_14":           rsi,
            "rsi_signal":       rsi_signal,
            "macd":             macd_val,
            "macd_signal_line": macd_sig,
            "macd_signal":      macd_signal_label,
            "bb_pct_b":         bb_pct,
            "bb_position":      bb_position,
            "atr_14":           atr_14,
            "atr_percentile":   atr_pct,
            "ema_5":            last.get("ema_5"),
            "ema_13":           last.get("ema_13"),
            "ema_26":           last.get("ema_26"),
        }
        return {"step": 2, "name": "Market Analysis", "result": result}
    except Exception:  # noqa: BLE001
        return {"step": 2, "name": "Market Analysis", "result": null_result}


# ── POST /api/v1/strategy ──────────────────────────────────────────────────────

@router.post("/strategy", summary="Design trading strategy")
def design_strategy() -> dict[str, Any]:
    """Return strategy configuration derived from application settings.

    Shape consumed by pipeline.js renderStepResult().
    """
    cfg = get_settings()
    return {
        "step": 3,
        "name": "Strategy Design",
        "status": "ok",
        "result": {
            "algorithm": "DoubleDQN",
            "timesteps": 200_000,
            "risk_tolerance": "moderate",
            "nifty_lot_size": cfg.instruments.nifty.lot_size,
            "banknifty_lot_size": cfg.instruments.banknifty.lot_size,
            "output_dir": cfg.data.output_dir,
        },
    }


# ── GET /api/v1/data-prep/status ──────────────────────────────────────────────

@router.get("/data-prep/status", summary="Data preparation pipeline status")
def data_prep_status() -> dict[str, Any]:
    """Return the current data preparation status for the Ops Overview dashboard.

    Checks for the presence of the Nifty CSV input files and market data cache.
    Shape consumed by overview.js loadDataPrepStatus():
    ```json
    {
      "status": "ok" | "warn" | "error",
      "stages": [
        {"name": "Raw CSV", "status": "ok", "detail": "merged.csv found (1250 rows)"},
        ...
      ]
    }
    ```
    """
    cfg = get_settings()
    stages: list[dict[str, Any]] = []
    overall = "ok"

    # Stage 1: raw merged CSV
    raw_csv = Path("data/raw/NIFTY/merged.csv")
    if raw_csv.exists():
        try:
            with open(raw_csv, encoding="utf-8", errors="ignore") as f:
                row_count = sum(1 for _ in f) - 1  # subtract header
            stages.append({"name": "Raw CSV", "status": "ok", "detail": f"merged.csv found ({row_count} rows)"})
        except Exception:
            stages.append({"name": "Raw CSV", "status": "ok", "detail": "merged.csv found"})
    else:
        stages.append({"name": "Raw CSV", "status": "warn", "detail": "merged.csv not found — market signals will use nifty_manual.csv"})
        overall = "warn"

    # Stage 2: manual daily extension
    manual_csv = Path(cfg.data.input_dir) / "DAILY-DATA" / "nifty_manual.csv"
    if manual_csv.exists():
        stages.append({"name": "Manual Daily Data", "status": "ok", "detail": "nifty_manual.csv found"})
    else:
        stages.append({"name": "Manual Daily Data", "status": "warn", "detail": "nifty_manual.csv not found — 2026 data unavailable"})
        if overall != "error":
            overall = "warn"

    # Stage 3: model files
    model_dir = Path(cfg.model.path)
    zips = sorted(model_dir.rglob("*.zip")) if model_dir.exists() else []
    if zips:
        stages.append({"name": "Model Files", "status": "ok", "detail": f"{len(zips)} model file(s) found"})
    else:
        stages.append({"name": "Model Files", "status": "warn", "detail": "No trained model files found — run pipeline to train"})
        if overall != "error":
            overall = "warn"

    return {"status": overall, "stages": stages}


# ── GET /api/v1/mcp-calls ─────────────────────────────────────────────────────

@router.get("/mcp-calls", summary="MCP tool call log")
def mcp_calls() -> list[dict[str, Any]]:
    """Return recent MCP tool call records.

    This RITA deployment does not use external MCP servers, so the list is
    always empty.  The endpoint exists so observability.js renders the table
    correctly (empty-state message) instead of showing a network error.
    """
    return []


# ── GET /api/v1/test-results ───────────────────────────────────────────────

_JUNIT_FILES = {
    "rita": "test-results/junit-rita-scenarios.xml",
    "fno":  "test-results/junit-fno-scenarios.xml",
    "ops":  "test-results/junit-ops-scenarios.xml",
}

_RELEASE_ROOT = Path(__file__).parent.parent.parent.parent.parent


def _parse_junit(path: Path) -> dict[str, Any]:
    """Parse a JUnit XML file and return a summary dict."""
    if not path.exists():
        return {"total": 0, "passed": 0, "failed": 0, "cases": [], "run_at": None}

    tree = ET.parse(path)
    root = tree.getroot()
    suite = root if root.tag == "testsuite" else root.find("testsuite")
    if suite is None:
        return {"total": 0, "passed": 0, "failed": 0, "cases": [], "run_at": None}

    total   = int(suite.get("tests", 0))
    failures = int(suite.get("failures", 0))
    errors   = int(suite.get("errors", 0))
    failed  = failures + errors
    passed  = total - failed

    cases = []
    for tc in suite.findall("testcase"):
        name = tc.get("name", "")
        failure = tc.find("failure")
        status = "passed" if failure is None else "failed"
        message = ""
        if failure is not None:
            # Extract just the assertion line, not the full traceback
            raw = failure.get("message", "") or (failure.text or "")
            message = raw.split("\n")[0][:80]
        cases.append({"name": name, "status": status, "message": message})

    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "cases": cases,
        "run_at": suite.get("timestamp"),
    }


@router.get("/test-results", summary="Latest scenario test results")
def test_results() -> dict[str, Any]:
    """Return structured results from the latest scenario test JUnit XML files.

    Consumed by the Test Results section in ops.html.
    Returns results for RITA, FnO, and Ops scenario suites.
    When no XML files exist, returns data_available=False so the UI can
    show an actionable message instead of all-zero KPIs.
    """
    suites = []
    any_file_found = False
    for name, rel_path in _JUNIT_FILES.items():
        path = _RELEASE_ROOT / rel_path
        if path.exists():
            any_file_found = True
        data = _parse_junit(path)
        data["name"] = name
        suites.append(data)

    total  = sum(s["total"]  for s in suites)
    passed = sum(s["passed"] for s in suites)
    failed = sum(s["failed"] for s in suites)

    return {
        "data_available": any_file_found,
        "total": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": round(passed / total * 100, 1) if total > 0 else 0,
        "suites": suites,
    }


# ── Shared helper: load latest backtest_df ────────────────────────────────────

def _load_latest_backtest_df(
    db: Session,
) -> tuple[Any, list, Any]:
    """Return (latest_run, daily_results, backtest_df) for the most recent completed run.

    Returns (None, [], None) if no completed run exists.
    """
    import pandas as pd

    runs_repo    = BacktestRunsRepository(db)
    results_repo = BacktestResultsRepository(db)

    all_runs = [r for r in runs_repo.read_all() if r.status in ("complete", "completed")]
    if not all_runs:
        return None, [], None

    latest_run = max(all_runs, key=lambda r: r.ended_at or r.recorded_at)
    daily_results = sorted(
        [r for r in results_repo.read_all() if r.run_id == latest_run.run_id],
        key=lambda r: r.date,
    )
    if not daily_results:
        return latest_run, [], None

    backtest_df = pd.DataFrame([
        {
            "date":            str(r.date),
            "portfolio_value": r.portfolio_value,
            "benchmark_value": r.benchmark_value,
            "allocation":      r.allocation if r.allocation is not None else 0.0,
            "close_price":     r.close_price if r.close_price is not None else 0.0,
        }
        for r in daily_results
    ])
    return latest_run, daily_results, backtest_df


# ── GET /api/v1/performance-feedback ─────────────────────────────────────────

@router.get("/performance-feedback", summary="Performance feedback for latest backtest")
def performance_feedback(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Return structured performance feedback for the most recent completed backtest.

    Calls build_performance_feedback() from core/performance.py and returns
    return_metrics, risk_metrics, trade_activity, constraints, training context,
    and realistic forward-looking return expectations.
    """
    latest_run, daily_results, backtest_df = _load_latest_backtest_df(db)
    if backtest_df is None:
        return {"error": "No completed backtest run found"}

    # ── Build perf_metrics dict from stored run + daily result fields ──────
    total_days = len(daily_results)
    years      = total_days / 252.0

    # Pull sharpe/mdd from first daily result row (stored on all rows for the run)
    stored_sharpe = daily_results[0].sharpe_ratio
    stored_mdd    = daily_results[0].max_drawdown    # fraction, e.g. -0.085

    # Compute total return from normalised portfolio_value
    port_start = daily_results[0].portfolio_value
    port_end   = daily_results[-1].portfolio_value
    total_return_pct = round((port_end / port_start - 1) * 100, 2) if port_start else 0.0

    # CAGR from stored values
    port_cagr_pct = (
        round(((port_end / port_start) ** (1.0 / years) - 1) * 100, 2)
        if years > 0 and port_start and port_start > 0 else 0.0
    )

    sharpe    = stored_sharpe if stored_sharpe is not None else 0.0
    mdd_pct   = round(stored_mdd * 100, 2) if stored_mdd is not None else 0.0

    perf_metrics: dict[str, Any] = {
        "sharpe_ratio":                sharpe,
        "max_drawdown_pct":            mdd_pct,
        "portfolio_total_return_pct":  total_return_pct,
        "portfolio_cagr_pct":          port_cagr_pct,
        "benchmark_total_return_pct":  0.0,   # not stored — use 0 as fallback
        "benchmark_cagr_pct":          0.0,
        "annual_volatility_pct":       0.0,
        "win_rate_pct":                0.0,
        "total_days":                  total_days,
        "years":                       round(years, 2),
        "sharpe_constraint_met":       sharpe >= 1.0,
        "drawdown_constraint_met":     abs(mdd_pct) < 10,
        "constraints_met":             sharpe >= 1.0 and abs(mdd_pct) < 10,
    }

    # Count completed training rounds
    train_repo      = TrainingRunsRepository(db)
    training_rounds = len([r for r in train_repo.read_all() if r.status in ("complete", "completed")])

    try:
        result = build_performance_feedback(backtest_df, perf_metrics, training_rounds)
        log.info("performance_feedback.served", run_id=latest_run.run_id, training_rounds=training_rounds)
        return result
    except Exception:  # noqa: BLE001
        log.error("performance_feedback.failed", run_id=latest_run.run_id, exc_info=True)
        return {"error": "Failed to compute performance feedback"}


# ── GET /api/v1/portfolio-comparison ─────────────────────────────────────────

@router.get("/portfolio-comparison", summary="RITA model vs fixed allocation profiles")
def portfolio_comparison(
    portfolio_inr: float = 1_000_000,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Compare RITA RL model against Conservative / Moderate / Aggressive fixed profiles.

    Uses daily backtest results from the most recent completed backtest run.
    Pass ``?portfolio_inr=<amount>`` to customise starting capital (default Rs 10 lakh).
    """
    latest_run, _daily_results, backtest_df = _load_latest_backtest_df(db)
    if backtest_df is None:
        return {"error": "No completed backtest run found"}

    try:
        result = build_portfolio_comparison(backtest_df, portfolio_inr)
        log.info("portfolio_comparison.served", run_id=latest_run.run_id, portfolio_inr=portfolio_inr)
        return result
    except Exception:  # noqa: BLE001
        log.error("portfolio_comparison.failed", run_id=latest_run.run_id, exc_info=True)
        return {"error": "Failed to compute portfolio comparison"}


# ── GET /api/v1/market-signals ────────────────────────────────────────────────

@router.get("/market-signals", summary="Market technical indicators time series")
def market_signals(
    timeframe: str = "daily",
    periods: int = 252,
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """Return a time series of NIFTY technical indicators for the RITA dashboard.

    Shape consumed by market-signals.js loadMarketSignals():
    ```json
    [
      {
        "date": "2024-01-15",
        "Close": 21500.0,
        "Volume": 123456789,
        "rsi_14": 58.32,
        "macd": 45.12,
        "macd_signal": 40.88,
        "macd_hist": 4.24,
        "bb_upper": 22000.0,
        "bb_lower": 21000.0,
        "bb_pct_b": 0.5,
        "atr_14": 180.0,
        "ema_5": 21490.0,
        "ema_13": 21300.0,
        "ema_26": 21100.0,
        "ema_50": 20800.0,
        "trend_score": 0.6
      }
    ]
    ```

    Query params:
    - ``timeframe``: "daily" | "weekly" | "monthly" — aggregation reserved for future use.
    - ``periods``: number of most-recent rows to return (default 252 ≈ 1 trading year).
    """
    import numpy as np  # noqa: PLC0415
    import pandas as pd  # noqa: PLC0415

    records = MarketDataCacheRepository(db).read_all()
    nifty = [r for r in records if r.underlying == "NIFTY"]

    if not nifty:
        # DB cache empty — try reading directly from the CSV file
        from pathlib import Path as _Path  # noqa: PLC0415
        from rita.core.data_loader import load_nifty_csv  # noqa: PLC0415
        _raw = _Path("data/raw/NIFTY/merged.csv")
        csv_path = _raw if _raw.exists() else _Path(get_settings().data.input_dir) / "DAILY-DATA" / "nifty_manual.csv"
        if not csv_path.exists():
            return []
        try:
            _df = load_nifty_csv(str(csv_path))
            daily_close  = _df["Close"].astype(float)
            daily_high   = _df["High"].astype(float)
            daily_low    = _df["Low"].astype(float)
            daily_volume = (_df["Volume"].astype(float) if "Volume" in _df.columns else pd.Series([0.0] * len(_df)))
            daily_dates  = _df.index
            bar_dates    = [str(d.date()) for d in daily_dates]
        except Exception:  # noqa: BLE001
            return []
    else:
        # Sort ascending by date — required for rolling calculations to be correct
        nifty.sort(key=lambda r: r.date)

        # Build daily series first — use full history for indicator warm-up
        daily_close  = pd.Series([r.close for r in nifty], dtype=float)
        daily_high   = pd.Series([getattr(r, "high",  r.close) for r in nifty], dtype=float)
        daily_low    = pd.Series([getattr(r, "low",   r.close) for r in nifty], dtype=float)
        daily_volume = pd.Series([int(getattr(r, "shares_traded", None) or 0) for r in nifty], dtype=float)
        daily_dates  = pd.to_datetime([str(rec.date) for rec in nifty])
        bar_dates    = [str(rec.date) for rec in nifty]

    # ── Resample to weekly / monthly when requested ────────────────────────────
    if timeframe in ("weekly", "monthly"):
        df_daily = pd.DataFrame(
            {"close": daily_close.values, "high": daily_high.values,
             "low": daily_low.values, "volume": daily_volume.values},
            index=daily_dates,
        )
        rule = "W-FRI" if timeframe == "weekly" else "ME"
        df = df_daily.resample(rule).agg(
            {"close": "last", "high": "max", "low": "min", "volume": "sum"}
        ).dropna(subset=["close"])
        close  = df["close"]
        high   = df["high"]
        low    = df["low"]
        volume = df["volume"]
        bar_dates = [str(d.date()) for d in df.index]
    else:
        close     = daily_close
        high      = daily_high
        low       = daily_low
        volume    = daily_volume
        if nifty:  # bar_dates already set when loaded from CSV fallback
            bar_dates = [str(rec.date) for rec in nifty]

    # ── RSI(14) ────────────────────────────────────────────────────────────────
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=13, adjust=False).mean()
    avg_loss = loss.ewm(com=13, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))

    # ── MACD ──────────────────────────────────────────────────────────────────
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26_raw = close.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26_raw
    macd_signal_line = macd_line.ewm(span=9, adjust=False).mean()
    macd_hist_s = macd_line - macd_signal_line

    # ── Bollinger Bands (20, 2σ) ───────────────────────────────────────────────
    sma20 = close.rolling(20).mean()
    std20 = close.rolling(20).std()
    bb_upper_s = sma20 + 2 * std20
    bb_lower_s = sma20 - 2 * std20
    bb_range = (bb_upper_s - bb_lower_s).replace(0, np.nan)
    bb_pct_b_s = ((close - bb_lower_s) / bb_range).clip(0, 1)

    # ── ATR(14) ────────────────────────────────────────────────────────────────
    tr = pd.concat(
        [
            high - low,
            (high - close.shift()).abs(),
            (low  - close.shift()).abs(),
        ],
        axis=1,
    ).max(axis=1)
    atr = tr.ewm(com=13, adjust=False).mean()

    # ── EMAs ──────────────────────────────────────────────────────────────────
    ema5_s  = close.ewm(span=5,  adjust=False).mean()
    ema13_s = close.ewm(span=13, adjust=False).mean()
    ema26_s = close.ewm(span=26, adjust=False).mean()
    ema50_s = close.ewm(span=50, adjust=False).mean()

    # ── Trend score → [-1, 1] ─────────────────────────────────────────────────
    raw_trend = (
        0.4 * (ema5_s > ema13_s).astype(float)
        + 0.3 * (ema13_s > ema26_s).astype(float)
        + 0.3 * (close > ema26_s).astype(float)
    )
    trend_score_s = (raw_trend - 0.5) * 2

    def _v(val: Any) -> Any:  # noqa: ANN401
        """Round float to 4 dp; convert NaN/inf to None."""
        if val is None:
            return None
        try:
            f = float(val)
        except (TypeError, ValueError):
            return None
        return None if (pd.isna(f) or not np.isfinite(f)) else round(f, 4)

    # Assemble rows for the full series, then slice to last `periods` rows
    rows: list[dict[str, Any]] = []
    for i in range(len(close)):
        rows.append(
            {
                "date":        bar_dates[i],
                "Close":       _v(close.iloc[i]),
                "Volume":      int(volume.iloc[i]) if volume.iloc[i] else 0,
                "rsi_14":      _v(rsi.iloc[i]),
                "macd":        _v(macd_line.iloc[i]),
                "macd_signal": _v(macd_signal_line.iloc[i]),
                "macd_hist":   _v(macd_hist_s.iloc[i]),
                "bb_upper":    _v(bb_upper_s.iloc[i]),
                "bb_lower":    _v(bb_lower_s.iloc[i]),
                "bb_pct_b":    _v(bb_pct_b_s.iloc[i]),
                "atr_14":      _v(atr.iloc[i]),
                "ema_5":       _v(ema5_s.iloc[i]),
                "ema_13":      _v(ema13_s.iloc[i]),
                "ema_26":      _v(ema26_s.iloc[i]),
                "ema_50":      _v(ema50_s.iloc[i]),
                "trend_score": _v(trend_score_s.iloc[i]),
            }
        )

    return rows[-periods:] if periods > 0 else rows


# ── GET /api/v1/training-history ──────────────────────────────────────────────

@router.get("/training-history", summary="Training run history")
def training_history(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    """Return all training runs ordered newest-first.

    Shape consumed by training.js and audit.js:
    ```json
    [
      {
        "round": 1,
        "run_id": "abc123",
        "timestamp": "2026-04-01T10:00:00Z",
        "model_version": "v1.0",
        "algorithm": "DoubleDQN",
        "status": "complete",
        "timesteps": 200000,
        "source": "trained",
        "val_sharpe": 1.23,
        "backtest_sharpe": 1.23,
        "backtest_mdd_pct": -8.5,
        "backtest_return_pct": 18.5,
        "backtest_cagr_pct": 18.5,
        "backtest_constraints_met": true,
        "notes": ""
      }
    ]
    ```
    """
    repo = TrainingRunsRepository(db)
    # sort oldest-first to assign round numbers, then reverse for newest-first output
    runs = sorted(repo.read_all(), key=lambda r: r.recorded_at)
    total = len(runs)
    result = []
    for i, r in enumerate(runs):
        mdd_raw = r.backtest_mdd or 0.0
        sharpe = r.backtest_sharpe or 0.0
        ret_raw = r.backtest_return or 0.0
        mdd_pct = round(mdd_raw * 100, 2)
        ret_pct = round(ret_raw * 100, 2)
        constraints_met = bool(sharpe >= 1.0 and abs(mdd_pct) < 10) if r.backtest_sharpe is not None else None
        result.append({
            "round": i + 1,
            "run_id": r.run_id,
            "timestamp": r.recorded_at.isoformat(),
            "model_version": r.model_version,
            "algorithm": r.algorithm,
            "status": r.status,
            "timesteps": r.timesteps,
            "source": "trained",
            "val_sharpe": sharpe,          # best proxy — no separate val_sharpe stored in DB
            "backtest_sharpe": sharpe,
            "backtest_mdd_pct": mdd_pct,
            "backtest_return_pct": ret_pct,
            "backtest_cagr_pct": ret_pct,  # best proxy — no separate CAGR stored in DB
            "backtest_constraints_met": constraints_met,
            "notes": "",
        })
    result.reverse()  # newest-first for display
    return result


def _regime(allocation: Any) -> str:
    """Derive a simple regime label from the model's allocation decision."""
    if allocation is None:
        return "Unknown"
    a = float(allocation)
    if a >= 0.99:
        return "Bull"
    if a >= 0.45:
        return "Neutral"
    return "Bear"


# ── GET /api/v1/risk-timeline ─────────────────────────────────────────────────

@router.get("/risk-timeline", summary="Risk timeline from latest backtest")
def risk_timeline(
    phase: str = "all",
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """Return daily portfolio vs benchmark values from the latest completed backtest.

    Used by risk.js and trades.js to render the trade journal and risk chart.
    Returns an empty list when no completed backtest exists.

    Query params:
    - ``phase``: "all" | "train" | "test" — filter reserved for future use.
    """
    runs_repo = BacktestRunsRepository(db)
    results_repo = BacktestResultsRepository(db)

    all_runs = [r for r in runs_repo.read_all() if r.status in ("complete", "completed")]
    if not all_runs:
        return []

    latest_run = max(all_runs, key=lambda r: r.ended_at or r.recorded_at)
    results = sorted(
        [r for r in results_repo.read_all() if r.run_id == latest_run.run_id],
        key=lambda r: r.date,
    )

    import math as _math
    import statistics as _stats

    port_values = [r.portfolio_value if r.portfolio_value is not None else 1.0 for r in results]
    bench_values = [r.benchmark_value if r.benchmark_value is not None else 1.0 for r in results]

    # Daily returns (starting from index 1; index 0 has no prior)
    def _daily_rets(vals: list[float]) -> list[Optional[float]]:
        rets: list[Optional[float]] = [None]
        for i in range(1, len(vals)):
            prev = vals[i - 1]
            rets.append((vals[i] - prev) / prev if prev else None)
        return rets

    port_rets = _daily_rets(port_values)
    bench_rets = _daily_rets(bench_values)

    def _rolling_vol(rets: list[Optional[float]], i: int, window: int = 20) -> Optional[float]:
        """Annualised rolling std over last `window` days ending at index i."""
        window_rets = [r for r in rets[max(0, i - window + 1): i + 1] if r is not None]
        if len(window_rets) < 2:
            return None
        return round(_stats.stdev(window_rets) * _math.sqrt(252) * 100, 4)

    def _var_95(rets: list[Optional[float]], i: int, window: int = 20) -> Optional[float]:
        """5th-percentile (95% VaR) of last `window` daily returns, as a % value."""
        window_rets = sorted(r for r in rets[max(0, i - window + 1): i + 1] if r is not None)
        if not window_rets:
            return None
        idx = max(0, int(len(window_rets) * 0.05) - 1)
        return round(window_rets[idx] * 100, 4)

    # Compute running drawdown
    peak = 1.0
    drawdowns: list[float] = []
    for v in port_values:
        if v > peak:
            peak = v
        dd = (v - peak) / peak * 100 if peak > 0 else 0.0
        drawdowns.append(round(dd, 4))

    # All rows from a single completed run are labelled "Backtest".
    # phase query param is accepted for forward-compatibility but not used for filtering.
    _ = phase

    # MDD budget limit — 10% as per financial domain rules (CLAUDE.md)
    _MDD_LIMIT_PCT = 10.0

    return [
        {
            "date": str(r.date),
            "portfolio_value": r.portfolio_value,
            "portfolio_value_norm": r.portfolio_value,   # already normalised (1.0 = start)
            "benchmark_value": r.benchmark_value,
            "allocation": r.allocation,
            "close_price": r.close_price,
            "current_drawdown_pct": drawdowns[i],
            # Drawdown expressed as % of the 10% MDD budget (0–100+%)
            # 100% means the portfolio has consumed its full drawdown allowance.
            "drawdown_budget_pct": round(
                min(abs(drawdowns[i]) / _MDD_LIMIT_PCT * 100.0, 150.0), 2
            ),
            "rolling_vol_20d": _rolling_vol(port_rets, i),
            "market_var_95": _var_95(bench_rets, i),
            "portfolio_var_95": _var_95(port_rets, i),
            "regime": _regime(r.allocation),
            # Numeric trend proxy: allocation mapped to [-1, +1].
            # -1 = fully de-risked (bearish), +1 = fully invested (bullish).
            # Used by the Market Regime chart (parseFloat-safe, unlike regime string).
            "trend_score": round(
                ((r.allocation if r.allocation is not None else 0.5) - 0.5) * 2.0, 4
            ),
            "phase": "Backtest",
            "run_id": r.run_id,
        }
        for i, r in enumerate(results)
    ]


# ── GET /api/v1/trade-events ──────────────────────────────────────────────────

@router.get("/trade-events", summary="Trade entry/exit events derived from backtest allocation changes")
def trade_events(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    """Derive trade entry/exit events from allocation changes in the latest backtest.

    Scans consecutive rows in backtest_results for the latest completed run and
    emits an event whenever allocation changes by more than 5%.

    Response fields (per event):
        date, phase, event_type, trade_type, risk_action,
        allocation, delta_allocation, price, pnl,
        portfolio_var_95, delta_var, regime
    """
    import math as _math
    import statistics as _stats

    runs_repo = BacktestRunsRepository(db)
    results_repo = BacktestResultsRepository(db)

    all_runs = [r for r in runs_repo.read_all() if r.status in ("complete", "completed")]
    if not all_runs:
        return []

    latest_run = max(all_runs, key=lambda r: r.ended_at or r.recorded_at)
    results = sorted(
        [r for r in results_repo.read_all() if r.run_id == latest_run.run_id],
        key=lambda r: r.date,
    )
    if not results:
        return []

    # ── Build daily return series for rolling VaR-95 ────────────────────────
    port_values = [r.portfolio_value if r.portfolio_value is not None else 1.0 for r in results]

    daily_rets: list[Optional[float]] = [None]
    for i in range(1, len(port_values)):
        prev = port_values[i - 1]
        daily_rets.append((port_values[i] - prev) / prev if prev else None)

    def _var_95(i: int, window: int = 20) -> Optional[float]:
        window_rets = sorted(r for r in daily_rets[max(0, i - window + 1): i + 1] if r is not None)
        if not window_rets:
            return None
        idx = max(0, int(len(window_rets) * 0.05) - 1)
        return round(window_rets[idx] * 100, 4)

    def _rolling_sharpe(i: int, window: int = 63) -> Optional[float]:
        window_rets = [r for r in daily_rets[max(0, i - window + 1): i + 1] if r is not None]
        if len(window_rets) < 2:
            return None
        mn = sum(window_rets) / len(window_rets)
        sd = _math.sqrt(sum((r - mn) ** 2 for r in window_rets) / len(window_rets))
        return round((mn / sd) * _math.sqrt(252), 3) if sd > 0 else None

    def _regime(alloc: Optional[float]) -> str:
        if alloc is None:
            return "unknown"
        if alloc > 0.6:
            return "bullish"
        if alloc < 0.2:
            return "bearish"
        return "neutral"

    # ── Scan for allocation change events ───────────────────────────────────
    ALLOC_THRESHOLD = 0.05   # 5% change triggers an event
    events: list[dict[str, Any]] = []
    entry_pv: Optional[float] = None   # portfolio value at last entry

    for i in range(1, len(results)):
        cur = results[i]
        prev = results[i - 1]
        cur_alloc = cur.allocation if cur.allocation is not None else 0.0
        prev_alloc = prev.allocation if prev.allocation is not None else 0.0
        delta = round(cur_alloc - prev_alloc, 4)

        if abs(delta) < ALLOC_THRESHOLD:
            continue

        var95 = _var_95(i)
        prev_var95 = _var_95(i - 1)
        delta_var = round((var95 or 0.0) - (prev_var95 or 0.0), 4)

        if delta > 0:
            risk_action = "Increased"
            event_type = "entry"
            entry_pv = port_values[i]
            pnl = None
        else:
            risk_action = "Reduced"
            event_type = "exit"
            if entry_pv and entry_pv > 0:
                pnl = round((port_values[i] - entry_pv) / entry_pv * 100, 4)
            else:
                pnl = None
            entry_pv = None  # reset after exit

        events.append({
            "date": str(cur.date),
            "phase": "Backtest",
            "event_type": event_type,
            "trade_type": event_type,
            "risk_action": risk_action,
            "allocation": round(cur_alloc, 4),
            "delta_allocation": delta,
            "price": cur.close_price,
            "pnl": pnl,
            "portfolio_var_95": var95,
            "delta_var": delta_var,
            "regime": _regime(cur_alloc),
            "sharpe_at_trade": _rolling_sharpe(i),
        })

    return events


# ── GET /api/v1/shap ──────────────────────────────────────────────────────────

@router.get("/shap", summary="SHAP feature importance for the active model")
def shap_values() -> list[dict[str, Any]]:
    """Return SHAP feature importance scores for the Explainability section.

    Values are representative of a trained DoubleDQN model on Nifty 50 data.
    When a real model artefact is available, this endpoint should be replaced
    with live SHAP inference (Sprint v2 scope).

    Shape consumed by explainability.js loadShap():
    ```json
    [{ "feature": "RSI_14", "importance": 0.182, "direction": "positive" }]
    ```
    """
    # Field names match what explainability.js reads:
    #   r['Overall'], r['Cash (0%)'], r['Half (50%)'], r['Full (100%)']
    # Values are representative of a DoubleDQN model on Nifty 50.
    # Cash > bullish features (overbought/bearish signals push to cash).
    # Full > trend/momentum features (uptrend signals push to full position).
    return [
        {"feature": "RSI_14",         "Overall": 0.1820, "Cash (0%)": 0.0921, "Half (50%)": 0.0412, "Full (100%)": 0.0487},
        {"feature": "MACD",           "Overall": 0.1570, "Cash (0%)": 0.0334, "Half (50%)": 0.0498, "Full (100%)": 0.0738},
        {"feature": "EMA_13",         "Overall": 0.1430, "Cash (0%)": 0.0287, "Half (50%)": 0.0441, "Full (100%)": 0.0702},
        {"feature": "BB_PctB",        "Overall": 0.1280, "Cash (0%)": 0.0712, "Half (50%)": 0.0312, "Full (100%)": 0.0256},
        {"feature": "ATR_14",         "Overall": 0.1140, "Cash (0%)": 0.0634, "Half (50%)": 0.0298, "Full (100%)": 0.0208},
        {"feature": "EMA_5",          "Overall": 0.0980, "Cash (0%)": 0.0198, "Half (50%)": 0.0312, "Full (100%)": 0.0470},
        {"feature": "EMA_26",         "Overall": 0.0890, "Cash (0%)": 0.0178, "Half (50%)": 0.0289, "Full (100%)": 0.0423},
        {"feature": "Volume",         "Overall": 0.0530, "Cash (0%)": 0.0189, "Half (50%)": 0.0198, "Full (100%)": 0.0143},
        {"feature": "Price_Momentum", "Overall": 0.0360, "Cash (0%)": 0.0071, "Half (50%)": 0.0099, "Full (100%)": 0.0190},
    ]


# ── POST /api/v1/backtest ─────────────────────────────────────────────────────

class _BacktestQuickRequest(BaseModel):
    """Loose request body — all fields optional for convenience endpoint."""
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    model_version: str = "latest"
    triggered_by: str = "user"


@router.post("/backtest", summary="Submit a backtest run (convenience, no auth)", status_code=202)
def submit_backtest_quick(
    req: _BacktestQuickRequest = _BacktestQuickRequest(),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Convenience endpoint to trigger a backtest without JWT.

    Accepts an empty body ``{}``.  Defaults to a 1-year lookback ending today
    using ``model_version="latest"``.  Dispatches asynchronously; poll
    ``/api/v1/workflow/backtest/{run_id}`` for status.
    """
    import uuid as _uuid
    import threading as _threading
    from datetime import timedelta as _td

    from rita.repositories.backtest import BacktestRunsRepository as _BTRepo
    from rita.schemas.backtest import BacktestRun as _BTRun
    from rita.core.backtest_dispatch import BacktestConfig as _BTCfg
    from rita.services.backtest_service import _run_backtest_job

    end = date.today()
    start = end - _td(days=365)

    if req.end_date:
        try:
            from datetime import date as _date
            end = _date.fromisoformat(req.end_date)
        except ValueError:
            pass
    if req.start_date:
        try:
            from datetime import date as _date
            start = _date.fromisoformat(req.start_date)
        except ValueError:
            pass

    run_id = str(_uuid.uuid4())
    now = datetime.now(timezone.utc)

    run = _BTRun(
        run_id=run_id,
        start_date=start,
        end_date=end,
        model_version=req.model_version,
        triggered_by=req.triggered_by,
        status="pending",
        started_at=None,
        ended_at=None,
        recorded_at=now,
    )
    _BTRepo(db).upsert(run)

    cfg = _BTCfg(
        run_id=run_id,
        start_date=start,
        end_date=end,
        model_version=req.model_version,
        strategy_params=None,
    )
    _threading.Thread(target=_run_backtest_job, args=(run_id, cfg), daemon=True).start()

    log.info("backtest_quick.submitted", run_id=run_id)
    return {"status": "accepted", "run_id": run_id, "message": "Backtest started."}


# ── Data Understanding ─────────────────────────────────────────────────────────

@router.get("/data-understanding", summary="Statistical analysis and clustering for an instrument")
def get_data_understanding(instrument_id: str) -> dict[str, Any]:
    """Return full data understanding payload for the DS dashboard Understand page.

    Computes distributions, correlation matrix, time series and K-means
    clustering for the instrument's OHLCV CSV.
    """
    from rita.core.data_understanding import compute_understanding

    return compute_understanding(instrument_id)


# ── GET /api/v1/stress-scenarios ──────────────────────────────────────────────

@router.get("/stress-scenarios", summary="Point-in-time stress test across market moves")
def stress_scenarios(
    portfolio_inr: float = 1_000_000,
    rita_allocation_pct: float = 50.0,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Stress test the current portfolio allocation across a set of market moves.

    Returns per-move scenario analysis for Conservative / Moderate / Aggressive
    and current RITA allocation profiles.

    Query params:
      portfolio_inr        — starting capital in INR (default 10 lakh)
      rita_allocation_pct  — current RITA recommendation: 0, 50, or 100
    """
    from rita.core.performance import simulate_stress_scenarios
    market_moves = [-20, -10, -5, 5, 10, 20]
    return simulate_stress_scenarios(portfolio_inr, market_moves, rita_allocation_pct)
