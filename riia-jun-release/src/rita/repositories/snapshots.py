"""Repository for the snapshots table (manoeuvre position snapshots)."""

from pathlib import Path

from rita.config import get_settings
from rita.repositories.base import CsvRepository
from rita.schemas.snapshots import Snapshot


class SnapshotsRepository(CsvRepository[Snapshot]):
    def __init__(self, data_dir: Path | None = None) -> None:
        base = data_dir or Path(get_settings().data.output_dir)
        super().__init__(
            csv_path=base / "snapshots.csv",
            schema=Snapshot,
            id_field="snapshot_id",
        )
