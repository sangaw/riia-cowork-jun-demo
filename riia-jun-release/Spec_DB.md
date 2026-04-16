# RITA — Database Specification

High-density reference for AI agents. Read before touching the DB, writing migrations, or modifying seeding logic.

---

## 1. Technology & Location

| Item | Value |
|---|---|
| Engine | SQLite via SQLAlchemy 2.x ORM |
| File | `rita_output/rita.db` (relative to `riia-jun-release/`) |
| Config key | `settings.database.database_url` → `"sqlite:///./rita_output/rita.db"` |
| Migrations | Alembic — `alembic/versions/` |
| v2 upgrade path | Change `database_url` to PostgreSQL — zero code changes needed |

---

## 2. ⚠️ CRITICAL SAFETY RULES — READ FIRST

**NEVER delete `rita_output/rita.db` without explicit user confirmation AND a backup.**

The DB contains two categories of data with very different recoverability:

| Category | Tables | Recoverable? |
|---|---|---|
| **Seeded on startup** | `instruments`, `market_data_cache` | Yes — auto-reseeded on next start |
| **Pipeline run history** | `training_runs`, `backtest_runs`, `backtest_results`, `risk_timeline` | **NO** — permanently lost if DB deleted |
| **FnO trading records** | `positions`, `orders`, `snapshots`, `trades`, `manoeuvres`, `portfolio` | Partial — source CSVs exist in `data/input/DAILY-DATA/` |
| **Config & audit** | `config_overrides`, `audit_log`, `alerts` | **NO** |

**Before any destructive DB operation, run:**
```bash
# Check what's in the DB first
python - << 'EOF'
from rita.database import SessionLocal
from rita.repositories.training import TrainingRunsRepository
from rita.repositories.backtest import BacktestRunsRepository
from rita.repositories.market_data import MarketDataCacheRepository

db = SessionLocal()
print("training_runs  :", len(TrainingRunsRepository(db).read_all()))
print("backtest_runs  :", len(BacktestRunsRepository(db).read_all()))
print("market_data    :", len(MarketDataCacheRepository(db).read_all()))
db.close()
EOF
```

**If training_runs > 0, do NOT delete the DB without user approval.**

**Backup command (run from `riia-jun-release/`):**
```bash
cp rita_output/rita.db rita_output/rita.db.bak-$(date +%Y%m%d-%H%M)
```

---

## 3. Tables — Full Inventory

### Auto-seeded on startup (safe to lose)

| Table | Model file | PK | Seeded from | Rows (typical) |
|---|---|---|---|---|
| `instruments` | `models/instrument.py` | `instrument_id` | `main.py` lifespan | 4 |
| `market_data_cache` | `models/market_data.py` | `cache_id` | `main.py` lifespan | ~266 |

### Pipeline run history (NOT recoverable)

| Table | Model file | PK | Contains |
|---|---|---|---|
| `training_runs` | `models/training.py` | `run_id` | All ML training runs — Sharpe, MDD, timesteps, status, model version |
| `backtest_runs` | `models/backtest.py` | `run_id` | Backtest job records — date range, strategy params, status |
| `backtest_results` | `models/backtest.py` | `result_id` | Daily portfolio/benchmark values, allocation, Sharpe, drawdown per backtest |
| `risk_timeline` | `models/risk.py` | (composite) | Day-by-day allocation, drawdown, regime — powers Trade Journal chart |

### FnO trading records (partially recoverable from CSVs)

| Table | Model file | Source CSVs |
|---|---|---|
| `positions` | `models/positions.py` | `data/input/DAILY-DATA/positions-*.csv` |
| `orders` | `models/orders.py` | `data/input/DAILY-DATA/orders-*.csv` |
| `snapshots` | `models/snapshots.py` | — |
| `trades` | `models/trades.py` | — |
| `manoeuvres` | `models/manoeuvres.py` | — |
| `portfolio` | `models/portfolio.py` | — |

### Config & observability (not recoverable)

| Table | Model file | Contains |
|---|---|---|
| `config_overrides` | `models/config_overrides.py` | Runtime config key/value overrides |
| `audit_log` | `models/audit.py` | API call audit trail |
| `alerts` | `models/alerts.py` | Chat/query confidence log |

---

## 4. Startup Seeding Behaviour

Seeding runs in `main.py` `lifespan()` on every startup. Each seed block checks if the table is already populated before inserting.

### Instruments seed
- Seeds 4 instruments: `NIFTY`, `BANKNIFTY`, `NVIDIA`, `ASML`
- Skipped if `instruments` table already has rows
- Also handles one-time rename `NVDA → NVIDIA`

### Market data seed
- Seeds NIFTY OHLCV data from two sources combined:
  1. `data/raw/NIFTY/merged.csv` — filters to **year == 2025** (249 rows)
  2. `data/input/DAILY-DATA/nifty_manual.csv` — filters to **year == 2026** (~17 rows)
- Combined: ~266 rows, 2025-01-01 → latest 2026 date
- Uses **single `db.add_all()` + one commit** — completes in < 2 seconds
- Skipped if `market_data_cache` table already has rows
- **Why 2025 only from merged.csv:** full 25-year history (6,594 rows) took 78 seconds with row-by-row upserts. 2025+ is sufficient for all technical indicators (RSI-14, MACD-26, BB-20, EMA-50 all warm up within the first 50 bars).

---

## 5. Repository Pattern Rules

```python
# CORRECT — always pass db: Session
from rita.database import SessionLocal, get_db
db = SessionLocal()
repo = TrainingRunsRepository(db)

# WRONG — no default constructor
repo = TrainingRunsRepository()   # TypeError at runtime
```

- Every repo inherits `SqlRepository[T, M]` and requires `db: Session`
- `SqlRepository.upsert()` calls `db.commit()` internally — do not commit again
- For bulk inserts, bypass `upsert()` and use `db.add_all(records); db.commit()` directly
- Background threads must open their own `SessionLocal()` — never pass a request-scoped session to a thread

---

## 6. Migrations

```bash
# Generate a new migration after changing an ORM model
alembic revision --autogenerate -m "describe the change"

# Apply all pending migrations
alembic upgrade head

# Roll back one step
alembic downgrade -1
```

- Migration scripts live in `alembic/versions/`
- `alembic/env.py` imports `Base` and all 17 model classes — any new model must be added there
- `main.py` lifespan calls `Base.metadata.create_all(bind=engine)` as a safety net (creates tables that Alembic hasn't migrated yet in dev)
- CI pipeline runs `alembic upgrade head` before `pytest`

---

## 7. Disaster Recovery Checklist

If the DB is accidentally deleted:

1. **Restart the server** — instruments and market_data_cache are reseeded automatically (<2 sec)
2. **Pipeline run history is gone** — user must re-run training and backtest to rebuild records
3. **Model `.zip` files survive** — they live in `data/output/{INSTRUMENT}/`, not in the DB
4. **FnO records** — can be re-imported from `data/input/DAILY-DATA/*.csv` source files (manual process, no auto-import exists yet)

Going forward: **always backup before deleting** using the command in Section 2.
