"""Repository for the alerts table."""

from pathlib import Path

from rita.config import get_settings
from rita.repositories.base import CsvRepository
from rita.schemas.alerts import Alert


class AlertsRepository(CsvRepository[Alert]):
    def __init__(self, data_dir: Path | None = None) -> None:
        base = data_dir or Path(get_settings().data.output_dir)
        super().__init__(
            csv_path=base / "alerts.csv",
            schema=Alert,
            id_field="alert_id",
        )
