"""Repository for the positions table (live open positions from broker)."""

from pathlib import Path

from rita.config import get_settings
from rita.repositories.base import CsvRepository
from rita.schemas.positions import Position


class PositionsRepository(CsvRepository[Position]):
    def __init__(self, data_dir: Path | None = None) -> None:
        base = data_dir or Path(get_settings().data.output_dir)
        super().__init__(
            csv_path=base / "positions.csv",
            schema=Position,
            id_field="position_id",
        )
