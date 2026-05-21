# Feature 09 — Data Pipeline: Add New Instrument — Plan Status

**Status:** COMPLETE — All runs done (2026-05-18)  
**Last updated:** 2026-05-18

---

## Current State

Requirements draft complete. Feature adds a self-service instrument onboarding pipeline from the Daily Ops page — company name search → Yahoo Finance ticker picker → automated data fetch, normalize, and DB seed.

---

## Task Breakdown

### Run A — Backend Pipeline

- [x] R1: Add `yfinance` to `pyproject.toml`
- [x] R2: Rename `load_nifty_csv()` → `load_ohlcv_csv()` in `data_loader.py` + backward-compat alias + update all 10 call sites
- [x] R3: Make `find_instrument_csv()` dynamic (glob-based) in `data_understanding.py`; preserve NIFTY/BANKNIFTY exceptions
- [x] R4: Add `currency` column to `instruments` model + Alembic migration; update `instruments.py` router to include `currency` in list/create
- [x] R5: New service `src/rita/services/instrument_onboard.py` — `search_tickers()`, `fetch_raw_data()`, `process_to_input()`, `seed_market_cache()`
- [x] R6: New router `src/rita/api/v1/workflow/instrument_onboard.py` — `GET /api/v1/instrument/search`, `POST /api/v1/instrument/onboard`
- [x] R7: Register new router in `main.py`

### Run B — Frontend + Experience Layer + Specs

- [x] R8: `daily-ops.js` — add `searchInstruments()`, `selectSearchResult()`, `onboardInstrument()`, `cancelOnboard()` + window exports
- [x] R9: `ops.html` — targeted Edit: add search input, results list, confirm form, progress div inside Daily Ops instruments section
- [x] R10: `experience/rita.py` geography-overview — dynamic instrument list from DB (done in Run A)
- [x] R11: Spec files updated — `Spec_Data.md`, `Spec_RITA_App.md`, `Spec_Python_Code.md`, `Spec_JS_Code.md`
- [x] R12: RITA dynamic instrument tabs — `rita.html` + `main.js` `loadInstrumentTabs()` (added Run B)
- [x] QA — 21 unit tests, all passing
- [x] TechWriter — Confluence Engineering v19, all spec files current

---

## Decisions Log

| Date | Decision |
|---|---|
| 2026-05-17 | Data source: yfinance. Fetch from 2009-09-01; usable range starts 2010-01-01 (warmup for indicator calculation). |
| 2026-05-17 | Ticker search via `yf.Search(query).quotes` — user picks from list when multiple listings exist (e.g., TRU vs TRU.TO). Currency auto-detected from yfinance result. |
| 2026-05-17 | DB cache window: 2025–2026 only (consistent with existing instruments). Full history in input CSV for training. |
| 2026-05-17 | `load_nifty_csv` alias kept post-rename for safety; Engineer updates all 10 call sites to `load_ohlcv_csv`. |
| 2026-05-17 | Geography-overview endpoint made dynamic — new instruments self-assign to geography bucket via `country_code`. |
| 2026-05-17 | No JWT on onboard endpoint (same pattern as `pipeline.py`). |

---

## Blockers

None.

## Handoff — Resume 2026-05-18

**Where we stopped:** /enhance Run A complete. QA agent (Step 5) was blocked at 96% quota.

**Next session steps (in order):**
1. Run QA agent — task brief: `project-office/task-briefs/task-brief-20260517-2137.md`
   - Test file target: `tests/unit/test_instrument_onboard.py`
   - Two endpoints to test: `GET /api/v1/instrument/search` + `POST /api/v1/instrument/onboard`
   - Mock yfinance; verify 400/409/502 edge cases
2. Run TechWriter agent (Step 6) — Confluence engineering page + spec confirmation
3. Write run log JSON to `riia-ai-org/agent-ops/runs/run-20260517-2137.json`
4. Run `/enhance ops "Feature 09 Run B — ops frontend: daily-ops.js search/onboard UI, ops.html panel insert, geography-overview already done in Run A"`

**Key facts:**
- Branch merged to master at `872aeaf`; migration fix committed at `b35a944`
- Alembic stamped at `e9f3b2c41a07` then upgraded to `20260517_add_currency`
- API endpoints live: `GET /api/v1/instrument/search?q=...` and `POST /api/v1/instrument/onboard`
- Run B (frontend) needs: `daily-ops.js` + `ops.html` only; geography-overview already made dynamic in Run A

---

## Notes

- Full requirements: `REQUIREMENTS.md`
- Root `PLAN_STATUS.md` should have one-line pointer to this file
- Estimated /enhance runs: 2 (Run A backend-only, Run B frontend + experience + specs)
- Feature number: 09 (folder: `project-office/features/May/09 Build complete data pipeline to add new instrument/`)


  Done today:
  - Feature 09 Run A fully implemented and merged (872aeaf) — all R1–R7 complete
  - Migration fixed and applied (b35a944) — instruments.currency column live
  - Both API endpoints live on master

  Tomorrow — resume at:
  1. QA agent (tests/unit/test_instrument_onboard.py) — mock yfinance, test 400/409/502 edge cases
  2. TechWriter agent — Confluence + spec confirmation
  3. Write run log JSON
  4. /enhance ops Run B — daily-ops.js + ops.html UI (search box, results list, confirm form)