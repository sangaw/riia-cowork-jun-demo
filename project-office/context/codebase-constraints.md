# Sprint 2.5+ Codebase Constraints

> **DEPRECATED — 2026-05-26 (Feature 18)**  
> Rules in this file have been moved to the three-tier guardrail system:
> - SQLAlchemy session rules → `project-office/guardrails/project.md §8`
> - Repository and service patterns → `project-office/guardrails/roles/engineer.md §3–4`
> - FastAPI dependency injection → `project-office/guardrails/roles/engineer.md §4`
>
> This file is kept for one sprint as a reference. **Do not load this file in new agent sessions** — load the guardrail files instead. This file will be deleted after 2026-06-26.

---

## 1. Repositories require `db: Session` — no default constructor

```python
# CORRECT
from rita.database import SessionLocal, get_db
repo = TrainingRunsRepository(db)          # db is a sqlalchemy Session

# WRONG — raises TypeError at runtime
repo = TrainingRunsRepository()
```

Every concrete repo (`TrainingRunsRepository`, `ManoeuvresRepository`, `PortfolioRepository`, `BacktestRunsRepository`, etc.) inherits from `SqlRepository[T, M]` with `def __init__(self, db: Session)`.

## 2. Service classes accept `db: Session`, not optional repos

```python
# CORRECT
class MyService:
    def __init__(self, db: Session) -> None:
        self._repo = MyRepository(db)

# WRONG
class MyService:
    def __init__(self, repo: MyRepository | None = None) -> None:
        self._repo = repo or MyRepository()   # MyRepository() won't work
```

## 3. FastAPI dependency injection pattern (all routers since Day 16)

```python
from rita.database import get_db

def get_my_service(db: Session = Depends(get_db)) -> MyService:
    return MyService(db)
```

## 4. Background threads must open their own session

```python
from rita.database import SessionLocal

def _background_worker(run_id: str) -> None:
    db = SessionLocal()
    try:
        repo = MyRepository(db)
        # ... do work ...
    finally:
        db.close()
```

Never pass a request-scoped `db` into a thread — sessions are not thread-safe.

## 5. `SqlRepository.upsert()` already calls `db.commit()` — do not commit again
