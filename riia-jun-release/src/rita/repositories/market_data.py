"""Repository for the market_data_cache table (OHLCV price data)."""

from pathlib import Path

from rita.config import get_settings
from rita.repositories.base import CsvRepository
from rita.schemas.market_data import MarketDataCache


class MarketDataCacheRepository(CsvRepository[MarketDataCache]):
    def __init__(self, data_dir: Path | None = None) -> None:
        base = data_dir or Path(get_settings().data.output_dir)
        super().__init__(
            csv_path=base / "market_data_cache.csv",
            schema=MarketDataCache,
            id_field="cache_id",
        )
