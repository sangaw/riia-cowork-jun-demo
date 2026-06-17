# Feature 31 — RITA Concepts: Investment Workflow & Agents Section: Plan Status

**Last updated:** 2026-06-17
**Overall status:** `[~] In progress` — Phase 1 build complete, pending Code Review + QA
**Requirements:** `project-office/features/Jun/31 rita-concepts-investment-workflow-section/REQUIREMENTS.md`

---

## Phase Summary

| Phase | Title | Status | Blocker |
|---|---|---|---|
| Phase 1 | Frontend build — narrative + 8 agent tabs | `[x] Complete (build)` | — |
| Phase 2 | Code Review + QA + smoke test | `[ ] Not started` | Phase 1 review |

---

## Phase 1 — Frontend Build (narrative + tabbed agents)

**Status:** `[x] Complete` — implemented by Engineer Agent (run 20260617-1045)
**Agent:** engineer
**Effort estimate:** 3 hours

### Tasks

| # | Task | Status | Notes |
|---|---|---|---|
| 1.1 | Port `concept-*` CSS from `ds.html` into `rita.html` `<style>` | `[x]` | Active-tab accent uses `--run` (RITA has no `--ds` var) |
| 1.2 | Add narrative intro + 8-step workflow table + RIIA copy + 4 ML bullets (verbatim) to `#sec-learnings` after Card 6 | `[x]` | Inserted via Grep → targeted Edit |
| 1.3 | Add `concept-tab-bar` (8 buttons) + 8 `concept-panel` divs (`aw-a1`…`aw-a8`) with charts | `[x]` | Canvases `aw-a1-c1`…`aw-a8-c1` + `aw-a4-c2` |
| 1.4 | Extend `learnings.js`: `switchAgentTab`, `_noData`, 8 render helpers, `loadAgentWorkflow` (Promise.allSettled over 5 endpoints) | `[x]` | Reuses `api`/`mkChart`/`C` |
| 1.5 | Wire `main.js`: import + `window.switchAgentTab` | `[x]` | Loader `learnings` already registered |
| 1.6 | Update `Spec_RITA_App.md` + `Spec_JS_Code.md` | `[x]` | Sections 2 + 9 + Concepts description |
| 1.7 | `ruff check src/` | `[x]` | Passed (frontend-only no-op) |

### Acceptance Gate
All charts reuse existing endpoints (no new path); one tab failure does not break the page (`Promise.allSettled` + `_noData`); `switchAgentTab` on `window.*`. — Met.

---

## Phase 2 — Code Review + QA + Smoke Test

**Status:** `[ ] Not started` — blocked on Phase 1 review
**Agent:** reviewer → qa
**Effort estimate:** 1 hour

### Tasks

| # | Task | Status | Notes |
|---|---|---|---|
| 2.1 | Code Review against Architect design | `[ ]` | |
| 2.2 | Browser smoke test — no console SyntaxError; tabs switch; charts render or show `_noData` | `[ ]` | |

### Acceptance Gate
Page loads with no JS console errors; all 8 tabs switch and render (or show no-data placeholder) without breaking Cards 1–6.

---

## Session Log

| Date | Session | Work Done |
|---|---|---|
| 2026-06-17 | Initial | Requirements written; PLAN_STATUS created |
| 2026-06-17 | Engineer (20260617-1045) | Phase 1 frontend build complete: rita.html section + learnings.js + main.js + both specs; ruff clean; committed to feature branch |

---

## Open Questions

| # | Question | Owner | Status |
|---|---|---|---|
| Q1 | Should the agent tabs be instrument-aware (follow the active instrument) rather than hardcoded NIFTY? | PM / user | Open — current build uses NIFTY default per Architect contract |
