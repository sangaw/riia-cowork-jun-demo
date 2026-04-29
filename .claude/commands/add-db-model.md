---
description: Add a SQLAlchemy ORM model, repository class, Pydantic schema, and Alembic migration
---

You are an Engineer agent adding a new DB model and repository to the RITA codebase.

**Task:** $ARGUMENTS

---

## Rule 1: Safety Check FIRST

Before any destructive DB operation, check what's in the DB:
```bash
python - << 'EOF'
from rita.database import SessionLocal
from rita.repositories.training import TrainingRunsRepository
from rita.repositories.backtest import BacktestRunsRepository

db = SessionLocal()
print("training_runs :", len(TrainingRunsRepository(db).read_all()))
print("backtest_runs :", len(BacktestRunsRepository(db).read_all()))
db.close()
EOF
```
If `training_runs > 0`, back up the DB first:
```bash
cp rita_output/rita.db rita_output/rita.db.bak-$(date +%Y%m%d-%H%M)
```

---

## Rule 2: ORM Model Pattern

```python
# src/rita/models/my_entity.py
from sqlalchemy import Column, String, Float, Integer, DateTime
from sqlalchemy.sql import func
from rita.database import Base

class MyEntity(Base):
    __tablename__ = "my_entities"

    entity_id  = Column(String, primary_key=True)
    name       = Column(String, nullable=False)
    value      = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

- Inherit from `rita.database.Base` — not SQLAlchemy's `Base` directly
- Primary key is always a `String` UUID (not auto-increment int)
- Nullable fields: use `nullable=True` explicitly; return `null` from the API so the frontend shows `—`
- Timestamps: `server_default=func.now()` — do not set in Python code

---

## Rule 3: Repository Class Pattern

```python
# src/rita/repositories/my_entity_repository.py
from sqlalchemy.orm import Session
from rita.repositories.base import SqlRepository
from rita.models.my_entity import MyEntity
from rita.schemas.my_entity import MyEntitySchema

class MyEntityRepository(SqlRepository[MyEntity, MyEntitySchema]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, MyEntity, MyEntitySchema)

    def get_by_name(self, name: str) -> list[MyEntitySchema]:
        rows = self._db.query(MyEntity).filter(MyEntity.name == name).all()
        return [MyEntitySchema.model_validate(r) for r in rows]
```

- Never instantiate without `db: Session` — `MyEntityRepository()` raises `TypeError`
- `upsert()` already calls `db.commit()` — do not commit again
- For bulk inserts: `db.add_all(records); db.commit()` directly
- Background threads must open their own session via `SessionLocal()`

---

## Rule 4: Pydantic Schema

```python
# src/rita/schemas/my_entity.py
from pydantic import BaseModel
from datetime import datetime

class MyEntitySchema(BaseModel):
    entity_id:  str
    name:       str
    value:      float | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
```

- `model_config = {"from_attributes": True}` is required — enables ORM object → Pydantic conversion
- Mirror nullability: if the ORM column is `nullable=True`, the schema field must be `T | None`

---

## Rule 5: Alembic Migration

```bash
# Run from riia-jun-release/
alembic revision --autogenerate -m "add my_entities table"
alembic upgrade head
```

Then update `alembic/env.py` — add the import for the new model:
```python
from rita.models.my_entity import MyEntity   # add this line
```
Without this import, Alembic's autogenerate won't detect the new table.

Also update `main.py` import block so `Base.metadata.create_all()` includes the new table:
```python
from rita.models.my_entity import MyEntity   # noqa: F401
```

---

## Rule 6: Startup Seeding (only if the table needs initial reference data)

```python
# In lifespan() — after existing seed blocks
if db.query(MyEntity).count() == 0:
    db.add_all([
        MyEntity(entity_id="seed-1", name="Example"),
    ])
    db.commit()
    logger.info("Seeded my_entities")
```

Do NOT seed pipeline run tables (`training_runs`, `backtest_runs`, etc.).

---

## Step-by-Step

1. Safety check — run the DB content check; backup if `training_runs > 0`
2. Create ORM model in `src/rita/models/my_entity.py`
3. Create Pydantic schema in `src/rita/schemas/my_entity.py`
4. Create repository in `src/rita/repositories/my_entity_repository.py`
5. Update `alembic/env.py` — add model import
6. Update `main.py` — add model import (for `create_all`) and seeding block if needed
7. Run `alembic revision --autogenerate` then review the generated script
8. Run `alembic upgrade head`

---

## Files to Touch

| File | Action |
|---|---|
| `src/rita/models/my_entity.py` | Create — ORM model |
| `src/rita/schemas/my_entity.py` | Create — Pydantic schema |
| `src/rita/repositories/my_entity_repository.py` | Create — repository class |
| `alembic/env.py` | Edit — add model import |
| `src/rita/main.py` | Edit — add model import + optional seed block |
| `alembic/versions/<ts>_add_my_entities.py` | Auto-generated |
| `Specs/Spec_DB.md` | Edit — add row to tables inventory |

---

## Definition of Done

- [ ] ORM model inherits `Base` from `rita.database`
- [ ] Repository constructor requires `db: Session` — no default constructor
- [ ] Pydantic schema has `model_config = {"from_attributes": True}`
- [ ] `alembic/env.py` updated with new model import
- [ ] Migration script reviewed before applying
- [ ] `alembic upgrade head` applied successfully
- [ ] `Specs/Spec_DB.md` table inventory updated
- [ ] DB backed up first if `training_runs > 0`
