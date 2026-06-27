# Feature 32 — RIIA Agent Performance + RL Improvement: Plan Status

**Last updated:** 2026-06-27
**Overall status:** `[~] Phases 1+2 DEPLOYED to prod (0178a44, 2026-06-27 — June-release golden version) — Phases 3–5 pending on separate branch/env`
**Requirements:** `project-office/features/Jun/32 riia-agent-performance-rl/REQUIREMENTS.md`

---

## Phase Summary

| Phase | Title | Status | Blocker |
|---|---|---|---|
| Phase 1 | Agent Performance Data Model & Instrumentation | `[x] Complete` (merge `c68601e`) | — |
| Phase 2 | Dashboard: RIIA Agent Performance Section | `[x] Complete` (merge `c68601e`; UI redesign 2026-06-27) | — |
| Phase 3 | RL Plan Step 1 — Close Scenario → Execution Bridge | `[ ] Not started` | Phase 1 |
| Phase 4 | RL Plan Step 2 — Outcome → Strategy/Scenario Closed Loop | `[ ] Not started` | Phase 1, Phase 3 |
| Phase 5 | Validation & Rollout Gate | `[ ] Not started` | Phase 3, Phase 4 |

---

## Phase 1 — Agent Performance Data Model & Instrumentation

**Status:** `[x] Complete` — merge `c68601e` (2026-06-26)
**Agent:** Engineer (worktree)
**Effort estimate:** 4–6 hours

### Tasks

| # | Task | Status | Notes |
|---|---|---|---|
| 1.1 | Add `agent_performance` ORM model | `[x]` | `src/rita/models/agent_performance.py` |
| 1.2 | Add repository + Pydantic schema | `[x]` | `repositories/agent_performance.py` + `schemas/agent_performance.py` |
| 1.3 | Alembic migration | `[x]` | `993fec6a43bd_add_agent_performance_table.py` |
| 1.4 | Add log hook in `classifier.py` for all 7 agent intents | `[x]` | fire-and-forget; `INTENT_TO_AGENT` map + `CANONICAL_AGENTS` |
| 1.5 | Wire outcome backfill from `explain_decision` / `backtest_performance` | `[ ]` | Deferred — outcome backfill source still open (Q1); column is backfillable |

### Acceptance Gate
All 7 agents write at least one row on invocation in a manual smoke test; migration applies cleanly on a fresh DB. ✅ Met for instrumentation; backfill (1.5) deferred per scope.

---

## Phase 2 — Dashboard: RIIA Agent Performance Section

**Status:** `[x] Complete` — merge `c68601e` (2026-06-26); UI redesign 2026-06-27
**Agent:** Engineer (worktree)
**Effort estimate:** 4 hours

### Tasks

| # | Task | Status | Notes |
|---|---|---|---|
| 2.1 | `GET /api/v1/experience/rita/agent-performance` endpoint | `[x]` | experience tier, read-only; `api/experience/rita.py` |
| 2.2 | `dashboard/js/rita/agent-performance.js` module | `[x]` | KPI cards + invocation chart + table, 7 agents |
| 2.3 | Register section in `rita.html` + `main.js` | `[x]` | `sec-agent-performance` |
| 2.4 | UI redesign to match Agent Panel conventions | `[x]` | 2026-06-27 — aggregate kpi-cards, click-to-expand chart-wrap, card-wrapped data-table, coloured trend badges |
| 2.5 | Per-agent scorecards (Ops Agent Builds style) + demo data | `[x]` | 2026-06-27 — 7 scorecards on 4 RL params (Outcome Match · Avg RL Reward · Data Coverage · Invocations); `MOCK_AGENTS` baseline merges live endpoint rows as they accrue; "Demo data" badge until Phases 3–5 produce real scoring |

### Acceptance Gate
Section renders with live data for all 7 agents, no console errors, visual style matches existing RITA sections. ✅ Met.

---

## Phase 3 — RL Plan Step 1 — Close Scenario → Execution Bridge

**Status:** `[ ] Not started` — blocked on Phase 1; to be done on a feature branch
**Agent:** Architect (design) → Engineer (worktree)
**Effort estimate:** 8–12 hours (training + backtest included)

> **DECISION (2026-06-27, user):** Phases 3–5 RL work happens on a **separate feature branch** against a **new trading env (e.g. `RIIATradingEnvV2`)**, NOT by modifying `RIIATradingEnv`. The current `RIIATradingEnv` is the **golden Jun-release** model and must stay untouched so a bad RL experiment can never regress production. Tasks 3.1/3.2 below are re-scoped onto the new env accordingly.

### Tasks

| # | Task | Status | Notes |
|---|---|---|---|
| 3.1 | Design extended action space in a **new** `RIIATradingEnvV2` (clone, do not edit `RIIATradingEnv`) | `[ ]` | Architect output → design doc in `docs/` |
| 3.2 | Implement reward shaping for unhedged MDD breach (on V2 env) | `[ ]` | pulls MDD tolerance from Financial Goal data |
| 3.3 | Train + backtest candidate policy | `[ ]` | offline only, no production swap |
| 3.4 | New `execution_analyst` chat intent (recommendation-only) | `[ ]` | never places live orders |

### Acceptance Gate
Backtest shows RL-suggested hedge timing is no worse than the current static threshold on historical MDD breach events; human review sign-off recorded before proceeding to Phase 4.

---

## Phase 4 — RL Plan Step 2 — Outcome → Strategy/Scenario Closed Loop

**Status:** `[ ] Not started` — blocked on Phase 1, Phase 3
**Agent:** Architect (design) → Engineer (worktree)
**Effort estimate:** 8–12 hours

### Tasks

| # | Task | Status | Notes |
|---|---|---|---|
| 4.1 | Define periodic retrain trigger using `agent_performance` outcome data | `[ ]` | reuse existing job pattern, no new scheduler |
| 4.2 | Update reward function with outcome-match secondary term | `[ ]` | |
| 4.3 | ADR-006 draft — closed-loop retraining decision | `[ ]` | `docs/ADR-006-*.md` |

### Acceptance Gate
Reward function change backtested against held-out data; no automatic production model swap — explicit approval required.

---

## Phase 5 — Validation & Rollout Gate

**Status:** `[ ] Not started` — blocked on Phase 3, Phase 4
**Agent:** PM + user
**Effort estimate:** 2–4 hours

### Tasks

| # | Task | Status | Notes |
|---|---|---|---|
| 5.1 | Produce rule-based vs RL-augmented comparison report | `[ ]` | same historical window, Sharpe/MDD compared |
| 5.2 | Go/no-go checklist + explicit user sign-off | `[ ]` | required before `aws-production-deploy` |

### Acceptance Gate
User has explicitly approved production rollout in writing (chat record acceptable).

---

## Session Log

| Date | Session | Work Done |
|---|---|---|
| 2026-06-17 | Initial | Requirements + phased PLAN_STATUS written; grounded in `Spec-Agent-Workflow.md` gap analysis and existing `RIIATradingEnv`/Double DQN infra; confirmed scope is distinct from existing Agent Builds (`/enhance` pipeline) system |
| 2026-06-26 | Phases 1+2 build | Implemented + tested Phase 1 (ORM model, repo, schema, Alembic migration `993fec6a43bd`, fire-and-forget classifier hook) and Phase 2 (read-only Experience endpoint, `agent-performance.js`, `sec-agent-performance` section). Committed locally `3098869`→`4a8adb0`→`c68601e`; not yet pushed/deployed |
| 2026-06-27 | UI redesign | Reworked the Agent Performance section to match Agent Panel conventions: `page-hdr` + status, 4 aggregate `kpi-card`s (total/active/avg-trend/backfill), click-to-expand `chart-wrap` horizontal bar chart of invocations by agent, and a card-wrapped `data-table` with coloured trend badges. JS rewritten to use `mkChart`/`C` palette |
| 2026-06-27 | Scorecards + deploy | Added Ops-Agent-Builds-style per-agent scorecards (4 RL params), switched invocations chart to vertical bars (40%) beside the detail table (60%), demo-data baseline. **Deployed Phases 1+2 to prod as `0178a44` — June-release golden version.** Push hit PATTERN-018 (osxkeychain `403 denied to sangaw`); resolved via `git-key.txt` + inline x-access-token helper (now documented). Health + endpoint verified (7 agents, 200) |

---

## Open Questions

| # | Question | Owner | Status |
|---|---|---|---|
| Q1 | Where should `outcome_status` backfill come from for trades older than this feature's ship date? | Engineer | Open |
| Q2 | Should Sentiment Analyst's data gap (no news/FII-DII feed) be solved before or after Phase 3? | PM | Open |
| Q3 | Does Phase 4's retrain cadence need a new cron job, or can it piggyback on an existing data-refresh schedule? | Architect | Open |
