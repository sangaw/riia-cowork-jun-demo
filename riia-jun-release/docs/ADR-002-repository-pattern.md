# ADR-002: Repository Pattern for CSV Data Access

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-03-30 |
| **Sprint** | 0 |

---

## Context

The POC scattered `pd.read_csv()` and `df.to_csv()` calls throughout `rest_api.py` and the core modules with no centralised access layer, no file locking, and no schema validation on read or write. This caused:

- **Data corruption risk** — concurrent requests could write to the same CSV simultaneously.
- **No schema enforcement** — malformed rows silently propagated through the system.
- **Untestable I/O** — tests had to set up real CSV files or monkey-patch pandas in-place.
- **Tight coupling** — migrating to PostgreSQL in v2 would require touching every caller.

---

## Decision

Implement a repository layer (`repositories/`) with the following rules:

### BaseRepository Interface

Every table gets one class that inherits from `BaseRepository`. No other code may read or write CSV files directly.

```python
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional

T = TypeVar("T")

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
```

### File Locking

Each repository instance holds a `threading.Lock`. All `read_all` and `write_all` calls acquire the lock. CSV is not concurrent-safe — this prevents corruption under FastAPI's async/threaded request handling.

### Schema Validation

All records are validated through Pydantic models on both read and write. A row that fails validation raises a `RepositoryValidationError` — it never silently passes through.

### v2 Migration Path

Only the repository layer changes to swap in PostgreSQL. Services, routes, and schemas are untouched. Implementations are swapped via dependency injection — no call sites change.

---

## CSV Tables in Scope (v1) — 15 Tables

| Repository Class | CSV File | Primary Key |
|---|---|---|
| `PositionsRepository` | `positions.csv` | `position_id` |
| `OrdersRepository` | `orders.csv` | `order_id` |
| `SnapshotsRepository` | `snapshots.csv` | `snapshot_id` |
| `TradesRepository` | `trades.csv` | `trade_id` |
| `PortfolioRepository` | `portfolio.csv` | `portfolio_id` |
| `ManoeuvresRepository` | `manoeuvres.csv` | `manoeuvre_id` |
| `BacktestRunsRepository` | `backtest_runs.csv` | `run_id` |
| `BacktestResultsRepository` | `backtest_results.csv` | `result_id` |
| `TrainingRunsRepository` | `training_runs.csv` | `run_id` |
| `TrainingMetricsRepository` | `training_metrics.csv` | `metric_id` |
| `ModelRegistryRepository` | `model_registry.csv` | `model_id` |
| `AlertsRepository` | `alerts.csv` | `alert_id` |
| `AuditLogRepository` | `audit_log.csv` | `log_id` |
| `MarketDataCacheRepository` | `market_data_cache.csv` | `cache_id` |
| `ConfigOverridesRepository` | `config_overrides.csv` | `override_id` |

`rita_input/` is **read-only** source data. All write operations target `rita_output/`.

---

## Consequences

**Positive:**
- All data access is testable — repositories can be mocked or replaced with in-memory implementations in tests.
- File locking prevents CSV corruption under concurrent load.
- Schema validation catches data quality issues at the boundary.
- v2 database migration is mechanical — one new implementation class per table, zero route/service changes.

**Negative:**
- 15 repository classes is more boilerplate than direct pandas calls.
- File locking adds latency on high-frequency writes (acceptable for v1 CSV-backed system).

---

## Alternatives Considered

| Option | Reason Rejected |
|---|---|
| SQLAlchemy ORM on CSV | No CSV dialect; wrong abstraction layer for flat files |
| Pandas-native access | No locking, no schema enforcement, untestable |
| TinyDB / SQLite | Additional dependency; CSV is the agreed v1 storage format |
