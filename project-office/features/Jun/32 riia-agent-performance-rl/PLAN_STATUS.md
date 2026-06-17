# Feature 32 — RIIA Agent Performance + RL Improvement: Plan Status

**Last updated:** 2026-06-17
**Overall status:** `[ ] Not started`
**Requirements:** `project-office/features/Jun/32 riia-agent-performance-rl/REQUIREMENTS.md`

---

## Phase Summary

| Phase | Title | Status | Blocker |
|---|---|---|---|
| Phase 1 | Agent Performance Data Model & Instrumentation | `[ ] Not started` | — |
| Phase 2 | Dashboard: RIIA Agent Performance Section | `[ ] Not started` | Phase 1 |
| Phase 3 | RL Plan Step 1 — Close Scenario → Execution Bridge | `[ ] Not started` | Phase 1 |
| Phase 4 | RL Plan Step 2 — Outcome → Strategy/Scenario Closed Loop | `[ ] Not started` | Phase 1, Phase 3 |
| Phase 5 | Validation & Rollout Gate | `[ ] Not started` | Phase 3, Phase 4 |

---

## Phase 1 — Agent Performance Data Model & Instrumentation

**Status:** `[ ] Not started`
**Agent:** Engineer (worktree)
**Effort estimate:** 4–6 hours

### Tasks

| # | Task | Status | Notes |
|---|---|---|---|
| 1.1 | Add `agent_performance` ORM model | `[ ]` | `src/rita/models/agent_performance.py` |
| 1.2 | Add repository + Pydantic schema | `[ ]` | follows `add-db-model` skill pattern |
| 1.3 | Alembic migration | `[ ]` | new table only, no data backfill needed |
| 1.4 | Add log hook in `classifier.py` for all 7 agent intents | `[ ]` | fire-and-forget, must not add latency |
| 1.5 | Wire outcome backfill from `explain_decision` / `backtest_performance` | `[ ]` | updates `outcome_status` on existing rows |

### Acceptance Gate
All 7 agents write at least one row on invocation in a manual smoke test; migration applies cleanly on a fresh DB.

---

## Phase 2 — Dashboard: RIIA Agent Performance Section

**Status:** `[ ] Not started` — blocked on Phase 1
**Agent:** Engineer (worktree)
**Effort estimate:** 4 hours

### Tasks

| # | Task | Status | Notes |
|---|---|---|---|
| 2.1 | `GET /api/experience/rita/agent-performance` endpoint | `[ ]` | experience tier, read-only |
| 2.2 | `dashboard/js/rita/agent-performance.js` module | `[ ]` | KPI cards + table, 7 agents |
| 2.3 | Register section in `rita.html` + `main.js` | `[ ]` | `sec-agent-performance` |

### Acceptance Gate
Section renders with live data for all 7 agents, no console errors, visual style matches existing RITA sections.

---

## Phase 3 — RL Plan Step 1 — Close Scenario → Execution Bridge

**Status:** `[ ] Not started` — blocked on Phase 1
**Agent:** Architect (design) → Engineer (worktree)
**Effort estimate:** 8–12 hours (training + backtest included)

### Tasks

| # | Task | Status | Notes |
|---|---|---|---|
| 3.1 | Design extended action space in `RIIATradingEnv` | `[ ]` | Architect output → design doc in `docs/` |
| 3.2 | Implement reward shaping for unhedged MDD breach | `[ ]` | pulls MDD tolerance from Financial Goal data |
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

---

## Open Questions

| # | Question | Owner | Status |
|---|---|---|---|
| Q1 | Where should `outcome_status` backfill come from for trades older than this feature's ship date? | Engineer | Open |
| Q2 | Should Sentiment Analyst's data gap (no news/FII-DII feed) be solved before or after Phase 3? | PM | Open |
| Q3 | Does Phase 4's retrain cadence need a new cron job, or can it piggyback on an existing data-refresh schedule? | Architect | Open |
