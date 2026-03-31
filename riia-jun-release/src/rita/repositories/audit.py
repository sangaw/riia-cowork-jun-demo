"""Repository for the audit_log table (API and agent action log)."""

from pathlib import Path

from rita.config import get_settings
from rita.repositories.base import CsvRepository
from rita.schemas.audit import AuditLog


class AuditLogRepository(CsvRepository[AuditLog]):
    def __init__(self, data_dir: Path | None = None) -> None:
        base = data_dir or Path(get_settings().data.output_dir)
        super().__init__(
            csv_path=base / "audit_log.csv",
            schema=AuditLog,
            id_field="log_id",
        )
