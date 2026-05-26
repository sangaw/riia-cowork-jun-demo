# Feature 16 — All Instruments Data Refresh Command

**Status:** Requirements Complete  
**Date:** 2026-05-20  
**Owner:** San G  
**Approach:** /enhance multi-agent orchestration (backend service + slash command)

---

## 1. Problem Statement

All 11 instruments have data that is stale by days to months:

| Instrument | Data ends | Gap (as of 2026-05-20) |
|---|---|---|
| NIFTY | 2025-12-31 (merged.csv) | ~5 months |
| BANKNIFTY | 2026-04-02 | ~7 weeks |
| ASML | 2026-04-24 | ~4 weeks |
| NVIDIA | 2026-04-02 | ~7 weeks |
| RELIANCE, SBIN, ASRNL, ATO, AEX, DJI, IXIC | ~2026-05-19 | likely current |

NIFTY and BANKNIFTY previously used manual CSVs (`nifty_manual.csv`, `banknifty_manual.csv`) appended after each trading day. This manual process is replaced by this automated command which fetches from yfinance for all instruments at once.

The command must follow the established data pipeline: **raw CSV → input CSV → DB cache**.

---

## 2. Scope

**In scope:**
- Check data gap for all 11 instruments (ATHER excluded — no yfinance data yet)
- Fetch delta from yfinance (`last_date + 1` to yesterday) for each instrument
- Append new rows to a `_yf.csv` companion file in `data/raw/{TICKER}/` (see §3)
- Rebuild `data/input/{TICKER}/` normalized CSV from the full raw source
- Upsert new `(instrument, date)` rows into `market_data_cache` — no deletes, no full overwrites
- Print a gap report and results summary to stdout
- Exposed as a Claude Code slash command: `/refresh-all-instruments-data`
- Backend API endpoint: `POST /api/v1/instrument/refresh-all`

**Out of scope:**
- ATHER (no yfinance data available — IPO 2025, not indexed)
- Intraday or non-daily timeframes
- Deleting or re-seeding the full DB — only targeted upsert of new dates
- UI button in Ops dashboard (slash command only for now)

---

## 3. NIFTY / BANKNIFTY Raw File Strategy

NIFTY and BANKNIFTY have historical raw files in a different date format (IST timezone: `1999-07-01 00:00:00+05:30`) which `load_ohlcv_csv()` detects from the first row. Appending yfinance plain ISO rows to these files would cause misparsing.

**Solution — Companion `_yf.csv` file:**

| Instrument | Existing raw file (keep untouched) | New companion file |
|---|---|---|
| NIFTY | `data/raw/NIFTY/merged.csv` | `data/raw/NIFTY/nifty_yf.csv` |
| BANKNIFTY | `data/raw/BANKNIFTY/banknifty_daily_25yr_rounded.csv` | `data/raw/BANKNIFTY/banknifty_yf.csv` |

On each refresh, `nifty_yf.csv` and `banknifty_yf.csv` are updated in place (overwritten with the full yfinance download from 2009-09-01 to yesterday). This replaces the old `nifty_manual.csv` / `banknifty_manual.csv` approach.

For all other instruments, their existing `data/raw/{TICKER}/{ticker_lower}_daily.csv` is appended to directly (it was already written by yfinance via Feature 09).

`load_instrument_data()` is extended to check for `{ticker_lower}_yf.csv` in `data/raw/{TICKER}/` and merge it alongside the primary file (same dedup + sort logic as the existing `nifty_manual.csv` merge).

---

## 4. yfinance Ticker Mapping

Hardcoded in the refresh service (`src/rita/services/data_refresh.py`). The `instruments` table has no `yf_ticker` column — add one via Alembic migration so the mapping is DB-driven and extensible.

| instrument_id | yfinance ticker | Notes |
|---|---|---|
| NIFTY | `^NSEI` | Index — uses companion file strategy |
| BANKNIFTY | `^NSEBANK` | Index — uses companion file strategy |
| ASML | `ASML.AS` | Euronext Amsterdam |
| NVIDIA | `NVDA` | NASDAQ |
| RELIANCE | `RELIANCE.NS` | NSE |
| SBIN | `SBIN.NS` | NSE |
| ASRNL | `ASRNL.AS` | Euronext Amsterdam |
| ATO | `ATO.PA` | Euronext Paris |
| AEX | `^AEX` | Index |
| DJI | `^DJI` | Index |
| IXIC | `^IXIC` | Index |
| ATHER | *(skip)* | No yfinance data |

---

## 5. Backend Requirements

### 5.1 DB Schema Change

Add `yf_ticker VARCHAR` column to the `instruments` table via Alembic migration. Populate from the mapping above in a data migration or seeding step. This makes the ticker mapping DB-driven and allows future instruments to specify their yfinance ticker at onboard time.

Also update `POST /api/v1/instrument/onboard` to accept `yf_ticker` in the request body and store it.

### 5.2 New Service — `src/rita/services/data_refresh.py`

```python
check_gap(instrument_id: str) -> dict
    # Returns: {instrument_id, last_date, gap_days, yf_ticker}

fetch_and_write_raw(instrument_id: str, yf_ticker: str) -> tuple[Path, int]
    # Downloads from yfinance (start = last_date + 1 day, or 2009-09-01 for companion-file instruments)
    # For NIFTY/BANKNIFTY: overwrites data/raw/{TICKER}/{ticker_lower}_yf.csv
    # For others: appends new rows to existing data/raw/{TICKER}/{ticker_lower}_daily.csv
    # Returns (raw_path, new_row_count)

rebuild_input(instrument_id: str) -> Path
    # Calls load_instrument_data() to get merged view
    # Normalizes and overwrites data/input/{TICKER}/{ticker_lower}_daily.csv
    # Returns input_path

upsert_cache_delta(db: Session, instrument_id: str) -> int
    # Reads data/input/{TICKER}/{ticker_lower}_daily.csv
    # Filters year >= 2025
    # Queries existing dates in market_data_cache for this instrument
    # Inserts only (instrument, date) pairs not already present
    # Uses db.add_all() + db.commit() — no deletes
    # Returns count inserted

refresh_all(db: Session) -> list[dict]
    # Runs check_gap → fetch_and_write_raw → rebuild_input → upsert_cache_delta
    # for each instrument in the ticker map (skips ATHER)
    # Returns list of per-instrument result dicts
```

### 5.3 Update `load_instrument_data()` — `src/rita/core/data_loader.py`

Extend to check for `{ticker_lower}_yf.csv` in `data/raw/{TICKER}/`:

```python
# After loading primary CSV, check for companion yf file
yf_path = Path(settings.data.raw_dir) / instrument.upper() / f"{instrument.lower()}_yf.csv"
if yf_path.exists():
    df_yf = load_ohlcv_csv(str(yf_path))
    df = pd.concat([df, df_yf])
    df = df[~df.index.duplicated(keep="last")].sort_index()
    df = df.dropna(subset=["Close"])
```

This is the same pattern as the existing `nifty_manual.csv` merge — just generalized to the `_yf.csv` companion.

### 5.4 New API Endpoint

**Router:** `src/rita/api/v1/workflow/instrument_onboard.py` (add to existing file)

```
POST /api/v1/instrument/refresh-all
```

No request body. No JWT required (same pattern as onboard endpoint). Returns:

```json
{
  "refreshed": 9,
  "already_current": 2,
  "results": [
    {"instrument": "NIFTY", "gap_days": 140, "raw_rows_added": 98, "db_rows_inserted": 98, "status": "ok"},
    {"instrument": "RELIANCE", "gap_days": 0, "raw_rows_added": 0, "db_rows_inserted": 0, "status": "current"},
    ...
  ]
}
```

Errors per instrument are caught and included in results as `"status": "error"` with `"error": "..."` — one bad instrument does not abort the rest.

---

## 6. Slash Command

**File:** `riia-jun-release/.claude/commands/refresh-all-instruments-data.md`

The command:
1. Checks the app is running (GET /health)
2. Calls `POST /api/v1/instrument/refresh-all`
3. Prints a formatted gap report and results table
4. Reports total new rows and DB insertions

**Companion script:** `project-office/scripts/run_data_refresh.py`
- Can be called standalone: `python project-office/scripts/run_data_refresh.py`
- Uses `requests` to call the API (defaults to `http://localhost:8000`)

---

## 7. Specs to Update (same commit as code)

| Spec | What changes |
|---|---|
| `Spec_Data.md` | §6 (Adding New Daily Data) — replace manual process description with data-refresh command; document `_yf.csv` companion file pattern; note `nifty_manual.csv` is superseded |
| `Spec_Python_Code.md` | Add `data_refresh.py` service; document `load_instrument_data()` companion-file extension; document new endpoint |
| `Spec_RITA_App.md` | Add `/api/v1/instrument/refresh-all` to API inventory |

---

## 8. Definition of Done

- [ ] `yf_ticker` column added to instruments table + Alembic migration runs cleanly
- [ ] `yf_ticker` populated for all 11 instruments in DB seed
- [ ] `data_refresh.py` service implemented with all 4 functions
- [ ] `load_instrument_data()` extended with companion `_yf.csv` merge
- [ ] `POST /api/v1/instrument/refresh-all` endpoint live
- [ ] `/refresh-all-instruments-data` slash command works end-to-end
- [ ] `project-office/scripts/run_data_refresh.py` standalone script present
- [ ] Running the command produces a gap report and updates CSVs + DB
- [ ] `nifty_manual.csv` / `banknifty_manual.csv` workflow is superseded (files retained but not required)
- [ ] All 3 spec files updated in same commit
- [ ] Unit tests: `tests/unit/test_data_refresh.py` — mock yfinance, test gap check, append, upsert delta, no-gap case, yfinance 502 case
- [ ] Confluence Engineering page updated

---

## 9. Estimated /enhance Runs

| Run | Focus | App |
|---|---|---|
| Run A | Backend: `yf_ticker` migration + `data_refresh.py` service + `load_instrument_data()` extension + endpoint + slash command + script | `ops` |
| Run B | QA: unit tests for `data_refresh.py` + TechWriter: spec updates + Confluence | `ops` |
