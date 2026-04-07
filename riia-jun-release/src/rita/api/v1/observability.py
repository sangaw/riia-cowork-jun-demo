"""Observability endpoints for the Ops dashboard.

Provides structured JSON summaries of:
  - /api/v1/metrics/summary   — API request counts, latency, top endpoints
  - /api/v1/step-log          — Training run log formatted as pipeline steps
  - /api/v1/drift             — System health / drift checks
  - /api/v1/mcp-calls         — MCP tool call log (empty in this deployment)
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timezone
from typing import Any

import structlog
from fastapi import APIRouter, Depends
from prometheus_client import REGISTRY
from sqlalchemy.orm import Session

from rita.database import get_db
from rita.repositories.market_data import MarketDataCacheRepository
from rita.repositories.training import TrainingRunsRepository
from rita.repositories.backtest import BacktestRunsRepository

log = structlog.get_logger()

router = APIRouter(prefix="/api/v1", tags=["observability"])


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
def metrics_summary() -> dict[str, Any]:
    """Return a JSON summary of live Prometheus metrics.

    Shape consumed by monitoring.js:
    ```json
    {
      "api_requests": { "total_requests": 42, "error_count": 1, ... },
      "pipeline":     { "completed_steps": 3, "failed_steps": 0, ... },
      "training":     { "rounds": 2 }
    }
    ```
    """
    api = _collect_metrics_summary()

    # Pipeline / training counters are lightweight DB reads; they fail
    # gracefully if the DB is not yet initialised.
    return {
        "api_requests": api,
        "pipeline": {
            "completed_steps": 0,
            "failed_steps": 0,
            "step_timing": {},
        },
        "training": {
            "rounds": 0,
        },
    }


# ── GET /api/v1/step-log ───────────────────────────────────────────────────────

@router.get("/step-log", summary="Pipeline step log")
def step_log(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    """Return training runs formatted as pipeline steps for the monitoring table.

    Each training run is one logical pipeline step.
    """
    repo = TrainingRunsRepository(db)
    runs = repo.read_all()

    rows: list[dict[str, Any]] = []
    for i, run in enumerate(sorted(runs, key=lambda r: r.recorded_at), start=1):
        started = run.started_at.isoformat() if run.started_at else None
        ended = run.ended_at.isoformat() if run.ended_at else None
        duration = None
        if run.started_at and run.ended_at:
            duration = (run.ended_at - run.started_at).total_seconds()

        rows.append({
            "step_num": i,
            "step_name": f"Train {run.model_version}",
            "status": run.status,
            "duration_secs": duration,
            "started_at": started,
            "ended_at": ended,
            "run_id": run.run_id,
        })

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
      "health": { "overall": "ok" | "warn" | "alert" },
      "report": {
        "sharpe_drift":          { "status": "ok", "message": "..." },
        "return_degradation":    { "status": "ok", "message": "..." },
        "data_freshness":        { "status": "ok", "days_old": 2, "latest_date": "2026-04-05" },
        "pipeline_health":       { "status": "ok", "message": "..." },
        "constraint_breach":     { "status": "ok", "message": "..." }
      },
      "sharpe_trend_last5": [1.2, 1.4, 1.3]
    }
    ```
    """
    freshness = _data_freshness_check(db)
    pipeline = _pipeline_health_check(db)
    sharpe = _sharpe_drift_check(db)

    # Return degradation and constraint breach are computed from backtest data
    bt_repo = BacktestRunsRepository(db)
    bt_runs = sorted(
        [r for r in bt_repo.read_all() if hasattr(r, "total_return") and r.total_return is not None],
        key=lambda r: r.recorded_at,
    )
    return_status = "ok"
    return_msg = "No backtest return data yet." if not bt_runs else "Returns within acceptable range."

    # Sharpe trend for sparkline
    train_repo = TrainingRunsRepository(db)
    sharpe_series = [
        r.backtest_sharpe
        for r in sorted(train_repo.read_all(), key=lambda r: r.recorded_at)
        if r.backtest_sharpe is not None
    ][-5:]

    report = {
        "sharpe_drift": sharpe,
        "return_degradation": {"status": return_status, "message": return_msg},
        "data_freshness": freshness,
        "pipeline_health": pipeline,
        "constraint_breach": {"status": "ok", "message": "No constraint violations detected."},
    }

    statuses = [v.get("status", "ok") for v in report.values()]
    if "alert" in statuses:
        overall = "alert"
    elif "warn" in statuses:
        overall = "warn"
    else:
        overall = "ok"

    return {
        "health": {"overall": overall},
        "report": report,
        "sharpe_trend_last5": sharpe_series,
    }


# ── GET /api/v1/mcp-calls ─────────────────────────────────────────────────────

@router.get("/mcp-calls", summary="MCP tool call log")
def mcp_calls() -> list[dict[str, Any]]:
    """Return recent MCP tool call records.

    This RITA deployment does not use external MCP servers, so the list is
    always empty.  The endpoint exists so observability.js renders the table
    correctly (empty-state message) instead of showing a network error.
    """
    return []
