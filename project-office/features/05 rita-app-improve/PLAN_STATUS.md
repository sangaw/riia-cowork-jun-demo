# RITA App UI Improvements — Feature Plan Status
**Last updated:** 2026-05-14
**Feature brief:** `project-office/task-briefs/task-brief-20260514-1030.md`
**Run log:** `riia-ai-org/agent-ops/runs/run-20260514-1030.json`

---

## Current Status: IN PROGRESS — Architect analysis pending user confirmation

---

## /enhance Rollout

| Step | Role | Task | Status | Notes |
|---|---|---|---|---|
| Step 1 | Orchestrator | Task brief + feature folder created | `[x]` | Brief: task-brief-20260514-1030.md |
| Step 2 | PM | Sprint validation — confirm fit, flag risks, approve | `[x]` | Approved. Phase 01 + Overview ready; Phases 03/04 need Data Science app (separate brief); Phase 04 removals need QA regression |
| Step 3 | Architect | Full technical design — phased plan across all requirements | `[x]` | 5-phase plan: Phase 01 → 0 → 05 → 03 → 04. Brief: task-brief-20260514-1030.md |
| Step 4 | Engineer | Implement Phase 01 — Technical Analysis page | `[x]` | Branch: worktree-agent-afaa245ae7de4a431. Commit: daf7a72. DoD: 8/8. Ruff: passed |
| Step 5 | QA | Unit tests + regression check | `[ ]` | — |
| Step 6 | TechWriter | Confluence update + spec files confirmed | `[ ]` | — |
| Merge | Engineer | Merge worktree branch into master | `[ ]` | — |

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
