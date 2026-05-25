# Feature 15 — Ops Monitoring & Observability Consolidation — Plan Status

**Status:** COMPLETE  
**Last updated:** 2026-05-24  
**Task brief:** `project-office/task-briefs/task-brief-20260524-1659.md`

---

## Summary

Consolidate 15 Ops nav items → 10 by merging five fragmented monitoring/observability sections into two clean pages. Pure frontend restructuring — no new endpoints required.

| Target page | Absorbs |
|---|---|
| Monitoring | CI/CD (step log dedup) + Alerts + Functional KPIs strip + API Metrics detail table |
| Observability | Source Availability |

---

## Task Breakdown

### Run A — Frontend Consolidation (this session)

**Status:** COMPLETE

- [x] R1: Update `nav.js` — remove `'cicd', 'alerts', 'source-availability', 'functional-kpis', 'api-metrics'` from `SECTIONS[]`
- [x] R2: Update `main.js` — remove 5 `sectionLoaders` entries and 5 `window.*` bindings
- [x] R3: Update `monitoring.js` — add import + call to `loadApiMetrics()` at end of `loadMonitoring()`
- [x] R4: `observability.js` — no change needed; `loadSourceAvailability()` already called by DOMContentLoaded in main.js
- [x] R5: Update `ops.html` — removed 5 nav items + Observability nav group header; renamed label; embedded KPI strip + alerts + API metrics cards into `sec-monitoring`; embedded source-availability into `sec-observability`; deleted 5 standalone sections
- [x] R6: Update `Spec_JS_Code.md` — removed `cicd.js` row; updated descriptions for monitoring, observability, api-metrics, alerts, source-availability, functional-kpis rows
- [x] R7: Update `Spec_RITA_App.md` — noted consolidation in ops section

**Branch:** `worktree-agent-ae044539da526fac0`  
**Commit:** `d20cc4f`

---

## Key Decisions

| Decision | Choice | Reason |
|---|---|---|
| Move vs delete modules | Keep all JS files, only change registration + render targets | Avoids breaking imports; modules stay usable |
| Functional KPIs placement | Top of Monitoring page as header strip | Already a strip component; gives at-a-glance health before deeper stats |
| Source Availability placement | Observability page | Data source health is an observability concern, not an API monitoring concern |
| CI/CD section | Remove entirely | 100% duplicate of step log already in Monitoring |
| Static JSON files | Keep as-is | No refresh mechanism in scope |
| New endpoints | None required | All data is already served by existing endpoints |

---

## Risks

| Risk | Mitigation |
|---|---|
| Section ID mismatch after DOM move | Engineer must grep `getElementById` calls in each JS module and verify target IDs match new DOM locations |
| `SECTIONS[]` and `sectionLoaders` out of sync | Remove from both in the same commit; check nav.js and main.js together |
| CSS class errors in new DOM blocks | Use exact ops design system classes from existing panels as copy-paste source |
| `loadedSections` set in nav.js | `observability` is in `liveReload` — confirm it still reloads correctly after source-availability is embedded |

---

## Blockers

None.

---

## Handoff Notes (for next session)

If this session ends before Run A is complete:

1. Read this file + `REQUIREMENTS.md` first
2. Check git log for any partial commits on the feature branch
3. Resume from the first unchecked task in Run A above
4. Do NOT re-run analysis — `REQUIREMENTS.md` has the full audit; skip straight to implementation

**Key context:** No new endpoints. No new Python files. This is a pure HTML + JS restructuring across 5 files. The analysis confirmed all endpoints are live; the problem is nav fragmentation and duplicate renders.
