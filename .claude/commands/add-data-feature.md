---
description: Add a new data field, analysis calculation, or ML model to the RITA data pipeline
---

You are an Engineer agent adding or updating a data feature in the RITA data pipeline.

**Task:** $ARGUMENTS

---

## Data Directory Layout (read-only rules)

```
riia-jun-release/data/
├── raw/          ← IMMUTABLE source of truth — never write here
│   ├── NIFTY/    ← merged.csv (6,594 rows, 1999–2025)
│   ├── BANKNIFTY/
│   ├── ASML/
│   └── NVIDIA/
├── input/        ← manually updated — read-only from the API
│   └── DAILY-DATA/
│       ├── nifty_manual.csv      ← 2026 daily OHLCV appended manually
│       └── banknifty_manual.csv
└── output/       ← the ONLY directory the API writes to
    ├── NIFTY/    ← model .zip, backtest_results.csv, performance_summary.json
    └── BANKNIFTY/
```

**Absolute rules:**
- Never write to `data/raw/` from code — it is the ground-truth source
- Never call `pd.read_csv()` directly on OHLCV files — always use `load_nifty_csv()`
- Never suggest downloading from NSE/Yahoo Finance — all 25-year data is already present
- All API-generated output goes to `data/output/{INSTRUMENT}/`

---

## Instrument Files

| Instrument | Source file | Rows | Date range |
|---|---|---|---|
| NIFTY | `data/raw/NIFTY/merged.csv` | 6,594 | 1999–2025 |
| NIFTY (2026) | `data/input/DAILY-DATA/nifty_manual.csv` | ~17 | Mar 2026–present |
| BANKNIFTY | `data/raw/BANKNIFTY/banknifty_daily_25yr_rounded.csv` | 4,563 | 2007–2026 |
| ASML | `data/raw/ASML/asml_2001-2026.csv` | 6,457 | 2001–2026 |
| NVIDIA | `data/raw/NVIDIA/nvda_daily_25yr_rounded.csv` | 6,283 | 2001–2026 |

CSV column format: `date, open, high, low, close, shares traded, turnover (₹ cr)`

---

## Canonical Data Loader

**Always** use `load_nifty_csv()` — never ad-hoc `pd.read_csv()` in routers or services:

```python
from rita.core.data_loader import load_nifty_csv

df = load_nifty_csv("data/raw/NIFTY/merged.csv")
# Returns: DataFrame with DatetimeIndex, columns = Open, High, Low, Close, Volume
# Timezone-naive, sorted ascending by date
```

Handles automatically: timezone-aware IST dates, dd-MMM-yyyy format, column renaming (lowercase → Title Case).

---

## Adding a New Data Field / Indicator

When adding a new technical indicator or derived field to the dataset:

### 1. Add the calculation to `data_loader.py` or a `core/` module

```python
# src/rita/core/my_indicators.py

def add_my_indicator(df: pd.DataFrame) -> pd.DataFrame:
    """Add my_indicator column to OHLCV DataFrame."""
    df = df.copy()
    df['my_indicator'] = ...  # pure pandas calculation
    return df
```

Rules:
- Pure functions — no side effects, no file I/O, no DB access
- Always `df.copy()` before mutating — never modify the input in place
- Return the full DataFrame with the new column appended
- Prefix with the instrument/timeframe if instrument-specific

### 2. Wire into the pipeline

Call your function where the DataFrame is assembled — typically in `data_loader.py` or in the service that prepares market data before the API response.

### 3. Expose in the API response

Add the new field to the relevant Pydantic schema and the endpoint's `return` dict:

```python
# src/rita/schemas/market_data.py
class MarketSignalRow(BaseModel):
    ...
    my_indicator: float | None = None
```

### 4. Update the spec

Add the new field to `Specs/Spec_Python_Code.md` API table and `Specs/Spec_Data.md` if it changes the data contract.

---

## Data Analysis — `core/` Pattern

All analysis logic lives in `src/rita/core/`. Rules:

```python
# src/rita/core/my_analysis.py

import pandas as pd
import numpy as np

def analyse_my_metric(df: pd.DataFrame, window: int = 20) -> dict:
    """Pure function — no DB, no file I/O, no external calls."""
    result = df['Close'].rolling(window).mean()
    return {
        "mean": float(result.iloc[-1]),
        "trend": "up" if result.iloc[-1] > result.iloc[-2] else "down",
    }
```

- **No external data calls** — all data is local CSV/SQLite
- **No `print()` statements** — use `structlog` or return the result
- Functions must be deterministic — same input → same output
- Use `float()` when returning numpy scalars (avoids JSON serialisation errors)

---

## Adding / Retraining a Model

RITA uses **Stable Baselines3 DoubleDQN**. The training pipeline is in `src/rita/core/`.

**Output paths (never change these — the API reads from here):**
```
data/output/{INSTRUMENT}/
    {model_version}.zip           ← SB3 model weights
    backtest_results.csv          ← daily portfolio values
    performance_summary.json      ← aggregated KPIs (Sharpe, MDD, CAGR, etc.)
```

**Model version convention:** `{instrument}_{YYYYMMDD}_{run_id[:8]}`

When adding a new model variant:
1. Add a new training config in `config/` if hyperparameters change
2. Write output to the standard paths above — the API uses `find_latest_model()` to locate the newest `.zip`
3. Update `Specs/Spec_Data.md` if the output schema changes
4. Run backtest after training — do not commit a model without a `performance_summary.json`

---

## DB Seeding Pattern (for new instruments or data tables)

```python
# In main.py lifespan() — after existing seed blocks
if db.query(MyModel).count() == 0:
    rows = [MyModel(**row) for row in load_seed_data()]
    db.add_all(rows)
    db.commit()
    logger.info("Seeded my_table", count=len(rows))
```

- **Bulk insert only** — `db.add_all()` + single `db.commit()` per instrument
- Never seed row-by-row with individual `upsert()` calls — 6,594 rows × 1 commit = 78 seconds
- Seeding window: 2025+2026 only for market_data_cache — full history is not needed for indicators (26 bars for MACD is the max lookback required)

---

## Files to Touch

| File | Action |
|---|---|
| `src/rita/core/my_indicators.py` | Create — pure indicator/analysis function |
| `src/rita/core/data_loader.py` | Edit — wire new function into the load chain |
| `src/rita/schemas/market_data.py` | Edit — add new field to schema if exposed via API |
| `src/rita/api/<tier>/my_endpoint.py` | Edit — add field to `return` dict |
| `Specs/Spec_Data.md` | Edit — document new field, file, or output |
| `Specs/Spec_Python_Code.md` | Edit — update API table if contract changed |

---

## Definition of Done

- [ ] New indicator/field is a pure function in `src/rita/core/` — no side effects
- [ ] `load_nifty_csv()` used for all OHLCV reads — no ad-hoc `pd.read_csv()`
- [ ] No writes to `data/raw/` or `data/input/`
- [ ] New field added to Pydantic schema if exposed via API
- [ ] API `return` dict includes the new field
- [ ] JS consumer field list matches handler `return` dict (if frontend reads the new field)
- [ ] `Specs/Spec_Data.md` updated if data layout or output changed
- [ ] `Specs/Spec_Python_Code.md` updated if API contract changed
- [ ] For new models: `performance_summary.json` present in `data/output/{INSTRUMENT}/`
