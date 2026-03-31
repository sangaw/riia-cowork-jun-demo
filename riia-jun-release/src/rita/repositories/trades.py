"""Repository for the trades table (closed/executed positions)."""

from pathlib import Path

from rita.config import get_settings
from rita.repositories.base import CsvRepository
from rita.schemas.trades import Trade


class TradesRepository(CsvRepository[Trade]):
    def __init__(self, data_dir: Path | None = None) -> None:
        base = data_dir or Path(get_settings().data.output_dir)
        super().__init__(
            csv_path=base / "trades.csv",
            schema=Trade,
            id_field="trade_id",
        )
