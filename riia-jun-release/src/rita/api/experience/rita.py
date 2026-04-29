"""Experience Layer — RITA dashboard aggregation router.

ADR-001 Tier 3: read-only composition, no writes, no side effects.
Serves performance, risk, trade, and instrument-selection views for the RITA dashboard.
URLs preserved from observability.py (Option A migration).
"""
from __future__ import annotations

import math as _math
import statistics as _stats
from typing import Any, Optional

import structlog
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from rita.config import get_settings
from rita.database import get_db
from rita.repositories.instrument import InstrumentRepository
from rita.repositories.config_overrides import ConfigOverridesRepository
from rita.repositories.backtest import BacktestRunsRepository, BacktestResultsRepository
from rita.repositories.training import TrainingRunsRepository
from rita.core.performance import (
    build_performance_feedback,
    build_portfolio_comparison,
    simulate_stress_scenarios,
)

log = structlog.get_logger()

router = APIRouter(prefix="/api/v1", tags=["experience:rita"])

_COUNTRY_FLAG  = {"IN": "\U0001f1ee\U0001f1f3", "US": "\U0001f1fa\U0001f1f8", "NL": "\U0001f1f3\U0001f1f1"}
_MDD_LIMIT_PCT = 10.0


# ── Shared helpers ────────────────────────────────────────────────────────────

def _get_active_instrument_id(db: Session) -> str:
    try:
        cfg = ConfigOverridesRepository(db).find_by_id("active_instrument_id")
        if cfg and cfg.value:
            return cfg.value.upper()
    except Exception:
        pass
    return "NIFTY"


def _regime(allocation: Any) -> str:
    if allocation is None:
        return "Unknown"
    a = float(allocation)
    if a >= 0.99:
        return "Bull"
    if a >= 0.45:
        return "Neutral"
    return "Bear"


def _load_latest_backtest_df(db: Session) -> tuple[Any, list, Any]:
    """Return (latest_run, daily_results, backtest_df) for the most recent completed run."""
    import pandas as pd

    runs_repo    = BacktestRunsRepository(db)
    results_repo = BacktestResultsRepository(db)

    all_runs = [r for r in runs_repo.read_all() if r.status in ("complete", "completed")]
    if not all_runs:
        return None, [], None

    latest_run    = max(all_runs, key=lambda r: r.ended_at or r.recorded_at)
    daily_results = sorted(
        [r for r in results_repo.read_all() if r.run_id == latest_run.run_id],
        key=lambda r: r.date,
    )
    if not daily_results:
        return latest_run, [], None

    backtest_df = pd.DataFrame([{
        "date":            str(r.date),
        "portfolio_value": r.portfolio_value,
        "benchmark_value": r.benchmark_value,
        "allocation":      r.allocation if r.allocation is not None else 0.0,
        "close_price":     r.close_price if r.close_price is not None else 0.0,
    } for r in daily_results])
    return latest_run, daily_results, backtest_df


# ── GET /api/v1/instrument/active ─────────────────────────────────────────────

@router.get("/instrument/active", summary="Currently active instrument")
def active_instrument(db: Session = Depends(get_db)) -> dict[str, Any]:
    active_id = _get_active_instrument_id(db)
    repo      = InstrumentRepository(db)
    inst      = repo.find_by_id(active_id)
    if inst is None:
        cfg = get_settings()
        return {
            "id": "NIFTY", "name": "Nifty 50", "flag": "\U0001f1ee\U0001f1f3",
            "exchange": "NSE", "lot_size": cfg.instruments.nifty.lot_size,
        }
    return {
        "id":       inst.instrument_id,
        "name":     inst.name,
        "flag":     _COUNTRY_FLAG.get(inst.country_code, ""),
        "exchange": inst.exchange,
        "lot_size": inst.lot_size,
    }


# ── GET /api/v1/performance-summary ──────────────────────────────────────────

@router.get("/performance-summary", summary="Latest backtest performance KPIs")
def performance_summary(db: Session = Depends(get_db)) -> dict[str, Any]:
    active_id  = _get_active_instrument_id(db)
    runs_repo  = BacktestRunsRepository(db)
    results_repo = BacktestResultsRepository(db)

    all_runs = [
        r for r in runs_repo.read_all()
        if r.status in ("complete", "completed")
        and (r.instrument or "NIFTY").upper() == active_id
    ]
    run_instrument = active_id if all_runs else "NONE"

    _empty = {
        "portfolio_total_return_pct": None, "benchmark_total_return_pct": None,
        "portfolio_cagr_pct": None, "benchmark_cagr_pct": None,
        "sharpe_ratio": None, "max_drawdown_pct": None,
        "annual_volatility_pct": None, "win_rate_pct": None,
        "total_days": 0, "constraints_met": False,
        "_run_instrument_id": run_instrument, "_active_instrument_id": active_id,
    }

    if not all_runs:
        return _empty

    latest_run = max(all_runs, key=lambda r: r.ended_at or r.recorded_at)
    results    = sorted(
        [r for r in results_repo.read_all() if r.run_id == latest_run.run_id],
        key=lambda r: r.date,
    )
    if not results:
        return _empty

    port_final      = results[-1].portfolio_value
    bench_final     = results[-1].benchmark_value
    port_return_pct = round((port_final - 1.0) * 100, 2)
    bench_return_pct = round((bench_final - 1.0) * 100, 2)
    total_days      = (results[-1].date - results[0].date).days or 1
    years           = total_days / 365.25
    port_cagr  = round((port_final ** (1 / years) - 1) * 100, 2) if years > 0 else port_return_pct
    bench_cagr = round((bench_final ** (1 / years) - 1) * 100, 2) if years > 0 else bench_return_pct

    sharpe: Optional[float] = results[0].sharpe_ratio
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
            std_r  = statistics.stdev(daily_returns)
            sharpe = round((mean_r / std_r) * (252 ** 0.5), 3) if std_r > 0 else None

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

    wins = sum(1 for i in range(1, len(results)) if results[i].portfolio_value > results[i - 1].portfolio_value)
    win_rate_pct = round(wins / (len(results) - 1) * 100, 1) if len(results) > 1 else None
    constraints_met = sharpe is not None and sharpe >= 1.0 and abs(max_dd_pct) < 10

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
        "backtest_start_date": str(results[0].date),
        "backtest_end_date": str(results[-1].date),
        "constraints_met": constraints_met,
        "_run_instrument_id": run_instrument,
        "_active_instrument_id": active_id,
    }


# ── GET /api/v1/backtest-daily ────────────────────────────────────────────────

@router.get("/backtest-daily", summary="Daily backtest results for charting")
def backtest_daily(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    active_id  = _get_active_instrument_id(db)
    runs_repo  = BacktestRunsRepository(db)
    results_repo = BacktestResultsRepository(db)

    all_runs = [
        r for r in runs_repo.read_all()
        if r.status in ("complete", "completed")
        and (r.instrument or "NIFTY").upper() == active_id
    ]
    if not all_runs:
        return []

    latest_run = max(all_runs, key=lambda r: r.ended_at or r.recorded_at)
    results    = sorted(
        [r for r in results_repo.read_all() if r.run_id == latest_run.run_id],
        key=lambda r: r.date,
    )
    return [{
        "date":            str(r.date),
        "portfolio_value": r.portfolio_value,
        "benchmark_value": r.benchmark_value,
        "allocation":      r.allocation,
        "close_price":     r.close_price,
    } for r in results]


# ── GET /api/v1/performance-feedback ─────────────────────────────────────────

@router.get("/performance-feedback", summary="Performance feedback for latest backtest")
def performance_feedback(db: Session = Depends(get_db)) -> dict[str, Any]:
    latest_run, daily_results, backtest_df = _load_latest_backtest_df(db)
    if backtest_df is None:
        return {"error": "No completed backtest run found"}

    total_days = len(daily_results)
    years      = total_days / 252.0
    stored_sharpe = daily_results[0].sharpe_ratio
    stored_mdd    = daily_results[0].max_drawdown
    port_start    = daily_results[0].portfolio_value
    port_end      = daily_results[-1].portfolio_value
    total_return_pct = round((port_end / port_start - 1) * 100, 2) if port_start else 0.0
    port_cagr_pct = (
        round(((port_end / port_start) ** (1.0 / years) - 1) * 100, 2)
        if years > 0 and port_start and port_start > 0 else 0.0
    )
    sharpe  = stored_sharpe if stored_sharpe is not None else 0.0
    mdd_pct = round(stored_mdd * 100, 2) if stored_mdd is not None else 0.0

    perf_metrics: dict[str, Any] = {
        "sharpe_ratio": sharpe, "max_drawdown_pct": mdd_pct,
        "portfolio_total_return_pct": total_return_pct, "portfolio_cagr_pct": port_cagr_pct,
        "benchmark_total_return_pct": 0.0, "benchmark_cagr_pct": 0.0,
        "annual_volatility_pct": 0.0, "win_rate_pct": 0.0,
        "total_days": total_days, "years": round(years, 2),
        "sharpe_constraint_met": sharpe >= 1.0,
        "drawdown_constraint_met": abs(mdd_pct) < 10,
        "constraints_met": sharpe >= 1.0 and abs(mdd_pct) < 10,
    }
    train_repo      = TrainingRunsRepository(db)
    training_rounds = len([r for r in train_repo.read_all() if r.status in ("complete", "completed")])

    try:
        result = build_performance_feedback(backtest_df, perf_metrics, training_rounds)
        log.info("performance_feedback.served", run_id=latest_run.run_id, training_rounds=training_rounds)
        return result
    except Exception:
        log.error("performance_feedback.failed", run_id=latest_run.run_id, exc_info=True)
        return {"error": "Failed to compute performance feedback"}


# ── GET /api/v1/portfolio-comparison ─────────────────────────────────────────

@router.get("/portfolio-comparison", summary="RITA model vs fixed allocation profiles")
def portfolio_comparison(
    portfolio_inr: float = 1_000_000,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    latest_run, _daily_results, backtest_df = _load_latest_backtest_df(db)
    if backtest_df is None:
        return {"error": "No completed backtest run found"}
    try:
        result = build_portfolio_comparison(backtest_df, portfolio_inr)
        log.info("portfolio_comparison.served", run_id=latest_run.run_id, portfolio_inr=portfolio_inr)
        return result
    except Exception:
        log.error("portfolio_comparison.failed", run_id=latest_run.run_id, exc_info=True)
        return {"error": "Failed to compute portfolio comparison"}


# ── GET /api/v1/risk-timeline ─────────────────────────────────────────────────

@router.get("/risk-timeline", summary="Risk timeline from latest backtest")
def risk_timeline(
    phase: str = "all",
    instrument: str = "NIFTY",
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    runs_repo    = BacktestRunsRepository(db)
    results_repo = BacktestResultsRepository(db)

    all_runs = [
        r for r in runs_repo.read_all()
        if r.status in ("complete", "completed") and (r.instrument or "NIFTY") == instrument
    ]
    if not all_runs:
        return []

    latest_run = max(all_runs, key=lambda r: r.ended_at or r.recorded_at)
    results    = sorted(
        [r for r in results_repo.read_all() if r.run_id == latest_run.run_id],
        key=lambda r: r.date,
    )

    port_values  = [r.portfolio_value if r.portfolio_value is not None else 1.0 for r in results]
    bench_values = [r.benchmark_value if r.benchmark_value is not None else 1.0 for r in results]

    def _daily_rets(vals: list[float]) -> list[Optional[float]]:
        rets: list[Optional[float]] = [None]
        for i in range(1, len(vals)):
            prev = vals[i - 1]
            rets.append((vals[i] - prev) / prev if prev else None)
        return rets

    port_rets  = _daily_rets(port_values)
    bench_rets = _daily_rets(bench_values)

    def _rolling_vol(rets: list[Optional[float]], i: int, window: int = 20) -> Optional[float]:
        window_rets = [r for r in rets[max(0, i - window + 1): i + 1] if r is not None]
        if len(window_rets) < 2:
            return None
        return round(_stats.stdev(window_rets) * _math.sqrt(252) * 100, 4)

    def _var_95(rets: list[Optional[float]], i: int, window: int = 20) -> Optional[float]:
        window_rets = sorted(r for r in rets[max(0, i - window + 1): i + 1] if r is not None)
        if not window_rets:
            return None
        idx = max(0, int(len(window_rets) * 0.05) - 1)
        return round(window_rets[idx] * 100, 4)

    peak = 1.0
    drawdowns: list[float] = []
    for v in port_values:
        if v > peak:
            peak = v
        dd = (v - peak) / peak * 100 if peak > 0 else 0.0
        drawdowns.append(round(dd, 4))

    _ = phase  # accepted for forward-compatibility, not yet used for filtering

    return [{
        "date":                  str(r.date),
        "portfolio_value":       r.portfolio_value,
        "portfolio_value_norm":  r.portfolio_value,
        "benchmark_value":       r.benchmark_value,
        "allocation":            r.allocation,
        "close_price":           r.close_price,
        "current_drawdown_pct":  drawdowns[i],
        "drawdown_budget_pct":   round(min(abs(drawdowns[i]) / _MDD_LIMIT_PCT * 100.0, 150.0), 2),
        "rolling_vol_20d":       _rolling_vol(port_rets, i),
        "market_var_95":         _var_95(bench_rets, i),
        "portfolio_var_95":      _var_95(port_rets, i),
        "regime":                _regime(r.allocation),
        "trend_score":           round(((r.allocation if r.allocation is not None else 0.5) - 0.5) * 2.0, 4),
        "phase":                 "Backtest",
        "run_id":                r.run_id,
    } for i, r in enumerate(results)]


# ── GET /api/v1/trade-events ──────────────────────────────────────────────────

@router.get("/trade-events", summary="Trade entry/exit events derived from backtest allocation changes")
def trade_events(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    runs_repo    = BacktestRunsRepository(db)
    results_repo = BacktestResultsRepository(db)

    all_runs = [r for r in runs_repo.read_all() if r.status in ("complete", "completed")]
    if not all_runs:
        return []

    latest_run = max(all_runs, key=lambda r: r.ended_at or r.recorded_at)
    results    = sorted(
        [r for r in results_repo.read_all() if r.run_id == latest_run.run_id],
        key=lambda r: r.date,
    )
    if not results:
        return []

    port_values   = [r.portfolio_value if r.portfolio_value is not None else 1.0 for r in results]
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

    def _trade_regime(alloc: Optional[float]) -> str:
        if alloc is None:
            return "unknown"
        if alloc > 0.6:
            return "bullish"
        if alloc < 0.2:
            return "bearish"
        return "neutral"

    ALLOC_THRESHOLD = 0.05
    events: list[dict[str, Any]] = []
    entry_pv: Optional[float] = None

    for i in range(1, len(results)):
        cur  = results[i]
        prev = results[i - 1]
        cur_alloc  = cur.allocation  if cur.allocation  is not None else 0.0
        prev_alloc = prev.allocation if prev.allocation is not None else 0.0
        delta = round(cur_alloc - prev_alloc, 4)

        if abs(delta) < ALLOC_THRESHOLD:
            continue

        var95      = _var_95(i)
        prev_var95 = _var_95(i - 1)
        delta_var  = round((var95 or 0.0) - (prev_var95 or 0.0), 4)

        if delta > 0:
            risk_action = "Increased"
            event_type  = "entry"
            entry_pv    = port_values[i]
            pnl         = None
        else:
            risk_action = "Reduced"
            event_type  = "exit"
            pnl = round((port_values[i] - entry_pv) / entry_pv * 100, 4) if entry_pv and entry_pv > 0 else None
            entry_pv = None

        events.append({
            "date": str(cur.date), "phase": "Backtest",
            "event_type": event_type, "trade_type": event_type,
            "risk_action": risk_action,
            "allocation": round(cur_alloc, 4), "delta_allocation": delta,
            "price": cur.close_price, "pnl": pnl,
            "portfolio_var_95": var95, "delta_var": delta_var,
            "regime": _trade_regime(cur_alloc), "sharpe_at_trade": _rolling_sharpe(i),
        })

    return events


# ── GET /api/v1/stress-scenarios ──────────────────────────────────────────────

@router.get("/stress-scenarios", summary="Point-in-time stress test across market moves")
def stress_scenarios(
    portfolio_inr: float = 1_000_000,
    rita_allocation_pct: float = 50.0,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    market_moves = [-20, -10, -5, 5, 10, 20]
    return simulate_stress_scenarios(portfolio_inr, market_moves, rita_allocation_pct)
