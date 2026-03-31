"""Repository for the model_registry table."""

from pathlib import Path

from rita.config import get_settings
from rita.repositories.base import CsvRepository
from rita.schemas.model_registry import ModelRegistry


class ModelRegistryRepository(CsvRepository[ModelRegistry]):
    def __init__(self, data_dir: Path | None = None) -> None:
        base = data_dir or Path(get_settings().data.output_dir)
        super().__init__(
            csv_path=base / "model_registry.csv",
            schema=ModelRegistry,
            id_field="model_id",
        )
