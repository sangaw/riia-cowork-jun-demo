"""Repository for the orders table (broker order log)."""

from pathlib import Path

from rita.config import get_settings
from rita.repositories.base import CsvRepository
from rita.schemas.orders import Order


class OrdersRepository(CsvRepository[Order]):
    def __init__(self, data_dir: Path | None = None) -> None:
        base = data_dir or Path(get_settings().data.output_dir)
        super().__init__(
            csv_path=base / "orders.csv",
            schema=Order,
            id_field="order_id",
        )
