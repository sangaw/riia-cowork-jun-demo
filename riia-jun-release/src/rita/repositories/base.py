"""Base repository abstractions for the RITA CSV data layer.

ADR-002: Every CSV table has exactly one repository class inheriting from
CsvRepository[T].  No other code may read or write CSV files directly.
"""

from __future__ import annotations

import threading
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Generic, Optional, TypeVar

import pandas as pd
from pydantic import ValidationError

T = TypeVar("T")


class RepositoryValidationError(Exception):
    """Raised when a CSV row fails Pydantic schema validation."""

    def __init__(self, row: dict, errors: list) -> None:
        self.row = row
        self.errors = errors
        super().__init__(
            f"Row failed validation: {errors!r} | row data: {row!r}"
        )


class BaseRepository(ABC, Generic[T]):
    @abstractmethod
    def read_all(self) -> list[T]: ...

    @abstractmethod
    def write_all(self, records: list[T]) -> None: ...

    @abstractmethod
    def find_by_id(self, id: str) -> Optional[T]: ...

    @abstractmethod
    def upsert(self, record: T) -> T: ...

    @abstractmethod
    def delete(self, id: str) -> bool: ...


class CsvRepository(BaseRepository[T], Generic[T]):
    """Concrete CSV-backed repository with per-instance file locking."""

    def __init__(self, csv_path: Path, schema: type[T], id_field: str) -> None:
        self._csv_path = csv_path
        self._schema = schema
        self._id_field = id_field
        self._lock = threading.Lock()

    def read_all(self) -> list[T]:
        with self._lock:
            return self._read_unlocked()

    def write_all(self, records: list[T]) -> None:
        with self._lock:
            self._write_unlocked(records)

    def find_by_id(self, id: str) -> Optional[T]:
        with self._lock:
            for record in self._read_unlocked():
                if str(getattr(record, self._id_field)) == str(id):
                    return record
            return None

    def upsert(self, record: T) -> T:
        with self._lock:
            records = self._read_unlocked()
            record_id = str(getattr(record, self._id_field))
            replaced = False
            for i, existing in enumerate(records):
                if str(getattr(existing, self._id_field)) == record_id:
                    records[i] = record
                    replaced = True
                    break
            if not replaced:
                records.append(record)
            self._write_unlocked(records)
        return record

    def delete(self, id: str) -> bool:
        with self._lock:
            records = self._read_unlocked()
            filtered = [
                r for r in records
                if str(getattr(r, self._id_field)) != str(id)
            ]
            removed = len(filtered) < len(records)
            if removed:
                self._write_unlocked(filtered)
        return removed

    # ------------------------------------------------------------------
    # Internal helpers — must only be called while lock is already held
    # ------------------------------------------------------------------

    def _read_unlocked(self) -> list[T]:
        if not self._csv_path.exists():
            return []

        df = pd.read_csv(self._csv_path, dtype=str)
        results: list[T] = []
        for _, raw_row in df.iterrows():
            row_dict = {k: (None if pd.isna(v) else v) for k, v in raw_row.items()}
            try:
                results.append(self._schema.model_validate(row_dict))
            except ValidationError as exc:
                raise RepositoryValidationError(row_dict, exc.errors()) from exc
        return results

    def _write_unlocked(self, records: list[T]) -> None:
        validated: list[T] = []
        for record in records:
            try:
                validated.append(self._schema.model_validate(record.model_dump()))
            except ValidationError as exc:
                raise RepositoryValidationError(record.model_dump(), exc.errors()) from exc

        self._csv_path.parent.mkdir(parents=True, exist_ok=True)
        if validated:
            rows = [r.model_dump() for r in validated]
            df = pd.DataFrame(rows)
        else:
            # Write an empty file preserving column headers from the schema
            fields = list(self._schema.model_fields.keys())
            df = pd.DataFrame(columns=fields)
        df.to_csv(self._csv_path, index=False)
