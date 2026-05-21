# Feature 09 — Build Complete Data Pipeline to Add New Instrument

**Status:** Requirements Draft  
**Date:** 2026-05-17  
**Owner:** San G  
**Approach:** /enhance multi-agent orchestration

---

## 1. Problem Statement

RITA is currently hard-wired to four instruments (NIFTY, BANKNIFTY, ASML, NVIDIA). Adding a fifth requires:
- Manually sourcing and placing CSV files
- Hardcoded paths in `find_instrument_csv()`
- A `load_nifty_csv()` function named after a single instrument
- Manual DB seeding via `main.py` lifespan

Users cannot onboard a new instrument without developer intervention. This feature gives the user a self-service workflow from the Daily Ops page: type a company name, pick the listing from Yahoo Finance results, and have the instrument fully available in RITA for signals, portfolio, training, and backtest.

---

## 2. Scope

**In scope:**
- Company-name → Yahoo Finance ticker search (with multi-listing picker when same company trades on multiple exchanges)
- Automated OHLCV data fetch via yfinance (from 2009-09-01 for warmup; usable data from 2010-01-01)
- Raw data saved to `data/raw/{TICKER}/`
- Normalized data saved to `data/input/{TICKER}/`
- Instrument registered in `instruments` table (with currency auto-detected from yfinance)
- `market_data_cache` seeded for 2025–2026 window at runtime (consistent with existing instruments)
- Instrument available in: RITA market signals, geography overview, DS training, backtest
- Daily Ops instruments list refreshes to show new instrument
- Rename `load_nifty_csv()` → `load_ohlcv_csv()` (instrument-agnostic name)
- Make `find_instrument_csv()` dynamic (glob-based, not hardcoded per instrument)

**Out of scope:**
- FnO positions for new instrument (lot_size stored but no automatic FnO seeding)
- Deleting / offboarding instruments
- Intraday data or non-daily timeframes
- Historical `nifty_manual.csv`-style live-append for new instruments (one CSV per instrument is sufficient)

---

## 3. User Flow

```
Daily Ops page
│
├─ User clicks "Add Instrument"
│
├─ Search box appears
│   User types: "Transunion"
│   → GET /api/v1/instrument/search?q=Transunion
│
├─ Results list renders (up to 10 matches, equity only):
│     TRU    TransUnion           NYSE     USD   Equity
│     TRU.TO TransUnion Canada   Toronto  CAD   Equity
│     ...
│
├─ User clicks a row → confirmation form appears:
│     Ticker:    TRU         (read-only, from search result)
│     Name:      TransUnion  (read-only, from search result)
│     Exchange:  NYSE        (read-only, from search result)
│     Currency:  USD         (read-only, from search result)
│     Country:   US          (read-only, from search result)
│     Lot Size:  [   ]       (optional user entry — leave blank for pure equity)
│
├─ User clicks "Add"
│   → POST /api/v1/instrument/onboard
│   Progress text: "Fetching data… → Saving… → Seeding cache…"
│
└─ On success: instrument list refreshes, new instrument shows as enabled (green dot)
```

---

## 4. Backend Requirements

### 4.1 New Dependency

**File:** `pyproject.toml`

Add `yfinance` to project dependencies.

---

### 4.2 Rename `load_nifty_csv()` → `load_ohlcv_csv()`

**File:** `src/rita/core/data_loader.py`

- Rename function `load_nifty_csv` to `load_ohlcv_csv`. Signature and behaviour unchanged.
- Add backward-compat alias immediately after the renamed function:
  ```python
  load_nifty_csv = load_ohlcv_csv
  ```

**Call sites to update** (change import name from `load_nifty_csv` to `load_ohlcv_csv`):

| File |
|---|
| `src/rita/core/data_understanding.py` |
| `src/rita/core/ml_dispatch.py` |
| `src/rita/core/drift_detector.py` |
| `src/rita/core/portfolio_engine.py` |
| `src/rita/api/experience/rita.py` |
| `src/rita/api/experience/pipeline_wizard.py` |
| `src/rita/api/experience/ds.py` |
| `src/rita/api/v1/workflow/chat.py` |
| `src/rita/api/v1/system/training_runs.py` |
| `src/rita/api/v1/system/market_signals.py` |

The alias means all sites compile before the rename is complete; Engineer should still update all 10 for cleanliness.

---

### 4.3 Make `find_instrument_csv()` Dynamic

**File:** `src/rita/core/data_understanding.py`

Current implementation has hardcoded paths per instrument. Replace with dynamic glob logic:

```
Priority 1: data/raw/{TICKER}/*.csv    → pick first match
Priority 2: data/input/{TICKER}/*.csv  → fallback if raw missing
NIFTY exception retained:
  primary  = data/raw/NIFTY/merged.csv
  append   = data/input/DAILY-DATA/nifty_manual.csv
BANKNIFTY exception retained:
  primary  = data/raw/BANKNIFTY/banknifty_daily_25yr_rounded.csv
```

Function signature `find_instrument_csv(instrument_id: str) -> Path` does not change. All callers work without modification.

---

### 4.4 Add `currency` Column to Instruments Model

**File:** `src/rita/models/instrument.py`

Add: `currency: Mapped[str] = mapped_column(String(10), nullable=True)`

**File:** new Alembic migration in `alembic/versions/`

```python
op.add_column("instruments", sa.Column("currency", sa.String(10), nullable=True))
```

**File:** `src/rita/api/v1/system/instruments.py`

- Add `currency: Optional[str] = None` to `_InstrumentBody`
- Include `"currency": i.currency` in the `list_instruments` response dict

---

### 4.5 New Service: `instrument_onboard.py`

**File:** `src/rita/services/instrument_onboard.py`

```python
def search_tickers(query: str, max_results: int = 10) -> list[dict]:
    """
    Calls yfinance.Search(query).quotes.
    Filters to quoteType == "EQUITY" only.
    Returns list of {ticker, name, exchange, currency, country, quote_type}.
    """

def fetch_raw_data(ticker: str) -> Path:
    """
    yf.download(ticker, start="2009-09-01", interval="1d", auto_adjust=True).
    Creates data/raw/{TICKER}/ if absent.
    Saves DataFrame to data/raw/{TICKER}/{ticker}_daily.csv.
    Raises ValueError if fewer than 100 rows returned.
    Returns path written.
    """

def process_to_input(ticker: str, raw_path: Path) -> Path:
    """
    load_ohlcv_csv(raw_path) → normalize → filter year >= 2010.
    Creates data/input/{TICKER}/ if absent.
    Saves to data/input/{TICKER}/{ticker}_daily.csv.
    Output columns: Date(index), Open, High, Low, Close, Volume — tz-naive, sorted asc.
    Returns path written.
    """

def seed_market_cache(db: Session, ticker: str, currency: str) -> int:
    """
    Reads data/input/{TICKER}/{ticker}_daily.csv via load_ohlcv_csv().
    Filters to year >= 2025.
    Skips if `underlying` == ticker already present in market_data_cache.
    db.add_all(records); db.commit() — bulk insert.
    Returns row count inserted (0 if skipped).
    """
```

---

### 4.6 New Router: `instrument_onboard.py`

**File:** `src/rita/api/v1/workflow/instrument_onboard.py`

Tier 2 Workflow. No JWT required (same pattern as `pipeline.py`).

```
GET  /api/v1/instrument/search
     Query param: q (str, required — min length 2)
     Response: list[{ticker, name, exchange, currency, country, quote_type}]
     Calls: search_tickers(q)
     Errors: 400 if q blank/short; 502 if yfinance unreachable

POST /api/v1/instrument/onboard
     Body: {ticker, name, exchange, currency, country_code, lot_size?}
     Response: {status, ticker, rows_fetched, rows_seeded, raw_path, input_path}
     Pipeline (in order):
       1. Check instruments table — 409 if ticker already exists
       2. fetch_raw_data(ticker)         → raw_path, rows_fetched
       3. process_to_input(ticker, raw_path) → input_path
       4. instruments repo upsert (currency, is_available=True, lot_size)
       5. seed_market_cache(db, ticker, currency) → rows_seeded
     Errors: 409 duplicate; 400 bad ticker; 502 yfinance failure
```

**File:** `main.py`

Register after `workflow/pipeline.py`:
```python
from rita.api.v1.workflow.instrument_onboard import router as instrument_onboard_router
app.include_router(instrument_onboard_router)
```

---

### 4.7 Update Geography Overview — Dynamic Instrument List

**File:** `src/rita/api/experience/rita.py`

`GET /api/v1/experience/rita/geography-overview` — update to load instruments dynamically:
- Query `instruments` table for all rows where `is_available = True`
- Map `country_code` to geography bucket:
  - `IN` → India
  - `US` → US
  - `NL`, `DE`, `FR`, `GB`, `BE`, `CH`, + other EU country codes → EU
  - Anything else → Other
- Build panel payload dynamically — new instruments appear in the correct panel automatically after onboarding

---

## 5. Frontend Requirements

### 5.1 `dashboard/js/ops/daily-ops.js`

Add to the instruments section. New functions:

```
searchInstruments(query)
  Calls GET /api/v1/instrument/search?q={query}
  Renders results into #dops-search-results (show spinner while loading)
  Each result row: onclick="selectSearchResult(ticker, name, exchange, currency, country)"

selectSearchResult(ticker, name, exchange, currency, country)
  Hides #dops-search-results
  Populates read-only fields in #dops-confirm-form
  Shows #dops-confirm-form

onboardInstrument()
  Reads ticker, name, exchange, currency, country_code, lot_size from form
  POST /api/v1/instrument/onboard
  Shows progress text in #dops-onboard-status:
    "Fetching data…" (immediately on click)
    "Saving…" (after 1s if no response yet)
    "Seeding cache…" (after 3s if no response yet)
  On success: hide form, clear search, call loadInstruments()
  On error: show error message in #dops-onboard-status

cancelOnboard()
  Hide #dops-add-instrument-panel
  Clear #dops-search-input value
  Clear #dops-search-results
  Hide #dops-confirm-form
```

**window exports (required for HTML onclick):**
```javascript
window.searchInstruments   = searchInstruments;
window.selectSearchResult  = selectSearchResult;
window.onboardInstrument   = onboardInstrument;
window.cancelOnboard       = cancelOnboard;
```

---

### 5.2 `dashboard/ops.html`

Targeted Edit only — no full-file read. Insert after the `#btn-save-instruments` button inside the Daily Ops instruments section.

Elements required:

```html
<!-- Add Instrument trigger -->
<button id="btn-add-instrument" onclick="cancelOnboard(); ...">"Add Instrument"</button>

<!-- Collapsible panel -->
<div id="dops-add-instrument-panel" style="display:none;">

  <!-- Step 1: Search -->
  <input id="dops-search-input" type="text" placeholder="Company name or ticker…">
  <button onclick="searchInstruments(document.getElementById('dops-search-input').value)">
    Search
  </button>
  <div id="dops-search-results"></div>   <!-- populated by JS -->

  <!-- Step 2: Confirm (hidden until result selected) -->
  <div id="dops-confirm-form" style="display:none;">
    <!-- read-only: ticker, name, exchange, currency, country -->
    <!-- editable:  lot_size (number input, optional) -->
    <button onclick="onboardInstrument()">Add</button>
    <button onclick="cancelOnboard()">Cancel</button>
  </div>

  <!-- Status / progress -->
  <div id="dops-onboard-status"></div>
</div>
```

Style consistent with existing Daily Ops cards (use `var(--bg2)`, `var(--bdr)`, `var(--t1)` CSS variables).

---

## 6. Data Layout for New Instruments

```
data/
├── raw/
│   └── {TICKER}/
│       └── {ticker}_daily.csv    ← yfinance output — never modified after write
└── input/
    └── {TICKER}/
        └── {ticker}_daily.csv    ← normalized: Open/High/Low/Close/Volume
                                     tz-naive, sorted asc, year >= 2010
```

| Window | Purpose | Filter |
|---|---|---|
| 2009-09-01 → 2009-12-31 | Indicator warmup (not in input CSV) | Fetched, not saved |
| 2010-01-01 → present | Full training history | `data/input/{TICKER}/` |
| 2025-01-01 → present | Runtime DB cache | `market_data_cache` |

---

## 7. Spec Files to Update (Same Commit — DoD)

| Spec | What to add/change |
|---|---|
| `project-office/specs/Spec_Data.md` | Add Section 10: New Instrument Data Layout. Note `load_ohlcv_csv()` rename + alias. Update `find_instrument_csv()` description to "glob-based, dynamic". |
| `project-office/specs/Spec_RITA_App.md` | Add `GET /api/v1/instrument/search` and `POST /api/v1/instrument/onboard` to Workflow Tier table. |
| `project-office/specs/Spec_Python_Code.md` | Add `instrument_onboard.py` to services table and workflow router table. Note `load_ohlcv_csv` rename. |

---

## 8. Definition of Done

- [ ] `yfinance` in `pyproject.toml`; `pip install` succeeds
- [ ] `load_ohlcv_csv()` in `data_loader.py`; `load_nifty_csv` alias present; all 10 call sites updated
- [ ] `find_instrument_csv("TRU")` resolves `data/raw/TRU/tru_daily.csv` after onboarding
- [ ] `find_instrument_csv("NIFTY")` still resolves `data/raw/NIFTY/merged.csv` (exception preserved)
- [ ] `instruments` table has `currency` column; `alembic upgrade head` runs clean
- [ ] `GET /api/v1/instrument/search?q=Transunion` returns ≥ 1 result with ticker, name, exchange, currency, country
- [ ] `POST /api/v1/instrument/onboard {ticker:"TRU", name:"TransUnion", exchange:"NYSE", currency:"USD", country_code:"US"}`:
  - `data/raw/TRU/tru_daily.csv` exists with ≥ 3,000 rows (from 2009-09-01)
  - `data/input/TRU/tru_daily.csv` exists; earliest row >= 2010-01-01; columns = Open/High/Low/Close/Volume
  - `instruments` table has TRU row: `is_available=True`, `currency="USD"`
  - `market_data_cache` has ~260 TRU rows for 2025–2026
- [ ] `GET /api/v1/market-signals?instrument=TRU` returns valid RSI/MACD/BB data
- [ ] `GET /api/v1/experience/rita/geography-overview` includes TRU in US panel
- [ ] `POST /api/v1/instrument/onboard` with duplicate ticker returns 409
- [ ] Daily Ops: search box, results list, confirm form, progress text all render and function correctly
- [ ] Daily Ops instruments list shows TRU (green dot) after successful onboard
- [ ] All three spec files updated in the same commit as code changes
- [ ] App starts end-to-end without errors after migration
