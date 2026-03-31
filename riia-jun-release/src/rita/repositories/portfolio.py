"""Repository for the portfolio table (daily performance summary)."""

from pathlib import Path

from rita.config import get_settings
from rita.repositories.base import CsvRepository
from rita.schemas.portfolio import Portfolio


class PortfolioRepository(CsvRepository[Portfolio]):
    def __init__(self, data_dir: Path | None = None) -> None:
        base = data_dir or Path(get_settings().data.output_dir)
        super().__init__(
            csv_path=base / "portfolio.csv",
            schema=Portfolio,
            id_field="portfolio_id",
        )
