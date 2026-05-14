# RITA App UI Improvements — Feature Plan Status
**Last updated:** 2026-05-14
**Feature brief:** `project-office/task-briefs/task-brief-20260514-1030.md`
**Run log:** `riia-ai-org/agent-ops/runs/run-20260514-1030.json`

---

## Current Status: PHASE 0 COMPLETE — resume next session at Phase 05 (Learnings)

---

## /enhance Rollout

| Step | Role | Task | Status | Notes |
|---|---|---|---|---|
| Step 1 | Orchestrator | Task brief + feature folder created | `[x]` | Brief: task-brief-20260514-1030.md |
| Step 2 | PM | Sprint validation — confirm fit, flag risks, approve | `[x]` | Approved. Phase 01 + Overview ready; Phases 03/04 need Data Science app (separate brief); Phase 04 removals need QA regression |
| Step 3 | Architect | Full technical design — phased plan across all requirements | `[x]` | 5-phase plan: Phase 01 → 0 → 05 → 03 → 04. Brief: task-brief-20260514-1030.md |
| Step 4 | Engineer | Implement Phase 01 — Technical Analysis page | `[x]` | Branch: worktree-agent-afaa245ae7de4a431. Commit: daf7a72. DoD: 8/8. Ruff: passed |
| Step 5 | QA | Unit tests + contract check (Phase 01) | `[x]` | 21/21 passed. URL bug found + fixed (daf4ce6): JS path was /api/experience/ not /api/v1/experience/ |
| Step 6 | TechWriter | Confluence update + spec files confirmed (Phase 01) | `[x]` | Confluence page 76611602 updated to v9. Both specs confirmed current |
| Merge | Engineer | Merge Phase 01 worktree branch into master | `[x]` | Merge commit: c57734a. URL fix: daf4ce6 |
| Step 4b | Engineer | Implement Phase 0 — Overview geography panels | `[x]` | Branch: worktree-agent-abb1dba6f43a36671. Commit: f8c8b84. Merge: 4e1e119. DoD: 8/8. Ruff: passed |
| Step 5b | QA | Unit tests + contract check (Phase 0) | `[x]` | 25/25 passed. Contract match. Note: GeoInstrument.flag unused by JS (harmless) |

---

## Feature Scope (Multi-Phase)

### Overview Page
| Area | Change |
|---|---|
| `dashboard/rita.html` | Add 3 geography panels (US, EU, India) — 4 instruments each |
| `dashboard/js/rita/overview.js` | New module for geography instrument panels |

### Phase 01 — Technical Analysis Page (PLAN menu)
| Area | Change |
|---|---|
| `dashboard/rita.html` | New "Technical Analysis" nav item under PLAN; move AIR% + RSI-14 rows there |
| `dashboard/js/rita/technical-analysis.js` | New module: Instrument commentary (top) + Price & Volume chart |
| `project-office/specs/Spec_RITA_App.md` | Add Technical Analysis section to nav inventory |

### Phase 03 — ANALYSE Menu Reorg (follow-on brief)
| Area | Change |
|---|---|
| RITA nav | Move Model Overview above Performance |
| Data Science app | New app — Trade Journal (renamed Experiment Results) + Trade Diagnostics |

### Phase 04 — Monitor Menu (follow-on brief)
| Area | Change |
|---|---|
| Data Science app | Copy Monitor menu; add Training Progress, Observability, MCP Calls, Audit |
| RITA app | Remove Training Progress, Observability, MCP Calls, Audit (destructive — needs QA regression) |
| Ops app | Move Utilities to Ops → API & Metrics page |

### Phase 05 — Learnings (follow-on brief)
| Area | Change |
|---|---|
| `dashboard/rita.html` | New Learnings nav section with 4 sub-pages |
| Content | Technical Indicators, Model Building, Sharpe Ratio, Market Trends charts |

---

## Blockers

| Blocker | Phase | Resolution |
|---|---|---|
| Phase 04 removals are destructive | Phase 04 | QA regression coverage required before merge |

> Note: Data Science HTML app confirmed at `riia-jun-release/dashboard/ds.html` (localhost:8000/dashboard/ds.html). Phase 03/04 items can target it directly — no separate app creation needed.

---

## Decisions Log

| Date | Decision |
|---|---|
| 2026-05-14 | PM approved Phase 01 + Overview as first increment; Phases 03/04/05 are follow-on briefs |

---

## Run Log

| Step | Timestamp | Agent | Branch | Commit | Outcome |
|---|---|---|---|---|---|
| Steps 1–2 | 2026-05-14-1030 | /enhance orchestrator | — | — | PM approved |
| Step 3 | 2026-05-14 | Architect (Plan agent) | — | — | 5-phase design complete |
| Steps 3b–6 | 2026-05-14 | Engineer / QA / TechWriter | worktree-agent-afaa245ae7de4a431 | daf7a72 + daf4ce6 | Phase 01 complete. Merge: c57734a |
| Post-QA fixes | 2026-05-14 | Orchestrator (direct) | master | e0db819 + 9824ee2 + 621360b | 3 bugs fixed: incomplete row move, dangling lastCrossIdx, display:none on section |

## Next Session — Resume at Phase 0

**Next phase:** Phase 0 — Overview Page (Geography Panels)
**Architect design:** already in `project-office/task-briefs/task-brief-20260514-1030.md`
**Implementation order for Phase 0:**
1. `src/rita/schemas/geography.py` — GeoInstrument, GeoRegion, GeographyOverviewResponse
2. `src/rita/api/experience/rita.py` — GET /api/v1/experience/rita/geography-overview
3. `dashboard/rita.html` — add `div#geo-panels` inside `sec-market-signals`
4. `dashboard/js/rita/market-signals.js` — add `loadGeoPanels()`, call from `loadMarketSignals()`
5. `dashboard/js/rita/main.js` — expose `window.loadGeoPanels`

**Post-Phase 0 order:** Phase 05 (Learnings) → Phase 03 (ANALYSE reorg) → Phase 04 (Monitor removals)

**Known gaps to feed into Engineer skill file (captured in memory):**
- Engineer must move complete DOM row containers, not just individual canvas elements, when requirement says "move a row"
- Engineer must not add `style="display:none"` to new sections — use class-only visibility matching existing section pattern
