# Session Hand-off — Observability API Refactoring

**Date:** 2026-04-25
**Status:** Steps 1–8 COMPLETE. Resume from Step 9.

## Steps Done (DO NOT redo these)
| Step | File | Done |
|---|---|---|
| 1 | `api/v1/system/instruments.py` | ✅ |
| 2 | `api/v1/system/drift.py` | ✅ |
| 3 | `api/v1/system/training_runs.py` | ✅ |
| 4 | `api/v1/system/data_prep.py` | ✅ |
| 5 | `api/v1/system/market_signals.py` | ✅ |
| 6 | `api/v1/workflow/pipeline.py` | ✅ JWT on /pipeline, config_overrides persistence |
| 7 | `api/experience/rita.py` | ✅ 8 endpoints + all helpers |
| 8 | `api/experience/ops.py` extended | ✅ metrics/summary + step-log added at bottom |

## Steps Remaining — START HERE
| Step | File | What to do |
|---|---|---|
| 9 | `api/experience/pipeline_wizard.py` | NEW file — 3 endpoints |
| 10 | `api/experience/ds.py` | NEW file — 1 new aggregated endpoint |
| 11 | `main.py` | Update — remove observability, add 9 new routers |
| 12 | `api/v1/observability.py` | DELETE this file |
| 13 | `specs/Spec_Python_Code.md` | Update — add new files to tier listings |

---

---

## Step 9 Detail — `api/experience/pipeline_wizard.py` (NEW file)

Three endpoints for the RITA Pipeline tab wizard steps. Router prefix = `/api/v1`, tags = `["experience:pipeline-wizard"]`.

**POST /goal** — Feasibility analysis. Body: `{target_return_pct, time_horizon_days, risk_tolerance}`. Computes annualised target, required monthly return, feasibility label (conservative/realistic/ambitious/unrealistic), yearly returns from MarketDataCacheRepository (NIFTY records), last 12m return. Returns `{"step":1,"name":"Financial Goal","result":{...}}`.

**POST /market** — Market conditions snapshot. Calls `_compute_market_signals(db, instrument, timeframe, periods)` — a PRIVATE helper inside this file (copy the pandas RSI/MACD/BB/ATR/EMA computation from `system/market_signals.py` route body, wrap as a plain function). Uses `_get_active_instrument_id(db)` from config_overrides. Returns `{"step":2,"name":"Market Analysis","result":{...}}`.

**POST /strategy** — Returns strategy config from settings. Calls `get_settings()`. Returns `{"step":3,"name":"Strategy Design","status":"ok","result":{"algorithm":"DoubleDQN","timesteps":200000,...}}`.

For `_get_active_instrument_id(db)` in this file:
```python
def _get_active_instrument_id(db: Session) -> str:
    try:
        from rita.repositories.config_overrides import ConfigOverridesRepository
        cfg = ConfigOverridesRepository(db).find_by_id("active_instrument_id")
        if cfg and cfg.value:
            return cfg.value.upper()
    except Exception:
        pass
    return "NIFTY"
```

Imports needed: `MarketDataCacheRepository`, `get_settings`, `get_db`, `Session`, `APIRouter`, `Depends`, `BaseModel`, `numpy`, `pandas`, `Path`.

---

## Step 10 Detail — `api/experience/ds.py` (NEW file)

One new aggregated endpoint for the DS dashboard initial load. Router prefix = `/api/experience/ds`, tags = `["experience:ds"]`.

**GET /** — Returns instruments list + last 10 training runs + training split dates.
```python
@router.get("/")
def ds_payload(instrument: str = "NIFTY", db: Session = Depends(get_db)):
    from rita.repositories.instrument import InstrumentRepository
    from rita.repositories.training import TrainingRunsRepository
    from rita.repositories.backtest import BacktestRunsRepository
    from rita.core.data_understanding import find_instrument_csv
    from rita.core.data_loader import load_nifty_csv
    from rita.core.technical_analyzer import calculate_indicators

    instruments = [{"id": i.instrument_id, "name": i.name, "exchange": i.exchange,
                    "data_ready": i.is_available} for i in InstrumentRepository(db).read_all()]

    runs = sorted(TrainingRunsRepository(db).read_all(), key=lambda r: r.recorded_at, reverse=True)
    history = [{"run_id": r.run_id, "status": r.status, "instrument": r.instrument or "NIFTY",
                "model_version": r.model_version, "recorded_at": r.recorded_at.isoformat(),
                "backtest_sharpe": r.backtest_sharpe} for r in runs[:10]]

    split = {"train_start": None, "train_end": None, "val_start": None, "val_end": None,
             "backtest_start": None, "backtest_end": None}
    try:
        csv_path = find_instrument_csv(instrument)
        df = calculate_indicators(load_nifty_csv(str(csv_path)))
        idx = int(len(df) * 0.8)
        split.update({"train_start": str(df.index[0].date()), "train_end": str(df.index[idx-1].date()),
                      "val_start": str(df.index[idx].date()), "val_end": str(df.index[-1].date())})
    except Exception:
        pass
    try:
        bts = [r for r in BacktestRunsRepository(db).read_all()
               if r.status in ("complete","completed") and (r.instrument or "NIFTY") == instrument]
        if bts:
            latest = max(bts, key=lambda r: r.ended_at or r.recorded_at)
            split.update({"backtest_start": str(latest.start_date), "backtest_end": str(latest.end_date)})
    except Exception:
        pass

    return {"instruments": instruments, "training_context": {"history": history, "split": split}}
```

---

## Step 11 Detail — `main.py` changes

Read `main.py` first. Make these changes:

**REMOVE:**
```python
from rita.api.v1.observability import router as observability_router
```
and:
```python
app.include_router(observability_router)
```

**ADD to imports (under system tier comment):**
```python
from rita.api.v1.system.instruments import router as instruments_router
from rita.api.v1.system.market_signals import router as market_signals_router
from rita.api.v1.system.training_runs import router as training_runs_router
from rita.api.v1.system.drift import router as drift_router
from rita.api.v1.system.data_prep import router as data_prep_router
```

**ADD to imports (under workflow tier comment):**
```python
from rita.api.v1.workflow.pipeline import router as pipeline_router
```

**ADD to imports (under experience layer comment):**
```python
from rita.api.experience.rita import router as rita_experience_router
from rita.api.experience.pipeline_wizard import router as pipeline_wizard_router
from rita.api.experience.ds import router as ds_router
```

**ADD include_router calls** (grouped by tier, after existing ones):
```python
# System tier additions
app.include_router(instruments_router)
app.include_router(market_signals_router)
app.include_router(training_runs_router)
app.include_router(drift_router)
app.include_router(data_prep_router)

# Workflow tier additions
app.include_router(pipeline_router)

# Experience Layer additions
app.include_router(rita_experience_router)
app.include_router(pipeline_wizard_router)
app.include_router(ds_router)
```

---

## Step 12 — Delete `api/v1/observability.py`

Simply delete the file. All 30 endpoints are now in their correct tier files.

---

## Step 13 — Update `specs/Spec_Python_Code.md`

Read the file first. Under "Tier 1: System" section add:
```
Added during observability refactoring (2026-04-25):
- system/instruments.py — instrument registry CRUD
- system/market_signals.py — RSI/MACD/BB/ATR/EMA time series
- system/training_runs.py — training history, split dates, backtest status poll
- system/drift.py — DriftDetector five-check health report
- system/data_prep.py — file-system checks, JUnit XML, SHAP, data understanding
```

Under "Tier 2: Workflow" add:
```
- workflow/pipeline.py — full pipeline orchestration (JWT), instrument selection, live progress, quick backtest
```

Under "Tier 3: Experience" add:
```
- experience/rita.py — RITA performance, risk, trade, chart, stress endpoints
- experience/pipeline_wizard.py — goal/market/strategy wizard steps
- experience/ds.py — DS dashboard aggregated payload
```

Remove any reference to `api/v1/observability.py`.

---

## What Was Decided This Session

1. **URL strategy:** Option A — keep all existing URLs, move Python code only. No JS changes.
2. **Active instrument state:** Migrate `_active_instrument_id` global → `config_overrides` table row (`override_id = "active_instrument_id"`).
3. **JWT on POST /pipeline:** Add `Depends(get_current_user)` on the `run_pipeline` function.
4. **Scope:** All 4 phases in one sprint.
5. **ds.html:** Active DS app — include in refactoring, create `experience/ds.py`.

---

## Confluence Updated

- Page 66650113 renamed to "API Reference — v1.0 Complete" — already published.
- Script: `project-office/confluence/pages/publish_api_reference_v1.py`

---

## Refactoring: Complete Endpoint → File Mapping (30 endpoints)

All files live under `riia-jun-release/src/rita/`.

### System tier — 5 new files (zero JWT, zero business logic, one or two repos max)

| New file | Endpoints |
|---|---|
| `api/v1/system/instruments.py` | `GET /api/v1/instruments`, `POST /api/v1/instruments`, `PATCH /api/v1/instruments/{id}/availability` |
| `api/v1/system/market_signals.py` | `GET /api/v1/market-signals` |
| `api/v1/system/training_runs.py` | `GET /api/v1/training-history`, `GET /api/v1/training-split`, `GET /api/v1/backtest-status/{run_id}` |
| `api/v1/system/drift.py` | `GET /api/v1/drift` |
| `api/v1/system/data_prep.py` | `GET /api/v1/data-prep/status`, `GET /api/v1/mcp-calls`, `GET /api/v1/test-results`, `GET /api/v1/shap`, `GET /api/v1/data-understanding` |

### Workflow tier — 1 new file

| New file | Endpoints | Notes |
|---|---|---|
| `api/v1/workflow/pipeline.py` | `POST /api/v1/instrument/select`, `GET /api/v1/training-progress`, `POST /api/v1/pipeline`, `POST /api/v1/backtest` | `/pipeline` needs JWT; others do not |

### Experience tier — 3 new files + 1 extension

| New/Extended file | Endpoints |
|---|---|
| `api/experience/rita.py` | `GET /api/v1/instrument/active`, `GET /api/v1/performance-summary`, `GET /api/v1/backtest-daily`, `GET /api/v1/performance-feedback`, `GET /api/v1/portfolio-comparison`, `GET /api/v1/risk-timeline`, `GET /api/v1/trade-events`, `GET /api/v1/stress-scenarios` |
| `api/experience/ops.py` (extend) | Add `GET /api/v1/metrics/summary` and `GET /api/v1/step-log` at the bottom |
| `api/experience/pipeline_wizard.py` | `POST /api/v1/goal`, `POST /api/v1/market`, `POST /api/v1/strategy` |
| `api/experience/ds.py` (new) | `GET /api/experience/ds/` — new aggregated endpoint (instruments + last 10 training runs + split dates) |

### Delete
- `api/v1/observability.py` — after all above files are wired into main.py

---

## Key Technical Details

### Router prefix rule (Option A — URL preservation)
All new routers keep the same URL. Example:
```python
# system/instruments.py
router = APIRouter(prefix="/api/v1", tags=["system:instruments"])
# paths: /instruments, /instrument/active, /instruments/{id}/availability
```

### Active instrument — replace `_active_instrument_id` global

Read helper (add to any file that needs the active instrument):
```python
def _get_active_instrument_id(db: Session) -> str:
    try:
        from rita.repositories.config_overrides import ConfigOverridesRepository
        cfg = ConfigOverridesRepository(db).find_by_id("active_instrument_id")
        if cfg and cfg.value:
            return cfg.value.upper()
    except Exception:
        pass
    return "NIFTY"
```

Write (in `workflow/pipeline.py`, `POST /instrument/select`):
```python
from datetime import datetime, timezone
from rita.schemas.config_overrides import ConfigOverride
from rita.repositories.config_overrides import ConfigOverridesRepository

now = datetime.now(timezone.utc)
ConfigOverridesRepository(db).upsert(ConfigOverride(
    override_id="active_instrument_id",
    key="active_instrument_id",
    value=inst.instrument_id,
    stage="active",
    description="Currently active trading instrument",
    saved_at=now,
    recorded_at=now,
))
```

### ConfigOverride schema fields
```
override_id: str  # primary key — use "active_instrument_id" as the fixed ID
key: str
value: str
stage: Optional[Literal["original","revised","active"]] = "active"
description: Optional[str]
saved_at: datetime
recorded_at: datetime
```

### JWT on POST /pipeline
```python
from rita.auth import get_current_user

@router.post("/pipeline", response_model=PipelineResponse, status_code=202,
             dependencies=[Depends(get_current_user)])
def run_pipeline(req: PipelineRequest) -> PipelineResponse:
    ...
```

### POST /market calls market_signals() — cross-file problem
`experience/pipeline_wizard.py` → `POST /market` calls `market_signals()` which is the same file in observability.py. When split, you cannot import a FastAPI route function.
**Fix:** Copy the computation body (RSI/MACD/BB/ATR/EMA pandas logic) as a private `_compute_market_signals(db, instrument, timeframe, periods)` helper inside `pipeline_wizard.py`. Identical logic, private function.

### Shared helpers — where they go
| Helper | Destination |
|---|---|
| `_collect_metrics_summary()` | `experience/ops.py` |
| `_load_latest_backtest_df()` | `experience/rita.py` |
| `_regime()`, `_MDD_LIMIT_PCT` | `experience/rita.py` |
| `_latest_xml()`, `_history_runs()`, `_parse_junit()`, `_parse_junit_grouped()`, `_extract_module_name()` | `system/data_prep.py` |

### main.py changes needed
1. Remove: `from rita.api.v1.observability import router as observability_router`
2. Remove: `app.include_router(observability_router)`
3. Add system imports + include_router calls under system tier comment
4. Add `from rita.api.v1.workflow.pipeline import router as pipeline_router` + include_router
5. Add rita, pipeline_wizard, ds experience imports + include_router calls

### Spec file to update
`riia-jun-release/specs/Spec_Python_Code.md` — add new files to each tier's listing.

---

## Source file to read before implementing
`riia-jun-release/src/rita/api/v1/observability.py` — 2,249 lines. Read in 400-line slices.
Already fully read in the previous session — do NOT re-read unless a specific section is needed.

## Traceability reference (for context only, no action needed)
- FnO app: 100% tier-compliant (reference implementation)
- RITA app: 7% compliant (14 API calls, 1 correct)
- Ops app: 14% compliant
- DS app: 0% compliant
All will be compliant after this refactoring since URLs are preserved and code moves to correct tiers.
