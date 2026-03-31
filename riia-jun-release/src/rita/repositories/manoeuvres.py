"""Repository for the manoeuvres table (manoeuvre group actions)."""

from pathlib import Path

from rita.config import get_settings
from rita.repositories.base import CsvRepository
from rita.schemas.manoeuvres import Manoeuvre


class ManoeuvresRepository(CsvRepository[Manoeuvre]):
    def __init__(self, data_dir: Path | None = None) -> None:
        base = data_dir or Path(get_settings().data.output_dir)
        super().__init__(
            csv_path=base / "manoeuvres.csv",
            schema=Manoeuvre,
            id_field="manoeuvre_id",
        )
