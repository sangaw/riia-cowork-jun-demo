"""Repository for the config_overrides table (runtime config and session state)."""

from pathlib import Path

from rita.config import get_settings
from rita.repositories.base import CsvRepository
from rita.schemas.config_overrides import ConfigOverride


class ConfigOverridesRepository(CsvRepository[ConfigOverride]):
    def __init__(self, data_dir: Path | None = None) -> None:
        base = data_dir or Path(get_settings().data.output_dir)
        super().__init__(
            csv_path=base / "config_overrides.csv",
            schema=ConfigOverride,
            id_field="override_id",
        )
