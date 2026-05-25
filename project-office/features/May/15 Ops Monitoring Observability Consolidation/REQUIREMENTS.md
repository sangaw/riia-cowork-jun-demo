# Feature 15 — Ops Monitoring & Observability Consolidation

**Status:** Requirements Complete  
**Date:** 2026-05-24  
**Owner:** San G  
**Approach:** /enhance multi-agent orchestration (analysis → implementation)

---

## 1. Problem Statement

The Ops dashboard nav has **15 items** but the monitoring domain is fragmented across 5 separate nav entries with overlapping content. Users cannot find related information and cannot tell the difference between "API & Metrics" and "API Metrics" or between "Monitoring" and "CI/CD".

Three confirmed duplicates exist:

| Duplicate | Item A | Item B |
|---|---|---|
| Step log data | "API & Metrics" → `#mon-steplog` | "CI/CD" → `#cicd-steplog` |
| API telemetry | "API & Metrics" summary stats | "API Metrics" per-endpoint table |
| Alert data | Inline alert widget in Monitoring | Separate "Alerts" nav item |

Target state: **10 nav items** with two clearly scoped pages replacing five fragmented ones.

---

## 2. Scope

**Primary target:** `dashboard/ops.html`, `dashboard/js/ops/`

**Sections affected:**
- `sec-monitoring` (rename + expand)
- `sec-observability` (expand)
- `sec-cicd` (remove — absorb into Monitoring)
- `sec-alerts` (remove — absorb into Monitoring)
- `sec-source-availability` (remove — absorb into Observability)
- `sec-functional-kpis` (remove — absorb into Monitoring as header strip)
- `sec-api-metrics` (remove — merge into Monitoring)

**No backend changes required.** All existing endpoints are live and correctly wired.

---

## 3. Current State Audit

### 3.1 Section Inventory

| Nav Label | Section ID | Endpoint(s) | Status |
|---|---|---|---|
| API & Metrics | `sec-monitoring` | `/api/experience/ops/metrics/summary`, `/api/experience/ops/step-log` | Live |
| CI/CD | `sec-cicd` | `/api/experience/ops/step-log` | **Duplicate of Monitoring step log** |
| Observability | `sec-observability` | `/api/v1/drift`, `/api/v1/mcp-calls`, `/health` | Live |
| Alerts | `sec-alerts` | `/ops/alerts/active-alerts.json` (static) | Live — data from 2026-05-08 |
| Source Availability | `sec-source-availability` | `/ops/metrics/source-availability.json` (static) | Live — 6 sources |
| Functional KPIs | `sec-functional-kpis` | `/api/experience/ops/functional-kpis` | Live |
| API Metrics | `sec-api-metrics` | `/api/experience/ops/api-metrics` | Live |

### 3.2 Duplicate Details

**Duplicate 1 — Step Log (exact duplicate):**
- `monitoring.js` renders `#mon-steplog` from `/api/experience/ops/step-log`
- `cicd.js` renders `#cicd-steplog` from the same `/api/experience/ops/step-log`
- Identical endpoint, identical table columns (Step, Name, Status, Duration, Ended)

**Duplicate 2 — API metrics (split view):**
- `monitoring.js` shows summary stats (total requests, error count, avg latency, top endpoint) via `metrics/summary.api_requests`
- `api-metrics.js` shows filterable per-endpoint detail (p50, p95, error rate) via `api-metrics`
- Same domain, should be one unified panel with summary + detail table

**Duplicate 3 — Alerts (two sources):**
- `monitoring.js` derives runtime alerts from metrics data (error rate > 5%, failed steps count)
- `alerts.js` loads the static `active-alerts.json` with labelled rules and components
- These complement each other but are surfaced as two unrelated nav items

### 3.3 Nav Label Mismatch

The `monitoring` nav item (line 331 of ops.html) displays `"API & Metrics"` via `data-i18n="nav.monitoring"`, but the section header badge reads `"Monitoring"`. The separate `api-metrics` nav item is also labelled `"API Metrics"`. Two items with near-identical names point to two different sections — this is the primary user confusion point.

---

## 4. Target Design

### 4.1 Monitoring Page (renamed from "API & Metrics")

**Nav label:** Monitoring  
**Section ID:** `sec-monitoring` (keep existing, update contents)  
**Badge:** `sense` colour (existing)

Widgets in order:
1. **Functional KPI strip** — training success, chat low-confidence, experience errors, API error rate, P95 latency (moved from standalone section; target `#functional-kpis-container`)
2. **API summary cards** — total requests, error count, avg latency, top endpoint (existing `#mon-total`, `#mon-errors`, `#mon-ips`, `#mon-top-ep`)
3. **Active Alerts** — table from `active-alerts.json` with critical/warning badges (moved from `sec-alerts`; target `#mon-alerts-table`)
4. **API endpoint detail table** — filterable per-endpoint breakdown (moved from `sec-api-metrics`; target `#mon-api-detail`)
5. **Step timing bars** — existing `#mon-timing`
6. **Pipeline step log** — last 20 entries, existing `#mon-steplog`
7. **Pipeline utilities** — Run Goal, Run Market, Run Strategy, Run Full Pipeline, Reset (existing)

**JS changes:**
- `monitoring.js` — add calls to `loadAlerts()`, `loadApiMetrics()`, `loadFunctionalKPIs()` internally; render their widgets inside `sec-monitoring` DOM
- `alerts.js`, `api-metrics.js`, `functional-kpis.js` — keep modules unchanged; their render targets move into `sec-monitoring` HTML
- Remove `sectionLoaders['cicd']`, `sectionLoaders['alerts']`, `sectionLoaders['functional-kpis']`, `sectionLoaders['api-metrics']` from `main.js`

### 4.2 Observability Page (expand scope)

**Nav label:** Observability  
**Section ID:** `sec-observability` (keep existing, add widgets)  
**Badge:** `data` colour (existing)

Widgets in order:
1. **Drift detection report** — 5-check grid (existing `#drift-checks`, `#drift-alerts`)
2. **Data Freshness** — existing `#freshness-content`
3. **Sharpe Trend** — existing `#sharpe-trend`
4. **Source Availability** — stacked bars per data source (moved from `sec-source-availability`; target `#obs-source-availability`)
5. **MCP Call Audit Log** — existing `#obs-mcp`

**JS changes:**
- `observability.js` — add call to `loadSourceAvailability()` internally; render its widget inside `sec-observability` DOM
- `source-availability.js` — keep module unchanged; render target moves into `sec-observability` HTML
- Remove `sectionLoaders['source-availability']` from `main.js`

### 4.3 Nav Changes

Remove from `SECTIONS[]` in `nav.js`:
```
'cicd', 'alerts', 'source-availability', 'functional-kpis', 'api-metrics'
```

Remove corresponding nav items from `ops.html`:
- `<div class="ni n-cicd" ...>`
- `<div class="ni n-alerts" ...>`
- `<div class="ni n-source-availability" ...>`
- `<div class="ni n-functional-kpis" ...>`
- `<div class="ni n-api-metrics" ...>`

Update remaining nav label:
- Change `data-i18n="nav.monitoring"` display text from `"API &amp; Metrics"` to `"Monitoring"`

Update i18n file if translations exist for `nav.monitoring`.

---

## 5. Files to Touch

| File | Change |
|---|---|
| `dashboard/ops.html` | (1) Remove 5 nav `<div class="ni">` elements; (2) Update monitoring nav label; (3) Move alert table, KPI strip, API detail table DOM into `sec-monitoring`; (4) Move source-availability chart DOM into `sec-observability`; (5) Remove standalone sections `sec-cicd`, `sec-alerts`, `sec-source-availability`, `sec-functional-kpis`, `sec-api-metrics` |
| `dashboard/js/ops/nav.js` | Remove `'cicd', 'alerts', 'source-availability', 'functional-kpis', 'api-metrics'` from `SECTIONS[]` |
| `dashboard/js/ops/main.js` | Remove 5 `sectionLoaders[...]` entries and their imports; remove 5 `window.*` bindings for removed sections |
| `dashboard/js/ops/monitoring.js` | Add internal calls to `loadAlerts()` and `loadApiMetrics()` and `loadFunctionalKPIs()`; import those functions |
| `dashboard/js/ops/observability.js` | Add internal call to `loadSourceAvailability()`; import that function |
| `project-office/specs/Spec_JS_Code.md` | Update ops module structure table to reflect removed modules and consolidated loaders |
| `project-office/specs/Spec_RITA_App.md` | Note consolidation in ops section; no endpoint changes |

---

## 6. Out of Scope

- No new API endpoints
- No changes to `alerts.js`, `api-metrics.js`, `functional-kpis.js`, `source-availability.js` — these modules stay; only their registration in `main.js` and their DOM targets in `ops.html` move
- No changes to any other dashboard (RITA, FnO, Mobile PWA)
- Static JSON files (`active-alerts.json`, `source-availability.json`) are kept as-is — no automated refresh mechanism in this feature

---

## 7. Definition of Done

- [ ] Nav reduced from 15 to 10 items
- [ ] No duplicate step log renders (CI/CD section gone)
- [ ] "Monitoring" and "API Metrics" nav labels consolidated to one "Monitoring" item
- [ ] Functional KPI strip visible at top of Monitoring page
- [ ] Active alerts table visible inside Monitoring page
- [ ] API endpoint detail table visible inside Monitoring page
- [ ] Source Availability visible inside Observability page
- [ ] `ruff check src/` passes (no Python changes expected; confirm)
- [ ] `SECTIONS[]` in `nav.js` matches visible nav items in `ops.html`
- [ ] Spec files updated
