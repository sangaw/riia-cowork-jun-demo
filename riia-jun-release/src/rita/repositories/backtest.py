"""Repositories for backtest_runs and backtest_results tables."""

from pathlib import Path

from rita.config import get_settings
from rita.repositories.base import CsvRepository
from rita.schemas.backtest import BacktestRun, BacktestResult


class BacktestRunsRepository(CsvRepository[BacktestRun]):
    def __init__(self, data_dir: Path | None = None) -> None:
        base = data_dir or Path(get_settings().data.output_dir)
        super().__init__(
            csv_path=base / "backtest_runs.csv",
            schema=BacktestRun,
            id_field="run_id",
        )


class BacktestResultsRepository(CsvRepository[BacktestResult]):
    def __init__(self, data_dir: Path | None = None) -> None:
        base = data_dir or Path(get_settings().data.output_dir)
        super().__init__(
            csv_path=base / "backtest_results.csv",
            schema=BacktestResult,
            id_field="result_id",
        )
