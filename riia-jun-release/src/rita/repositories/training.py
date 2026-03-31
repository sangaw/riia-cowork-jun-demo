"""Repositories for training_runs and training_metrics tables."""

from pathlib import Path

from rita.config import get_settings
from rita.repositories.base import CsvRepository
from rita.schemas.training import TrainingRun, TrainingMetric


class TrainingRunsRepository(CsvRepository[TrainingRun]):
    def __init__(self, data_dir: Path | None = None) -> None:
        base = data_dir or Path(get_settings().data.output_dir)
        super().__init__(
            csv_path=base / "training_runs.csv",
            schema=TrainingRun,
            id_field="run_id",
        )


class TrainingMetricsRepository(CsvRepository[TrainingMetric]):
    def __init__(self, data_dir: Path | None = None) -> None:
        base = data_dir or Path(get_settings().data.output_dir)
        super().__init__(
            csv_path=base / "training_metrics.csv",
            schema=TrainingMetric,
            id_field="metric_id",
        )
