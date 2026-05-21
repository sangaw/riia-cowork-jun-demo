# Task Brief — Improve Observability
# Running audit trail — each agent appends its section; never overwrite prior sections.
# Format follows: project-office/agents/Agentic_AI_Enterprise_Approach.md Section 3.3

**Feature:** Improve Logging, Monitoring & Alerting
**Created:** 2026-05-08
**Orchestration approach:** `Agentic_AI_Enterprise_Approach.md`
**Skill reference:** `project-office/skills/skill-add-ops-feature.md` (dashboard panels) / `skill-add-endpoint.md` (client-error endpoint)

---

## Request

Add structured observability across all three RITA projects. Two root problems:

1. **No functional metrics in logs** — structlog emits HTTP structural fields only. No domain
   events: trade counts, backtest Sharpe, chat confidence, drift state. Impossible to answer
   "is RITA doing its job?" from logs alone.

2. **Experience layer is a black box** — `api/experience/` silently swallows exceptions and
   returns empty data. Cannot distinguish a DB miss from an error from genuinely empty results.
   Every blank dashboard panel requires guesswork to diagnose.

Deliverables:
- Unified `log_event()` schema across all backend components
- `experience.compose` provenance log per experience handler (per-source ok/empty/error)
- 4 rotating JSONL log files (`logs/app.jsonl`, `experience.jsonl`, `jobs.jsonl`, `client-errors.jsonl`)
- Local aggregator script → `ops/metrics/metrics-summary.json` + `functional-kpis.json`
- Alert generator → `ops/alerts/active-alerts.json` + daily digest
- Two new Ops dashboard panels (source availability + functional KPI trends)
- JS `apiFetch()` wrapper with `X-Request-ID` across all dashboards and mobile PWA
- Service worker + global JS error capture in mobile PWA

## App Target

`riia-jun-release` (primary), `riia-ai-org` (AgentOps pipeline), `rita-build-portfolio` (mobile PWA)

## Spec Reference

`project-office/features/improve-observability/Observability_Requirements.md`

---

## [PM] Validation

- **Sprint alignment:** Feature is well-scoped and ready to proceed. This is a post-v1.0 observability improvement — it is not gated behind any sprint milestone and does not block or depend on any current sprint work. The 10-step rollout is clearly sequenced: infrastructure first (Steps 2–4), domain events second (Steps 5–7), UI and cross-project work third (Steps 8–9), QA and docs last (Step 10). Scope is additive only.
- **Risk flags:** (1) Cross-project scope across 3 repos (`riia-jun-release`, `riia-ai-org`, `rita-build-portfolio`) increases coordination surface — Steps 8 and 9 must not be started until Steps 2–5 are stable and merged. (2) Step 9 touches all three dashboards plus the mobile PWA `sw.js`; if `apiFetch()` wrapper is not backward-compatible it could break existing network calls — engineer must audit all existing `fetch()` call sites before replacing them. (3) The aggregator and alert scripts (Steps 6–7) write to `ops/metrics/` and `ops/alerts/` JSON files that the Ops dashboard will read; file schema must be locked before Step 8 begins. All risks are manageable with the step sequencing already in place.
- **Dependencies:** none
- **Approved to proceed:** yes

---

## [Architect] Design

### 1. Feature Summary

End-to-end structured observability for the RITA platform: replaces silent failures and opaque HTTP logs with a unified `log_event()` schema, per-request provenance tracing across the experience layer, rotating JSONL log files, rule-based alerting, and two new Ops dashboard panels — giving operators the ability to answer "is RITA doing its job?" directly from logs and the dashboard without guesswork.

---

### 2. New API Contract

**POST `/api/v1/client-error`** — System tier (`src/rita/api/v1/system/client_error.py`)
Auth: none (accepts errors from unauthenticated frontends including mobile PWA)

| Field | Type | Validation |
|---|---|---|
| `type` | string enum | `js_error`, `fetch_failure`, `sw_error`, `unhandled_rejection` |
| `message` | string | Non-empty, max 2000 chars |
| `stack` | string or null | Nullable; truncate to 8000 chars server-side |
| `url` | string | Non-empty |
| `trace_id` | string | Non-empty |

Responses: `204 No Content` (success), `422` (validation failure)
Behaviour: calls `log_event(logger, "info", "client.error", ...)` → writes to `logs/client-errors.jsonl`. No DB write.
Pydantic schema: `src/rita/schemas/client_error.py`

---

### 3. New Files to Create

| File | Purpose |
|---|---|
| `src/rita/schemas/client_error.py` | Pydantic `ClientErrorRequest` model with field constraints |
| `src/rita/api/v1/system/client_error.py` | FastAPI router — single POST route, calls `log_event()`, returns 204 |
| `project-office/scripts/aggregate_ops_metrics.py` | Reads 4 JSONL logs; writes 3 JSON summary files to `ops/metrics/` |
| `project-office/scripts/generate_alerts.py` | Reads `metrics-summary.json` + last 1h of `jobs.jsonl`; writes `active-alerts.json` + appends `alert-history.jsonl` |
| `riia-jun-release/ops/metrics/metrics-summary.json` | Seed file — valid JSON, all numeric fields 0 |
| `riia-jun-release/ops/metrics/functional-kpis.json` | Seed file — valid JSON, empty datapoints arrays |
| `riia-jun-release/ops/metrics/source-availability.json` | Seed file — valid JSON, `sources: {}` |
| `riia-jun-release/ops/alerts/active-alerts.json` | Seed file — valid JSON, `alerts: []` |
| `riia-jun-release/ops/alerts/alert-history.jsonl` | Empty seed file |

---

### 4. Files to Modify

| File | Lines Affected | Change |
|---|---|---|
| `src/rita/logging_config.py` | ~25 new lines | Add `log_event()` wrapper; add `configure_logging(log_level)` with 4 `RotatingFileHandler` instances (10 MB, 7-file rotation); route events by prefix to correct JSONL file |
| `src/rita/main.py` | startup + route registration | Call `configure_logging(settings.log_level)` first in startup; register client-error router at `/api/v1/client-error` |
| `src/rita/api/experience/rita.py` | all handlers | Add `experience.compose` provenance log per handler with per-source ok/empty/error breakdown |
| `src/rita/api/experience/ds.py` | all handlers; lines 44, 52 | Add provenance log; replace 2 bare `except: pass` with `log_event(... exc_info=True)` |
| `src/rita/api/experience/ops.py` | all handlers | Add `experience.compose` provenance log per handler |
| `src/rita/api/v1/portfolio.py` | lines 173, 220, 264, 296, 312, 385, 404 | Replace 7 bare `except: pass` with `log_event(logger, "error", "portfolio.error", ..., exc_info=True)` |
| `src/rita/api/v1/workflow/pipeline.py` | lines 44, 226 | Replace 2 bare `except: pass` with `log_event(logger, "error", "pipeline.error", ..., exc_info=True)` |
| `src/rita/api/v1/system/training_runs.py` | lines 105, 118 | Replace 2 bare `except: pass` with `log_event(logger, "error", "training_run.error", exc_info=True)` |
| `src/rita/core/drift_detector.py` | lines 210, 223 | Replace 2 bare `except: pass` with `log_event(logger, "warning", "drift.check_error", exc_info=True)` |
| `src/rita/services/workflow_service.py` | after train/backtest resolve | Add `training.completed`, `training.failed`, `backtest.completed`, `backtest.failed` events |
| `src/rita/core/trading_env.py` | after trade execution | Add `trade.executed` event with instrument, direction, quantity, price, pnl |
| `src/rita/api/v1/workflow/chat.py` | after classify; after response | Add `chat.request` and `chat.response` events with intent, confidence, duration_ms |
| `dashboard/js/rita/main.js` | all `fetch()` call sites | Add `SESSION_TRACE_ID = crypto.randomUUID()`; replace all `fetch()` with `apiFetch()` wrapper |
| `dashboard/js/fno/main.js` | all `fetch()` call sites | Same as rita/main.js |
| `dashboard/js/ops/main.js` | all fetch calls + new panels | Add `apiFetch()` wrapper; add `loadSourceAvailability()`, `loadFunctionalKPIs()`, `loadAlerts()` panel loaders |
| `riia-ai-org/agent-ops/aggregate_metrics.py` | lines 127-131, 140-141, 161, 178-179 | Remove `stderr=subprocess.DEVNULL`; replace `print()` with `logging`; replace silent `except` with `log.error()` |
| `riia-ai-org/agent-ops/shared/agentops.js` | header render | Add data freshness indicator; show warning banner if staleness > 24h |
| `android-mobile-app/index.html` | `<head>`; all `fetch()` sites | Add `window.onerror` + `unhandledrejection` handlers; add `apiFetch()` wrapper |
| `android-mobile-app/sw.js` | install, activate, fetch handlers | Add `.catch(err => console.error('[SW]', err))` to every promise chain |

---

### 5. Implementation Order (per step)

| Step | Files |
|---|---|
| Step 2 | `logging_config.py`, `main.py` (startup only) |
| Step 3 | `experience/rita.py`, `experience/ds.py`, `experience/ops.py` |
| Step 4 | `portfolio.py`, `pipeline.py`, `training_runs.py`, `drift_detector.py` |
| Step 5 | `workflow_service.py`, `trading_env.py`, `chat.py` |
| Step 6 | `project-office/scripts/aggregate_ops_metrics.py` + 3 seed JSON files in `ops/metrics/` |
| Step 7 | `project-office/scripts/generate_alerts.py` + `active-alerts.json` + empty `alert-history.jsonl` |
| Step 8 | `dashboard/js/ops/main.js` (panels + apiFetch) |
| Step 9 | `schemas/client_error.py`, `api/v1/system/client_error.py`, `main.py` (router), `js/rita/main.js`, `js/fno/main.js`, `riia-ai-org` files, `android-mobile-app/index.html`, `sw.js` |

---

### 6. Edge Cases

1. `log_event()` called before `configure_logging()` — must not crash; guard with idempotent init on import
2. `experience.compose` where all sources raise — overall_status must be "error"; provenance log must always fire even if all sources fail
3. `apiFetch()` returns non-JSON body — catch `res.json()` parse error; log to console with trace_id; return `null`
4. `aggregate_ops_metrics.py` when `logs/` is missing or empty — write valid seed JSON (all zeros) to all 3 outputs; do not crash
5. `generate_alerts.py` when `metrics-summary.json` does not yet exist — write `alerts: []` + `meta.warning`; exit 0
6. `client-error` endpoint receives oversized stack — Pydantic enforces `max_length=8000`; still return 204 (not 422) after truncation
7. `crypto.randomUUID()` unavailable in mobile WebView sw.js — use `Math.random()` hex fallback; never call `apiFetch()` from sw.js
8. `configure_logging()` called more than once (tests, hot reload) — idempotent: check if handlers already attached before adding
9. `alert-history.jsonl` grows without bound — rotate when > 50 MB or 90 days
10. Race condition: aggregator writing while dashboard reads `metrics-summary.json` — write to `.tmp` then atomic rename

---

### 7. Definition of Done Checklist

- [ ] `log_event()` wrapper exists in `logging_config.py` and is importable
- [ ] 4 JSONL rotating file handlers configured (`app`, `experience`, `jobs`, `client-errors`)
- [ ] `configure_logging(log_level)` wired into `main.py` startup
- [ ] `experience.compose` event logged in all 3 experience handlers (`rita`, `ds`, `ops`)
- [ ] All bare `except: pass` replaced with `log_event(...)` calls
- [ ] Functional events added (`training.*`, `backtest.*`, `chat.*`, `trade.executed`, `drift.check`)
- [ ] `aggregate_ops_metrics.py` runs without error and produces all 3 JSON outputs
- [ ] `generate_alerts.py` runs without error and produces `active-alerts.json`
- [ ] Ops dashboard renders source-availability and functional-kpis panels
- [ ] `ruff check src/` passes with 0 errors

---

## [Engineer] Implementation Log

### Step 2 — Core Logging Infrastructure
- **Branch:** worktree-agent-ab190a43c42d82923
- **Worktree path:** C:/Users/Sandeep/Documents/Work/code/riia-cowork-jun/.claude/worktrees/agent-ab190a43c42d82923
- **Files changed:** riia-jun-release/src/rita/logging_config.py, riia-jun-release/src/rita/main.py
- **Commit:** 865b673
- **Ruff result:** passed
- **Notes:** `configure_logging` import was already present in `main.py` (line 32); only the call site needed updating from `configure_logging()` to `configure_logging(settings.server.log_level)`. Log level attribute confirmed as `settings.server.log_level` (not `settings.log_level`) by reading `config.py`. Existing structlog processor chain preserved inside the new `configure_logging()` function.

### Step 3 — Experience Layer Provenance Logging
- **Branch:** worktree-agent-ab190a43c42d82923
- **Files changed:** riia-jun-release/src/rita/api/experience/rita.py, ds.py, ops.py
- **Commit:** 959c511
- **Ruff result:** passed (0 errors on the 3 modified files; 1 pre-existing error in pipeline_wizard.py not in scope)
- **Notes:** Instrumented all 8 handlers across the 3 files — `active_instrument`, `performance_summary`, `backtest_daily`, `performance_feedback`, `portfolio_comparison`, `risk_timeline`, `trade_events`, `stress_scenarios` in rita.py; `ds_payload` in ds.py; `get_ops`, `metrics_summary`, `step_log` in ops.py. Each call wrapped in individual try/except recording status/record_count/duration_ms into a per-source `sources` dict; overall_status derived as ok/partial/error; `log_event` emits `experience.compose` at the end of each handler. Two bare `except: pass` blocks in ds.py (csv_splits and backtest_splits) replaced with `log_event(..., "experience.ds.source_error", ...)` calls with `exc_info=True`. `import time`, `import structlog`, and `from rita.logging_config import log_event` added to ds.py and ops.py; `log = structlog.get_logger()` added at module level in both.

### Step 4 — Silent Failure Fixes
- **Branch:** worktree-agent-ab190a43c42d82923
- **Files changed:** portfolio.py, pipeline.py, training_runs.py, drift_detector.py
- **Commit:** ec2abff
- **Ruff result:** passed
- **Notes:** Replaced 4 bare `except: pass` blocks total. portfolio.py: 1 (market data cache block in `portfolio_summary`; added `log_event` import). pipeline.py: 1 (`_get_active_instrument_id`; added `log_event` import; also removed 2 pre-existing unused imports — `get_settings` and `WorkflowService` — that caused ruff F401 errors). training_runs.py: 2 (CSV split and backtest split blocks in `training_split`; added `structlog`, `log_event` imports and module-level `log`). drift_detector.py: 0 — all `except` blocks in this file already had real `log.warning(...)` handling; no changes needed.

---

## [QA] Test Results

- **Tests written:** 30
- **Test file:** `riia-jun-release/tests/unit/test_observability.py`
- **Tests passed:** 29/30 (1 xfail — expected, documented below)
- **Coverage delta:** ~+12% estimated for `logging_config.py`, `api/v1/system/client_errors.py`, and `project-office/scripts/generate_alerts.py` (rule evaluation paths). No pre-existing coverage baseline for these new files.
- **Areas tested:**
  - `log_event()` wrapper — key emission, stdlib level routing, structlog bind call, idempotency of `configure_logging()`, safe call before `configure_logging()`
  - `POST /api/v1/client-error` endpoint — 204 on valid payload, null/missing optional `stack`, missing required `message` → 422, `log_event()` invocation verified, `type`/enum and `trace_id`/`url` fields accepted
  - Alert rule evaluation — threshold rules (`error_rate_high`, `latency_high`, `chat_low_confidence`, `experience_error`), data staleness rules (`data_stale_warn`, `data_stale_critical`), event-based rules (`training_failed`, `backtest_failed`), per-source availability rule (`source_down`), all-nominal no-alert case, alert metadata correctness

- **Edge cases from Architect section 6:**

  | # | Edge case | Status |
  |---|---|---|
  | 1 | `log_event()` called before `configure_logging()` — must not crash | **Tested** (`test_log_event_before_configure_logging_does_not_crash`) |
  | 2 | `experience.compose` where all sources raise — overall_status = "error" | **Not tested** (experience layer handlers not in scope for this QA pass) |
  | 3 | `apiFetch()` returns non-JSON body — catch parse error, log to console | **Not tested** (JS, no pytest coverage) |
  | 4 | `aggregate_ops_metrics.py` when `logs/` missing — write seed JSON | **Not tested** (script not in scope for this QA pass) |
  | 5 | `generate_alerts.py` when `metrics-summary.json` does not exist — write `alerts: []` + warning | **Tested** (`test_missing_metrics_summary_writes_empty_alerts`, `test_missing_metrics_summary_read_json_returns_none`) |
  | 6 | `client-error` endpoint receives oversized message > 2000 chars — should return 422 | **Tested / xfail** — `test_oversized_message_returns_422` is marked `xfail` because `ClientErrorPayload.message` has no `max_length=2000` constraint in the current implementation. Schema tightening required. |
  | 7 | `crypto.randomUUID()` unavailable in mobile WebView — fallback | **Not tested** (JS, no pytest coverage) |
  | 8 | `configure_logging()` called more than once — idempotent | **Tested** (`test_configure_logging_idempotent`) |
  | 9 | `alert-history.jsonl` rotation when > 50 MB or 90 days | **Not tested** (rotation logic not implemented yet per implementation log) |
  | 10 | Race condition: aggregator writing while dashboard reads `metrics-summary.json` | **Not tested** (atomic-rename logic not in scope for unit tests) |

- **Outstanding finding:** `ClientErrorPayload` in `client_errors.py` does not enforce `max_length=2000` on `message` or `max_length=8000` on `stack` as specified in the Architect's API contract. The xfail test documents this gap; the schema should be tightened before production release.

---

## [TechWriter] Documentation

- **Confluence page updated:** https://ravionics.atlassian.net/wiki/spaces/RIIAProjec/pages/76611602/Engineering
- **Page section modified:** API Inventory — System CRUD table (new `/api/v1/client-error` row added); new structured observability paragraph inserted above the Workflow section; version date confirmed 2026-05-11. Page bumped from v4 → v5.
- **Spec file confirmed current:**
  - `Spec_RITA_App.md` — updated: `/api/v1/client-error` row added to the System Tier table (was missing).
  - `Spec_JS_Code.md` — updated: `apiFetch()` wrapper note added to Section 8 (API Communication Pattern), documenting `SESSION_TRACE_ID`, `X-Request-ID` header, and fallback for WebViews across all three dashboards and Mobile PWA (was missing).
- **Task brief archived:** yes
- **TechWriter DoD checklist:**
  - [x] Confluence Engineering page updated with new endpoint and observability notes
  - [x] `Spec_RITA_App.md` System Tier table contains `/api/v1/client-error`
  - [x] `Spec_JS_Code.md` Section 8 documents `apiFetch()` wrapper
  - [x] Run log written to `riia-ai-org/agent-ops/runs/run-20260508-improve-observability.json`
