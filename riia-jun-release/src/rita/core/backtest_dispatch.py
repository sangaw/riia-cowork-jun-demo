"""Backtest dispatch stub for historical strategy evaluation.

Replace the ``run_backtest`` function body with a real backtesting engine
(e.g. vectorbt, backtrader, or a custom loop reading from ``rita_input/``
CSV files).

Production replacement notes:
  - Load Nifty 50 OHLCV data from ``rita_input/`` for the date range in
    ``config.start_date`` to ``config.end_date``.
  - Load the trained model from disk using ``config.model_version``.
  - Parse ``config.strategy_params`` (JSON string) for any overrides.
  - Step through each trading day, apply the model policy, track
    portfolio_value and benchmark_value (buy-and-hold normalised to 1.0).
  - Compute Sharpe ratio and max drawdown from the daily series.
  - Return a ``BacktestOutcome`` with all daily results.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import date, timedelta


# ---------------------------------------------------------------------------
# Configuration & result dataclasses
# ---------------------------------------------------------------------------


@dataclass
class BacktestConfig:
    run_id: str
    start_date: date
    end_date: date
    model_version: str
    strategy_params: str | None


@dataclass
class DailyResult:
    date: date
    portfolio_value: float
    benchmark_value: float
    allocation: float
    close_price: float


@dataclass
class BacktestOutcome:
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    daily_results: list[DailyResult] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Stub implementation
# ---------------------------------------------------------------------------


def run_backtest(config: BacktestConfig) -> BacktestOutcome:
    """Run historical backtest and return outcome metrics.

    **Stub** — replace this body with a real backtesting engine.
    See module-level docstring for migration notes.

    The stub:
    - Sleeps 0.02 seconds.
    - Iterates over every calendar day from start_date to end_date.
    - portfolio_value compounds at 0.03 % per day; benchmark_value at 0.02 %
      per day.
    - close_price = 22000.0 + day_index * 10; allocation = 0.6 (constant).
    - Returns total_return=round(final_portfolio_value - 1.0, 4),
      sharpe_ratio=1.35, max_drawdown=-0.08.
    """
    time.sleep(0.02)

    daily_results: list[DailyResult] = []
    portfolio_value = 1.0
    benchmark_value = 1.0

    current = config.start_date
    day_index = 0
    while current <= config.end_date:
        portfolio_value *= 1.0003
        benchmark_value *= 1.0002
        daily_results.append(
            DailyResult(
                date=current,
                portfolio_value=round(portfolio_value, 6),
                benchmark_value=round(benchmark_value, 6),
                allocation=0.6,
                close_price=22000.0 + day_index * 10,
            )
        )
        current += timedelta(days=1)
        day_index += 1

    final_pv = daily_results[-1].portfolio_value if daily_results else 1.0
    total_return = round(final_pv - 1.0, 4)

    return BacktestOutcome(
        total_return=total_return,
        sharpe_ratio=1.35,
        max_drawdown=-0.08,
        daily_results=daily_results,
    )
