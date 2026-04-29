---
description: Add or modify a FastAPI endpoint — tier placement, repo/service/schema scaffolding, JS contract check
---

You are an Engineer agent adding or modifying a FastAPI route in the RITA codebase.

**Task:** $ARGUMENTS

---

## Rule 1: Tier Placement (ADR-001)

Use the first rule that matches:

| If the endpoint... | Tier | Directory |
|---|---|---|
| Reads or writes exactly ONE table, no logic | **System** | `src/rita/api/v1/system/<resource>.py` |
| Orchestrates a multi-step or ML workflow | **Workflow** | `src/rita/api/v1/workflow/<process>.py` |
| Composes a read-only UI payload from multiple sources | **Experience** | `src/rita/api/experience/<section>.py` |

- **System:** Call ONE repository only. Zero business logic. Never call a service or combine tables.
- **Workflow:** Call services only — never call repositories directly from the router.
- **Experience:** Read-only. No side effects. No writes.

---

## Rule 2: Repository Pattern (ADR-002)

No direct DB/CSV access in routes or services. All data through `repositories/`.

```python
# src/rita/repositories/my_resource_repository.py
from rita.repositories.base import SqlRepository
from rita.models import MyModel
from rita.schemas.my_resource import MyResourceSchema

class MyResourceRepository(SqlRepository[MyModel, MyResourceSchema]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, MyModel, MyResourceSchema)
```

---

## Rule 3: FastAPI Dependency Injection

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from rita.database import get_db
from rita.services.my_service import MyService

router = APIRouter()

def _get_service(db: Session = Depends(get_db)) -> MyService:
    return MyService(db)

@router.get("/resource")
def get_resource(svc: MyService = Depends(_get_service)):
    return svc.get_resource()
```

For System (CRUD) routers — inject the repo directly, skip the service:
```python
def _get_repo(db: Session = Depends(get_db)) -> MyResourceRepository:
    return MyResourceRepository(db)
```

---

## Rule 4: Service Constructor

```python
class MyService:
    def __init__(self, db: Session) -> None:
        self._repo = MyResourceRepository(db)
```

Never use optional repos or a default constructor — `MyRepository()` raises `TypeError`.

---

## Rule 5: Background Thread Sessions

```python
from rita.database import SessionLocal

def _background_worker(run_id: str) -> None:
    db = SessionLocal()
    try:
        repo = MyResourceRepository(db)
        # ... work ...
    finally:
        db.close()
```

Never pass a request-scoped `db` into a thread — sessions are not thread-safe.

---

## Rule 6: JS Frontend Contract Check (mandatory if a JS consumer exists)

```
grep -r "/api/v1/my-endpoint" dashboard/js/
```

1. List every field the JS reads from the response (`r.fieldName`, `data.someKey`, etc.)
2. Your handler's `return { ... }` dict must include every field in that list
3. Missing fields become `undefined` — no error, UI silently shows `—` or `NaN`
4. Never echo a query param as a row field value

| Pitfall | Safe pattern |
|---|---|
| `parseFloat(null)` → `NaN` | `v !== null ? parseFloat(v).toFixed(2) : '—'` |
| `catch (_) {}` swallows errors | `catch (e) { console.warn('...', e) }` |
| Query param echoed as row field | Derive from data; never echo the request param |

---

## Step-by-Step

1. Grep for the JS consumer — list the fields it reads
2. Choose the tier using the decision tree above
3. Check/create Pydantic schemas in `src/rita/schemas/`
4. Create/update the repository in `src/rita/repositories/`
5. Create/update the service in `src/rita/services/` (Workflow/Experience only)
6. Create/update the router in the correct tier directory
7. Register the router in `src/rita/main.py`
8. Verify JS contract — paste field list from JS next to your `return` dict
9. Update `Specs/Spec_Python_Code.md` if API contract changed

---

## Files to Touch

| File | Action |
|---|---|
| `src/rita/schemas/<resource>.py` | Create or extend — Pydantic request/response models |
| `src/rita/repositories/<resource>_repository.py` | Create if new table access needed |
| `src/rita/services/<resource>_service.py` | Create for Workflow or Experience tier |
| `src/rita/api/<tier>/<resource>.py` | Create or edit — router + handler |
| `src/rita/main.py` | Edit — `app.include_router(...)` |
| `Specs/Spec_Python_Code.md` | Edit if API contract changed |

---

## Definition of Done

- [ ] Route in the correct tier directory
- [ ] No direct DB/CSV access in routes or services
- [ ] Every repo instantiation passes `db: Session`
- [ ] Handler's `return` dict includes every field the JS consumer reads
- [ ] `ruff check src/` passes
- [ ] Router registered in `main.py`
- [ ] `Specs/Spec_Python_Code.md` updated if contract changed
