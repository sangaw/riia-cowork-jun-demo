# Feature 32 — RIIA Investment-Workflow Agent Performance Tracking + RL Improvement Plan

**Created:** 2026-06-17
**Owner:** PM / Architect
**Status:** `[ ] Not started`
**Guardrail refs:** org · architect-role · rita-project
**Affected specs:** Spec-Agent-Workflow.md, Spec_RITA_App.md, Spec_DB.md, Spec_JS_Code.md
**Affected skills:** skill-add-rita-feature.md, skill-add-db-model.md

---

## Objective

Track the performance of the 7 RIIA investment-workflow agents (Financial Goal, Sentiment
Analyst, Technical Analyst, Strategy Analyst, Scenario Analyst, Execution Analyst, Outcome
Analyst) the same way the Ops "Agent Builds" page tracks `/enhance` pipeline agents — and lay
out a phased plan to evolve these agents from independent rule-based heuristics into
components trained/refined with reinforcement learning, closing the gaps already documented
in `Spec-Agent-Workflow.md`.

This is **not** the same system as Agent Builds. Agent Builds measures the software-delivery
pipeline (PM/Architect/Engineer/QA/TechWriter). This feature measures the **trading decision**
pipeline — the agents a retail user actually relies on for Risk/Reward decisions.

---

## Background

A professionally run investment firm runs a 7-step workflow (Initiation → Research ×3 → Design
→ Evaluation → Execution → Feedback) before taking a hedged position. RITA already implements a
version of each step as a chat intent + backend function (see table below), but:

- Each agent is an isolated rule-based function — no shared learning signal between them.
- `Spec-Agent-Workflow.md` (current state, read 2026-06-17) documents specific gaps per agent:
  - **Financial Goal:** goal target is captured but never enforced as a constraint on Strategy.
  - **Sentiment Analyst:** technicals-only proxy — no news/FII-DII flow/earnings calendar.
  - **Strategy Analyst:** one allocator for all 4 strategy intents — no real Value/Momentum/
    Long-Term split.
  - **Scenario Analyst:** flags MDD breach (`breach_note: YES`) but nothing downstream acts on it.
  - **Execution Analyst:** zero chat coverage; FnO trades are still CSV-imported manually.
  - **Outcome Analyst:** read-only reporting — no closed loop back to Strategy/Scenario tuning.
- Real RL infra already exists and works: `RIIATradingEnv` (`core/trading_env.py`), Double DQN
  training via `core/ml_dispatch.py`, persisted runs via `core/training_tracker.py` /
  `repositories/training.py`, model checkpoints under `models/<INSTRUMENT>/pipeline-*.zip`.
  Today this trains **one** trading-decision model — none of the 7 named agents has its own
  measurable contribution to the trained reward.

The intent of this feature: instrument what each agent actually does today (so we can measure
it), then use that instrumentation to decide which agents are worth converting into
RL-trained components vs. which stay rule-based with better data inputs.

---

## Scope

### In Scope
- New data model + dashboard section to measure per-agent performance (chat coverage,
  decision-accuracy proxy, gap status, contribution to trade outcome) — separate from Agent Builds.
- A phased plan (this document + PLAN_STATUS.md) for using RL to close the documented gaps,
  starting with the highest-value, lowest-risk one (Scenario → Execution bridge) and ending with
  a full closed feedback loop (Outcome → Strategy/Scenario retraining).
- Reuse of existing `RIIATradingEnv` / Double DQN infra — extend, do not replace.

### Out of Scope
- Training and deploying a new RL model in this round — Phase 1–2 are instrumentation and
  design only. Model training/deploy is Phase 3+ and requires separate sign-off per phase.
- Rebuilding the Agent Builds (`/enhance` pipeline) system — that system is unaffected.
- Adding live brokerage order execution — Execution Analyst RL output stays a recommendation
  until a human approves, per existing FnO workflow.

---

## Current State — Per-Agent Status (from Spec-Agent-Workflow.md)

| Agent | Status | Chat Intents | Backend Function | RL-readiness |
|---|---|---|---|---|
| Financial Goal | Covered, not enforced | `return_1y/3y/5y` etc. | `get_period_return_estimates()` | Low — feeds env as a target constraint only |
| Sentiment Analyst | Proxy only | `market_sentiment` | `get_sentiment_score()` | Medium — needs richer input data first |
| Technical Analyst | Well covered | `rsi_reading`, `volatility_check` | `get_market_summary()` | High — already numeric, easy reward feature |
| Strategy Analyst | Single allocator | `invest_now`, `allocation_level` | `get_allocation_recommendation()` | High — natural RL policy output (allocation %) |
| Scenario Analyst | Covered, no downstream action | `stress_crash_10/20` | `simulate_stress_scenarios()` | High — natural RL action trigger |
| Execution Analyst | **Gap — no chat, no automation** | none | FnO CSV import only | High — this is the action space extension target |
| Outcome Analyst | Read-only | `backtest_performance`, `explain_decision` | `_load_perf_summary()` | High — natural reward signal source |

---

## Phases

### Phase 1 — Agent Performance Data Model & Instrumentation

**Goal:** Capture, per chat/API invocation, which of the 7 agents handled it and whether the
recommendation matched the subsequent market outcome — without changing any agent's logic yet.

| Deliverable | Description |
|---|---|
| `src/rita/models/agent_performance.py` | New ORM model — `agent_name`, `intent`, `recommendation`, `outcome_status`, `created_at`, links to existing `training_runs` where applicable |
| `src/rita/repositories/agent_performance.py` | Repository class extending `SqlRepository` |
| `src/rita/schemas/agent_performance.py` | Pydantic response schema |
| Alembic migration | New `agent_performance` table |
| Instrumentation hook in `core/classifier.py` | One-line log call after each of the 7 agent intents resolves — writes outcome later via Outcome Analyst intents |

**Acceptance Criteria:**
- [ ] Every one of the 7 agents' intents writes one `agent_performance` row per invocation
- [ ] `outcome_status` is backfillable from `explain_decision` / `backtest_performance` calls
- [ ] No change to existing chat response content or latency (instrumentation is fire-and-forget)
- [ ] Alembic migration applies cleanly on a fresh DB

---

### Phase 2 — Dashboard: RIIA Agent Performance Section

**Goal:** Surface per-agent KPIs on a new dashboard section, modeled visually on the existing
Agent Builds page but reading from `agent_performance`, not `agent_builds`.

| Deliverable | Description |
|---|---|
| `GET /api/experience/rita/agent-performance` | Experience-tier endpoint — per-agent KPI summary |
| `dashboard/js/rita/agent-performance.js` | New module — KPI cards + per-agent table |
| `rita.html` section `sec-agent-performance` | New section, registered in `dashboard/js/rita/main.js` |

**KPI cards (one per agent):** invocation count (30d), gap status (from table above, static for
now), outcome-match rate (where backfilled), trend vs prior 30d.

**Acceptance Criteria:**
- [ ] All 7 agents shown with live invocation counts from `agent_performance`
- [ ] Outcome-match rate shows `—` (not 0%) when no backfilled outcomes exist yet
- [ ] No JS console errors; visual style matches existing RITA dashboard sections

---

### Phase 3 — RL Plan Step 1: Close Scenario → Execution Bridge

**Goal:** Use the existing `RIIATradingEnv` action space to let the trained policy itself
decide when an MDD breach should produce a hedge recommendation, instead of a static threshold
check in `performance.py`.

| Deliverable | Description |
|---|---|
| `core/trading_env.py` — extended action space | Add a discrete "suggest hedge" action conditioned on portfolio MDD state feature |
| Reward shaping | Penalize unhedged drawdown beyond the user's stated MDD tolerance (pulled from Financial Goal, Phase 1 data) more heavily than before |
| New `execution_analyst` chat intent | Surfaces the policy's hedge suggestion as a recommendation (human-approved, not auto-executed) |
| Backtest comparison | Old static-threshold behavior vs new RL-suggested hedge, on historical data only |

**Acceptance Criteria:**
- [ ] Backtest shows RL-suggested hedge timing is no worse than static threshold on historical MDD events
- [ ] New chat intent returns a recommendation, never places a live order
- [ ] Training run logged via existing `training_tracker.py` — no new tracking system built

---

### Phase 4 — RL Plan Step 2: Outcome → Strategy/Scenario Closed Loop

**Goal:** Feed realized trade outcomes (from Phase 1 `agent_performance.outcome_status`) back
into the Double DQN reward function so Strategy/Scenario behavior adapts over time, not just
at initial training.

| Deliverable | Description |
|---|---|
| `core/ml_dispatch.py` — periodic retrain trigger | Scheduled retrain using accumulated outcome data, reusing existing training job pattern |
| Reward function update | Incorporate `agent_performance` outcome-match rate as a secondary reward term |
| Spec/ADR update | Document the closed loop as an explicit decision (new ADR-006 candidate) |

**Acceptance Criteria:**
- [ ] Retrain job runs on existing schedule infra (no new scheduler built)
- [ ] Reward function change is backtested against held-out data before any production model swap
- [ ] Model swap requires explicit human approval — never auto-promoted

---

### Phase 5 — Validation & Rollout Gate

**Goal:** Confirm Phases 3–4 improve outcomes before any production deploy.

| Deliverable | Description |
|---|---|
| Comparison report | Rule-based vs RL-augmented agents, side by side, on the same historical window |
| Go/no-go checklist | Human sign-off gate before `aws-production-deploy` skill is invoked for this feature |

**Acceptance Criteria:**
- [ ] Report shows RL-augmented agents do not regress Sharpe/MDD vs current rule-based baseline
- [ ] Explicit user approval recorded before deploy

---

## Dependencies

| Phase | Depends on |
|---|---|
| Phase 2 | Phase 1 (data must exist before it can be displayed) |
| Phase 3 | Phase 1 (needs Financial Goal MDD tolerance data) |
| Phase 4 | Phase 1 + Phase 3 (needs outcome data and the new action space) |
| Phase 5 | Phase 3 + Phase 4 |

---

## Key Design Decisions

| Decision | Reason |
|---|---|
| Separate data model from `agent_builds` | Agent Builds measures the dev pipeline; this measures trading agents — different lifecycle, different audience (trader vs engineer) |
| Reuse `RIIATradingEnv` instead of building per-agent RL environments | One trained policy already exists and works; adding 7 separate RL agents would fragment the reward signal and multiply maintenance cost |
| Execution stays recommendation-only through Phase 4 | No live brokerage integration exists; auto-execution is a separate, much larger risk decision requiring its own sign-off |
| Model retrain/promotion always human-gated | Matches existing project pattern — no model is auto-promoted to production without explicit approval (see Phase 5) |

---

## Open Questions

| # | Question | Owner | Status |
|---|---|---|---|
| Q1 | Where should `outcome_status` backfill come from for trades older than this feature's ship date? | Engineer | Open |
| Q2 | Should Sentiment Analyst's data gap (no news/FII-DII feed) be solved before or after Phase 3? | PM | Open |
| Q3 | Does Phase 4's retrain cadence need a new cron job, or can it piggyback on an existing data-refresh schedule? | Architect | Open |

---

## Definition of Done

- [ ] Phase 1 + Phase 2 complete with acceptance criteria checked (instrumentation + dashboard)
- [ ] Phase 3 backtest report reviewed and approved before any chat-facing change ships
- [ ] Phase 4 only started after Phase 3 is in production and stable for at least one full review cycle
- [ ] `Spec-Agent-Workflow.md` updated to reflect closed gaps as each phase ships
- [ ] `Spec_DB.md` updated with new `agent_performance` table
- [ ] Session committed to git
