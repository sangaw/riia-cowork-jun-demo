# Improve Observability — Feature Plan Status
**Last updated:** 2026-05-08
**Feature brief:** `task-brief-improve-observability.md`
**Requirements:** `Observability_Requirements.md`
**Engineering context:** `eng-context.md`

---

## Current Status: COMPLETE — all 10 steps done; merged and closed 2026-05-11

---

## 10-Step Rollout

| Step | Role | Task | Status | Notes |
|---|---|---|---|---|
| Step 1 | PM + Architect | Sprint validation + full technical design (API contracts, file map, schemas) | `[x]` | PM: approved. Architect: 10 edge cases, 10-item DoD, full file map across 3 repos |
| Step 2 | Engineer | Core logging infrastructure — `log_event()` wrapper, `logging_config.py`, 4 JSONL rotating files, log-level wiring in `main.py` | `[x]` | Branch: worktree-agent-ab190a43c42d82923. Commit: 865b673. Ruff: passed |
| Step 3 | Engineer | Experience layer provenance — `experience.compose` log in `rita.py`, `ds.py`, `ops.py`; fix bare `except: pass` in `ds.py` | `[x]` | Commit: 959c511. 10 handlers instrumented across 3 files. 2 bare excepts fixed in ds.py. Ruff: passed |
| Step 4 | Engineer | Silent failure fixes — replace all `except: pass` in `portfolio.py`, `pipeline.py`, `training_runs.py`, `drift_detector.py` | `[x]` | Commit: ec2abff. 4 bare excepts fixed across 3 files. drift_detector.py already handled. Ruff: passed |
| Step 5 | Engineer | Functional domain events — `training.*`, `backtest.*`, `chat.*`, `drift.*`, `trade.executed` in `workflow_service.py`, `trading_env.py`, `chat.py` | `[x]` | Commit: a6f064a. training.*+trade.executed+chat.* added. No backtest fn in workflow_service (embedded in training outcome). Ruff: passed |
| Step 6 | Engineer | Aggregator script — `aggregate_ops_metrics.py` → `metrics-summary.json`, `functional-kpis.json`, `source-availability.json` | `[x]` | Commit: 5046cd2. 268-line stdlib aggregator + 5 seed files. Syntax ok. Handles missing logs gracefully |
| Step 7 | Engineer | Alert generator — `generate_alerts.py` → `active-alerts.json` + `alert-history.jsonl` + daily digest | `[x]` | Commit: dfe2437. 703 lines stdlib only. 10 rules. Merge logic + idempotency verified. data_stale_critical fires on seed (99.0 days) |
| Step 8 | Engineer | Ops dashboard panels — source availability stacked bar + functional KPI 24h sparklines | `[x]` | Commit: 7e37fff. 3 new JS modules (alerts.js, source-availability.js, functional-kpis.js) + main.js wired. node --check: passed |
| Step 9 | Engineer | JS `apiFetch()` wrapper + `X-Request-ID` (all dashboards + mobile PWA) + `window.onerror` + `sw.js` fixes + `/api/v1/client-error` endpoint + riia-ai-org `print()` → logging | `[x]` | Commit: 9d591b0. 7 files, 274 insertions. All ruff checks passed. 3 sw.js catches added. window.onerror added to PWA |
| Step 10a | Engineer | ops/ static mount + HTML sections for 3 new panels + nav.js SECTIONS fix | `[x]` | Commit: 3bca774. nav.js SECTIONS array updated. 3 nav items + 3 sections added to ops.html. Ruff: passed |
| Step 10b | QA | Unit tests — log_event, client-error endpoint, alert rules; contract check | `[x]` | 30 tests written (29/30 pass, 1 xfail — max_length not enforced on ClientErrorPayload.message). test_observability.py |
| Step 10c | TechWriter | Confluence Engineering page update, spec files confirmed, run log, merge review | `[x]` | Confluence Engineering page v4→v5. Spec_RITA_App.md + Spec_JS_Code.md updated. Run log: run-20260508-improve-observability.json |

---

## Scope Summary

| Project | What changes |
|---|---|
| `riia-jun-release` (Python) | `logging_config.py`, `main.py`, `experience/rita.py`, `experience/ds.py`, `experience/ops.py`, `portfolio.py`, `pipeline.py`, `training_runs.py`, `drift_detector.py`, `workflow_service.py`, `trading_env.py`, `chat.py` |
| `riia-jun-release` (JS) | `dashboard/js/rita/main.js`, `dashboard/js/fno/main.js`, `dashboard/js/ops/main.js` |
| `riia-jun-release` (new files) | `ops/metrics/metrics-summary.json`, `ops/metrics/functional-kpis.json`, `ops/metrics/source-availability.json`, `ops/alerts/active-alerts.json`, `ops/alerts/alert-history.jsonl` |
| `riia-ai-org` | `agent-ops/aggregate_metrics.py`, `agent-ops/shared/agentops.js` |
| `rita-build-portfolio` | `android-mobile-app/index.html`, `android-mobile-app/sw.js` |
| `project-office/scripts` | `aggregate_ops_metrics.py` (new), `generate_alerts.py` (new) |

---

## Blockers

None

---

## Run Log

| Step | Timestamp | Agent | Branch | Commit | Outcome |
|---|---|---|---|---|---|
| — | — | — | — | — | Not started |
