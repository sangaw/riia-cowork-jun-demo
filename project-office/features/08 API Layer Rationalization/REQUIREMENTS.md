# Feature 08 — API Layer Rationalization

**Status:** Requirements Draft  
**Date:** 2026-05-17  
**Owner:** San G  
**Approach:** /enhance multi-agent orchestration

---

## 1. Problem Statement

RITA has three defined API tiers (ADR-001):
- **Experience Layer** — `/api/v1/experience/` — aggregates, formats, client-ready
- **Orchestration/Workflow Layer** — `/api/v1/workflow/` or business process routes — multi-step operations
- **System/Data Layer** — `/api/v1/system/` or single-table CRUD routes — raw DB access

Current state has **8 direct violations** where dashboard JS bypasses the experience layer and calls system-tier routes directly. Additionally, 4 route definitions are missing or path-mismatched, and 6 data sources are fetched redundantly (2–3x per load cycle with no caching).

**Overall compliance score: 82%** — acceptable for POC, must be 100% before production.

---

## 2. Scope

All client surfaces:
- RITA main dashboard (`dashboard/js/rita/`)
- FnO dashboard (`dashboard/js/fno/`)
- Ops dashboard (`dashboard/js/ops/`)
- Mobile PWA (`rita-build-portfolio/android-mobile-app/index.html`)
- Invest-Game (`dashboard/js/invest-game/`)

All API tiers:
- `src/rita/api/experience/`
- `src/rita/api/v1/workflow/` and business-process routes
- `src/rita/api/v1/system/` (read-only access for internal use)
- `src/rita/api/` (portfolio, chat, MCP)

---

## 3. Findings

### 3.1 Architecture Compliance Summary

| Component | Finding | Status |
|---|---|---|
| Experience tier — read-only | All 23 experience endpoints are read-only (no commits) | ✅ PASS |
| System tier — pure CRUD | All 18 system endpoints are single-table CRUD | ✅ PASS |
| Workflow tier — service layer | All 13 workflow endpoints use service layer, no direct repo access | ✅ PASS |
| Dashboard calls experience tier | 24 of 32 dashboard API calls use experience or workflow tiers | ⚠️ PARTIAL |
| Dashboard avoids system tier | 8 violations — dashboard calls system tier directly | ❌ FAIL |
| Mobile PWA compliance | 4 of 6 mobile calls correct; 2 will be fixed when experience endpoints added | ✅ PASS |
| No missing endpoints | 2 missing routes + 2 path mismatches found | ❌ FAIL |
| No redundant multi-file calls | 6 data sources fetched 2–3x per cycle with no caching | ⚠️ PARTIAL |
| Router registration order | Correct order: system → workflow → experience → portfolio → chat | ✅ PASS |

---

### 3.2 Tier Violations (Dashboard Calling System Directly)

These are calls that must route through an Experience endpoint. Currently they bypass it:

| # | File | Endpoint Called | Tier | Fix |
|---|---|---|---|---|
| 1 | `dashboard/js/rita/performance.js` | `GET /api/v1/backtest-daily` | System | Create `/api/v1/experience/rita/backtest-daily` |
| 2 | `dashboard/js/rita/scenarios.js` | `GET /api/v1/backtest-daily` | System | Same as above |
| 3 | `dashboard/js/rita/diagnostics.js` | `GET /api/v1/backtest-daily` | System | Same as above |
| 4 | `dashboard/js/rita/trades.js` | `GET /api/v1/risk-timeline` | System | Create `/api/v1/experience/rita/risk-timeline` |
| 5 | `dashboard/js/rita/risk.js` | `GET /api/v1/risk-timeline` | System | Same as above |
| 6 | `dashboard/js/rita/trades.js` | `GET /api/v1/training-history` | System | Create `/api/v1/experience/rita/training-history` |
| 7 | `dashboard/js/rita/training.js` | `GET /api/v1/training-history` | System | Same as above |
| 8 | `dashboard/js/rita/audit.js` | `GET /api/v1/training-history` | System | Same as above |

**Root cause:** Three experience endpoints were never created. All violations resolve by adding 3 endpoints.

---

### 3.3 Missing Routes and Path Mismatches

| # | File | Endpoint Called | Issue | Fix |
|---|---|---|---|---|
| M1 | `dashboard/js/fno/manoeuvre.js` | `POST /api/v1/portfolio/adjust-position-action` | Route not defined in backend | Add route; write to existing `manoeuvres` table via `ManoeuvreService.record()` — no new migration needed |
| M2 | `dashboard/js/rita/audit.js` | `GET /metrics` | Dead code — `metrics` variable fetched but never used | Remove the fetch call; no backend work needed |
| M3 | `dashboard/js/ops/users.js` | `GET /users` | Path mismatch — backend expects `/api/v1/users` | Update JS to use `/api/v1/users` |
| M4 | `dashboard/js/ops/users.js` | `PUT /users/{userId}/roles` | Path mismatch — backend expects `/api/v1/users/{user_id}/roles` | Update JS; also align `userId` vs `user_id` naming |

**M1 decision (2026-05-17):** Renamed from `man-action` to `adjust-position-action` — clearer intent and future ML analysis. Separate concern from `man-snapshot` (snapshot = full state save; adjust-position-action = per-lot interaction audit trail). Backend: add `POST /api/v1/portfolio/adjust-position-action` to `portfolio.py`; use existing `ManoeuvreModel`/`ManoeuvreService` — the `manoeuvres` table already has the exact schema. No new DB table or migration.

**M2 decision (2026-05-17):** `audit.js` fetches `/metrics` and assigns to `metrics` variable, but `metrics` is never referenced again in the file. This is dead code from an abandoned feature. Fix: remove the `api('/metrics')` line from the `Promise.all` in `audit.js`.

---

### 3.4 Redundant API Calls (No Client-Side Caching)

These endpoints are called from multiple JS files per load cycle with no shared cache:

| Endpoint | Called From | Call Count | Impact |
|---|---|---|---|
| `/api/v1/performance-summary` | health.js, scenarios.js, trades.js, performance.js, mobile | 5 | High |
| `/api/v1/backtest-daily` | performance.js, scenarios.js, diagnostics.js | 3 | Medium |
| `/api/v1/risk-timeline` | trades.js, risk.js, mobile | 3 | Medium |
| `/api/v1/training-history` | trades.js, training.js, audit.js | 3 | Medium |
| `/api/v1/drift` | health.js, observability.js | 2 | Low |
| `/api/v1/experience/ops/step-log` | audit.js, observability.js | 2 | Low |

**Note:** `/api/v1/performance-summary` is called 5 times — highest priority for caching.

---

### 3.5 Correctly Compliant Calls (Do Not Touch)

The following are correctly routed and should not be changed:

- All invest-game calls → `/api/experience/invest-game/*` ✅
- All portfolio calls → `/api/v1/portfolio/*` ✅
- Chat and warmup → `/api/v1/chat*` ✅
- Commentary → `/api/v1/commentary` and `/api/v1/experience/rita/technical-commentary` ✅
- Geography overview → `/api/v1/experience/rita/geography-overview` ✅
- Ops metrics summary → `/api/v1/experience/ops/metrics/summary` ✅
- Market signals (raw indicators) → `/api/v1/market-signals` — system tier, acceptable for raw signals ✅
- SHAP → `/api/v1/shap` — system tier, acceptable (ML artifact access) ✅
- Pipeline and workflow operations → `/api/v1/train`, `/api/v1/backtest`, `/api/v1/pipeline`, `/api/v1/instrument/select` ✅
- MCP calls log → `/api/v1/mcp-calls` ✅
- App-root routes → `/health`, `/progress`, `/reset` ✅

---

## 4. Requirements

### R1 — Create Three Missing Experience Endpoints

**File to modify:** `src/rita/api/experience/rita.py`

Add three new read-only GET endpoints:

```
GET /api/v1/experience/rita/backtest-daily
  Returns: Latest backtest daily results formatted for UI (charts, phase labels)
  Source: wraps /api/v1/backtest-daily + formatting
  Consumers: performance.js, scenarios.js, diagnostics.js

GET /api/v1/experience/rita/risk-timeline
  Returns: Risk metrics (portfolio_value, allocation, MDD) per day, all phases
  Source: wraps /api/v1/risk-timeline + phase colour mapping
  Consumers: trades.js, risk.js, mobile

GET /api/v1/experience/rita/training-history
  Returns: Training run history formatted for UI (round labels, phase colours)
  Source: wraps /api/v1/training-history + label enrichment
  Consumers: trades.js, training.js, audit.js
```

Each endpoint must:
- Be read-only (no DB writes, no `db.commit`)
- Accept the same query parameters as the underlying system endpoint
- Return the same data shape plus any enrichment (labels, colours)
- Be documented in `project-office/specs/Spec_RITA_App.md`

---

### R2 — Update Dashboard JS to Use New Experience Endpoints

After R1 is implemented, update the 8 violating JS files:

| File | Old Call | New Call |
|---|---|---|
| `dashboard/js/rita/performance.js` | `/api/v1/backtest-daily` | `/api/v1/experience/rita/backtest-daily` |
| `dashboard/js/rita/scenarios.js` | `/api/v1/backtest-daily` | `/api/v1/experience/rita/backtest-daily` |
| `dashboard/js/rita/diagnostics.js` | `/api/v1/backtest-daily` | `/api/v1/experience/rita/backtest-daily` |
| `dashboard/js/rita/trades.js` | `/api/v1/risk-timeline` | `/api/v1/experience/rita/risk-timeline` |
| `dashboard/js/rita/risk.js` | `/api/v1/risk-timeline` | `/api/v1/experience/rita/risk-timeline` |
| `dashboard/js/rita/trades.js` | `/api/v1/training-history` | `/api/v1/experience/rita/training-history` |
| `dashboard/js/rita/training.js` | `/api/v1/training-history` | `/api/v1/experience/rita/training-history` |
| `dashboard/js/rita/audit.js` | `/api/v1/training-history` | `/api/v1/experience/rita/training-history` |

Mobile app (`rita-build-portfolio/android-mobile-app/index.html`):
- `fetchTimeline()` → update to `/api/v1/experience/rita/risk-timeline`
- `fetchTradeEvents()` → update to `/api/v1/experience/rita/trade-events` (if created, else leave)

---

### R3 — Resolve Missing Routes

**R3.1 — `POST /api/v1/portfolio/adjust-position-action`** _(renamed from `man-action`)_

This is a per-lot interaction audit trail: fired fire-and-forget every time a user moves a lot between manoeuvre groups. Long-term goal is ML analysis of trader behaviour patterns.

- Add `POST /api/v1/portfolio/adjust-position-action` to `src/rita/api/v1/portfolio.py`
- Use existing `ManoeuvreService.record()` — no new service code needed
- Use existing `ManoeuvreCreate` schema — all fields already match the JS payload
- No new DB table or Alembic migration — `manoeuvres` table already has exact schema: `date`, `month`, `action`, `lot_key`, `from_group`, `to_group`, `nifty_spot`, `banknifty_spot`
- Update `dashboard/js/fno/manoeuvre.js`: change URL from `/api/v1/portfolio/man-action` to `/api/v1/portfolio/adjust-position-action`

**R3.2 — `/metrics` dead code removal**

- Remove `api('/metrics').catch(() => ({}))` from the `Promise.all` in `dashboard/js/rita/audit.js` (line 10)
- Remove `metrics` from the destructuring assignment on line 7
- No backend change required — route never needs to be created

**R3.3 — `/users` path mismatch**
- Verify backend router prefix in `src/rita/api/v1/users.py` and `src/rita/main.py`
- Update `dashboard/js/ops/users.js`:
  - `/users` → `/api/v1/users`
  - `/users/{userId}/roles` → `/api/v1/users/{user_id}/roles`

---

### R4 — Client-Side Session Cache for Redundant Calls

Implement a lightweight session cache utility in a shared JS module (e.g., `dashboard/js/shared/api-cache.js`):

```js
// Session-scoped cache — cleared on page reload
const _cache = {};

export async function cachedApi(path, ttlMs = 60000) {
  const now = Date.now();
  if (_cache[path] && (now - _cache[path].ts) < ttlMs) {
    return _cache[path].data;
  }
  const data = await api(path);
  _cache[path] = { data, ts: now };
  return data;
}
```

Apply to the 5 highest-impact redundant endpoints:
- `/api/v1/performance-summary` (called 5x — TTL 120s)
- `/api/v1/experience/rita/backtest-daily` (called 3x — TTL 120s)
- `/api/v1/experience/rita/risk-timeline` (called 3x — TTL 60s)
- `/api/v1/experience/rita/training-history` (called 3x — TTL 120s)
- `/api/v1/drift` (called 2x — TTL 60s)

---

### R5 — API Monitoring Endpoints + End-of-Cycle Agent Builds Feed

Add a monitoring/observability layer so API usage is tracked durably and automatically feeds into the Agent Builds dashboard at the end of every `/enhance` run — matching how Feature 07 made token counts flow without manual seeding.

**R5.1 — Request count and latency middleware → DB-persisted**
- Add FastAPI middleware in `src/rita/main.py` that records per-endpoint:
  - Request count
  - P50/P95 latency (via `statistics.quantiles`)
  - Error rate (4xx, 5xx)
- **Store in SQLite DB table `api_call_log`** — NOT in-memory. In-memory resets on restart and cannot be read by `aggregate_metrics.py` at end-of-cycle.
- Table schema: `log_id (PK)`, `path`, `method`, `status_code`, `duration_ms`, `recorded_at`
- New Alembic migration required for `api_call_log` table
- Middleware writes one row per request (async, non-blocking — use background task)

**R5.2 — `/api/v1/experience/ops/api-metrics` endpoint**
- New read-only GET endpoint in `src/rita/api/experience/ops.py`
- Reads from `api_call_log` table and aggregates: count, p50_ms, p95_ms, error_rate per (path, method)
- Returns JSON array: `[{ path, method, count, p50_ms, p95_ms, error_rate }]`
- Consumed by Ops dashboard observability panel

**R5.3 — Ops Dashboard panel**
- Add "API Metrics" panel to `ops.html` (Ops experience layer section)
- Table view: path | method | calls | p50 | p95 | errors
- Sort by call count descending
- Filter by tier (experience / workflow / system) using path prefix

**R5.4 — End-of-cycle Agent Builds feed (automatic, no manual seeding)**
- Update `riia-ai-org/agent-ops/aggregate_metrics.py` to query `api_call_log` from `rita.db` and include a new `api_metrics` section in `metrics.json`:
  ```json
  "api_metrics": {
    "top_endpoints": [{ "path": "...", "count": N, "p95_ms": N, "error_rate": 0.0 }],
    "total_requests": N,
    "error_rate_overall": 0.0,
    "captured_at": "2026-05-17T..."
  }
  ```
- Because `aggregate_metrics.py` is already called in `/enhance` Step 7, this feed happens automatically at the end of every run — no change to `enhance.md` needed and no manual seed step.
- The Agent Builds dashboard (`ops.html` agent-builds section) will display the `api_metrics` block alongside the existing run metrics.

---

### R6 — Architecture Enforcement Rule (CLAUDE.md Update)

Add to `CLAUDE.md` (or `project-office/specs/Spec_JS_Code.md`):

```
## API Tier Routing Rules (Enforced)

Dashboard JS must call Experience or Workflow tier only:
  Allowed:  /api/v1/experience/*
  Allowed:  /api/experience/*
  Allowed:  /api/v1/chat*, /api/v1/commentary, /api/v1/instrument/*
  Allowed:  /api/v1/train, /api/v1/backtest, /api/v1/pipeline, /api/v1/goal, /api/v1/market, /api/v1/strategy
  Allowed:  /api/v1/portfolio/* (portfolio tier)
  Allowed:  /api/v1/agent-panel/*
  Allowed:  /health, /progress, /reset (app roots)
  Allowed:  /api/v1/mcp-calls (log read-only)
  Allowed:  /api/v1/market-signals (raw indicator, no experience wrapper needed)
  Allowed:  /api/v1/shap (ML artifact, no experience wrapper needed)

  NEVER:    /api/v1/backtest-daily (system tier — use experience wrapper)
  NEVER:    /api/v1/risk-timeline (system tier — use experience wrapper)
  NEVER:    /api/v1/training-history (system tier — use experience wrapper)
  NEVER:    /api/v1/drift (system tier — acceptable now; move to experience if new consumers added)

When adding a new JS module:
  1. Check if data is available in an experience endpoint
  2. If not, add the experience endpoint first
  3. Never call system tier directly from dashboard JS
```

---

## 5. Definition of Done

- [ ] R1: 3 new experience endpoints exist, return correct data, pass unit tests
- [ ] R2: All 8 violating JS files updated; mobile app updated
- [ ] R3.1: `POST /api/v1/portfolio/adjust-position-action` route live; writes to `manoeuvres` table; `manoeuvre.js` URL updated
- [ ] R3.2: Dead `/metrics` fetch removed from `audit.js`
- [ ] R3.3/R3.4: `/users` path mismatch fixed in `ops/users.js`
- [ ] R4: Session cache utility created; applied to top 5 redundant endpoints
- [ ] R5.1: `api_call_log` DB table created (Alembic migration applied); middleware writes one row per request
- [ ] R5.2: `/api/v1/experience/ops/api-metrics` endpoint live; returns aggregated data from DB
- [ ] R5.3: Ops dashboard "API Metrics" panel renders table
- [ ] R5.4: `aggregate_metrics.py` reads `api_call_log` and writes `api_metrics` block to `metrics.json`; verified by running the script and inspecting output
- [ ] R6: CLAUDE.md updated with routing rules
- [ ] Spec update: `Spec_RITA_App.md` updated with 3 new experience endpoints + `adjust-position-action` + `api-metrics`
- [ ] App starts end-to-end without errors
- [ ] No regressions in RITA, FnO, Ops, or Mobile dashboards
- [ ] Agent Builds dashboard shows `api_metrics` block after a `/enhance` run (confirmed manually)

---

## 6. Files to Touch

| File | Change |
|---|---|
| `src/rita/api/experience/rita.py` | Add 3 GET endpoints (backtest-daily, risk-timeline, training-history) |
| `src/rita/api/experience/ops.py` | Add `GET /api-metrics` endpoint; reads from `api_call_log` table |
| `src/rita/api/v1/portfolio.py` | Add `POST /adjust-position-action` route; uses existing `ManoeuvreService` |
| `src/rita/models/api_call_log.py` | New ORM model for `api_call_log` table |
| `src/rita/repositories/api_call_log.py` | New repository for `api_call_log` |
| `src/rita/main.py` | Add request-logging middleware (writes to `api_call_log` via background task) |
| `alembic/versions/{hash}_add_api_call_log.py` | New migration — creates `api_call_log` table |
| `dashboard/js/rita/performance.js` | Update backtest-daily call |
| `dashboard/js/rita/scenarios.js` | Update backtest-daily call |
| `dashboard/js/rita/diagnostics.js` | Update backtest-daily call |
| `dashboard/js/rita/trades.js` | Update risk-timeline + training-history calls |
| `dashboard/js/rita/risk.js` | Update risk-timeline call |
| `dashboard/js/rita/training.js` | Update training-history call |
| `dashboard/js/rita/audit.js` | Update training-history call; remove dead `/metrics` fetch |
| `dashboard/js/ops/users.js` | Fix path from /users to /api/v1/users |
| `dashboard/js/fno/manoeuvre.js` | Update URL to `/api/v1/portfolio/adjust-position-action` |
| `dashboard/js/shared/api-cache.js` | New file — session cache utility |
| `rita-build-portfolio/android-mobile-app/index.html` | Update risk-timeline call |
| `riia-ai-org/agent-ops/aggregate_metrics.py` | Add `api_metrics` section reading from `api_call_log` table in `rita.db` |
| `project-office/specs/Spec_RITA_App.md` | Document 3 new experience endpoints + `adjust-position-action` + `api-metrics` |
| `CLAUDE.md` | Add API routing rules |

---

## 7. Estimated Effort (for /enhance sizing)

| Step | Agent | Effort |
|---|---|---|
| PM: confirm scope and acceptance criteria | PM | 30 min |
| Architect: design 3 experience endpoints + middleware + api_call_log model | Architect | 1 hr |
| Engineer: implement R1 + R2 (endpoints + JS updates) | Engineer | 2 hr |
| Engineer: implement R3 (missing routes + dead code removal) | Engineer | 30 min |
| Engineer: implement R4 (session cache) | Engineer | 1 hr |
| Engineer: implement R5.1–R5.3 (DB model + middleware + panel) | Engineer | 2 hr |
| Engineer: implement R5.4 (aggregate_metrics.py update) | Engineer | 30 min |
| QA: unit tests for all new endpoints + contract checks | QA | 1.5 hr |
| TechWriter: update specs + CLAUDE.md + Confluence | TechWriter | 30 min |
| **Total** | | **~9.5 hrs** |

Recommended: split into two `/enhance` runs:
- **Run A:** R1 + R2 + R3 — compliance fix (tier violations + missing routes + dead code). ~4 hrs.
- **Run B:** R4 + R5 — caching + monitoring + Agent Builds feed. ~5.5 hrs.

**R5.4 constraint for Run B:** Engineer must run `aggregate_metrics.py` after implementing R5.4 and confirm the `api_metrics` key appears in `metrics.json` before marking DoD complete. This is the manual verification step that replaces a one-off seed.
