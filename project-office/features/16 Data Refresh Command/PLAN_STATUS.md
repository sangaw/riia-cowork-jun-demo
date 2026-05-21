# Feature 16 — All Instruments Data Refresh Command — Plan Status

**Status:** COMPLETE — Run A (e920177) + Run B (8e7aa40) merged to master  
**Last updated:** 2026-05-21

---

## Current State

Requirements complete. Analysis done in session 2026-05-20. Feature replaces the manual `nifty_manual.csv` / `banknifty_manual.csv` workflow with an automated yfinance-based refresh that covers all 11 instruments and follows the established raw → input → DB pipeline.

Full requirements: `REQUIREMENTS.md` in this folder.

---

## Task Breakdown

### Run A — Backend + Slash Command (commit e920177)

- [x] R1: Add `yf_ticker VARCHAR` column to `instruments` table — Alembic migration + populate via seed update in `main.py`
- [x] R2: Update `POST /api/v1/instrument/onboard` request schema to accept `yf_ticker`
- [x] R3: Extend `load_instrument_data()` in `data_loader.py` to check for `{ticker_lower}_yf.csv` companion file in `data/raw/{TICKER}/` and merge (same pattern as existing `nifty_manual.csv` merge)
- [x] R4: New service `src/rita/services/data_refresh.py` — `check_gap()`, `fetch_and_write_raw()`, `rebuild_input()`, `upsert_cache_delta()`, `refresh_all()`
- [x] R5: New endpoint `POST /api/v1/instrument/refresh-all` added to `src/rita/api/v1/workflow/instrument_onboard.py` + registered in `main.py`
- [x] R6: Slash command `riia-jun-release/.claude/commands/refresh-all-instruments-data.md`
- [x] R7: Standalone script `project-office/scripts/run_data_refresh.py`

### Run B — QA + TechWriter (commit 8e7aa40)

- [x] R8: Unit tests `tests/unit/test_data_refresh.py` — mock yfinance; test gap check, append, upsert delta, no-gap case, yfinance 502 error handling
- [x] R9: Spec updates — `Spec_Data.md`, `Spec_Python_Code.md`, `Spec_RITA_App.md`
- [x] R10: Confluence Engineering page update (page 76611602 updated to v28)

---

## Decisions Log

| Date | Decision |
|---|---|
| 2026-05-20 | NIFTY and BANKNIFTY will use yfinance (`^NSEI`, `^NSEBANK`) going forward — manual CSV workflow retired |
| 2026-05-20 | Companion `_yf.csv` file strategy for NIFTY/BANKNIFTY — avoids IST timezone date format conflict in existing raw files |
| 2026-05-20 | DB upsert is targeted (insert new dates only) — no full table delete, no per-instrument drop; learned from prior incident |
| 2026-05-20 | `yf_ticker` column added to instruments table so mapping is DB-driven, not hardcoded |
| 2026-05-20 | ATHER excluded — no yfinance data available (IPO 2025, not yet indexed) |
| 2026-05-20 | Slash command: `/refresh-all-instruments-data` — Claude Code slash command, not Ops dashboard UI button |

---

## Blockers

None.

---

## Key Context for Engineer Agent (Run A)

**Ticker mapping** (hardcode in service, also seed into DB):

| instrument_id | yf_ticker |
|---|---|
| NIFTY | `^NSEI` |
| BANKNIFTY | `^NSEBANK` |
| ASML | `ASML.AS` |
| NVIDIA | `NVDA` |
| RELIANCE | `RELIANCE.NS` |
| SBIN | `SBIN.NS` |
| ASRNL | `ASRNL.AS` |
| ATO | `ATO.PA` |
| AEX | `^AEX` |
| DJI | `^DJI` |
| IXIC | `^IXIC` |

**Companion file rule:**
- NIFTY → `data/raw/NIFTY/nifty_yf.csv` (full download from 2009-09-01, overwrite on each refresh)
- BANKNIFTY → `data/raw/BANKNIFTY/banknifty_yf.csv` (same)
- All others → append delta to existing `data/raw/{TICKER}/{ticker_lower}_daily.csv`

**DB upsert safety:** Query `SELECT DISTINCT date FROM market_data_cache WHERE underlying = ?` first, then insert only new dates. Never delete existing rows.

**Existing files to modify:**
- `src/rita/core/data_loader.py` — `load_instrument_data()` companion file merge
- `src/rita/api/v1/workflow/instrument_onboard.py` — add refresh-all endpoint
- `src/rita/main.py` — register endpoint (if not auto-discovered) + populate `yf_ticker` in `_SEED_INSTRUMENTS`
- `src/rita/schemas/instrument.py` — add `yf_ticker` field
- `src/rita/models/instrument.py` — add `yf_ticker` column

**New files to create:**
- `src/rita/services/data_refresh.py`
- `riia-jun-release/.claude/commands/refresh-all-instruments-data.md`
- `project-office/scripts/run_data_refresh.py`
- `alembic/versions/{hash}_add_yf_ticker.py`

---

## Notes

- Estimated /enhance runs: 2 (Run A backend + command; Run B QA + TechWriter)
- Feature folder: `project-office/features/16 Data Refresh Command/`
- Root `PLAN_STATUS.md` should have a one-line pointer to this file after Run A completes



Run /agent-performance-improvements to address these before the next
  /enhance run.
  ─────────────────────────────────────────────────────────

  What's live on master:
  - POST /api/v1/instrument/refresh-all — fetches delta OHLCV from yfinance
  for all 11 instruments, rebuilds input CSVs, upserts to DB cache
  - yf_ticker column in instruments table (migration applied)
  - /refresh-all-instruments-data slash command
  - project-office/scripts/run_data_refresh.py standalone script
  - 8 unit tests in tests/unit/test_data_refresh.py

  Next step (Run B): QA integration testing + TechWriter spec consolidation
  — or invoke the slash command against the live app to verify end-to-end.