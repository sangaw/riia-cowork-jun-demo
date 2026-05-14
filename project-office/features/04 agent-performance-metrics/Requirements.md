# Agent Performance Metrics — Feature Requirements

**Feature:** AI Agent Performance Measurement & Improvement Framework
**Created:** 2026-05-11
**Decisions locked:** 2026-05-11
**Status:** Requirements Complete — ready for build
**Owner:** Project Office
**Feature folder:** `project-office/features/agent-performance-metrics/`
**Scope:** `/enhance` command pipeline only — not RITA functional AI (trading agent, chat, compliance)

---

## Design Decisions (Locked)

| # | Decision | Choice |
|---|---|---|
| D1 | Human score entry | Interactive CLI prompt at TechWriter Step 10c |
| D2 | Token tracking | Pre-run **forecasting** based on historical data + feature complexity — not cost in USD |
| D3 | Backfill | All 14 prior runs backfilled with estimated values (best-effort) |
| D4 | Dashboard placement | Inline panels on existing **Agent Builds** page — no new tab |

---

## 1. Context — What Already Exists

The AgentOps system at `riia-ai-org/agent-ops/` already captures:

| Existing Asset | What It Captures |
|---|---|
| `runs/run-{ID}.json` | Per-role: `adherence_score`, `token_estimate`, `status`, `grounding_checks[]`, `failure_modes[]` |
| `metrics.json` | Aggregates: `first_pass_rate`, `avg_adherence_score`, `avg_token_cost`, per-app pass/fail counts |
| `failure-catalog.md` | 7 failure codes (FC-001 to FC-007) with root cause + prevention rule |
| `schema.md` | JSON schema spec for run logs |
| `aggregate_metrics.py` | Script that regenerates `metrics.json` from all run files |

Observed token range from 14 runs: **15,400 – 138,800** tokens per run.
Per-role averages (from `metrics.json`): PM 7,612 · Architect 9,975 · Engineer 31,112 · QA 11,300 · TechWriter 6,650.

This feature **extends** those assets — it does not replace them.

---

## 2. Metric Taxonomy — Feasibility-Filtered

Capture method legend:
- **Auto** — computed from run log fields without human input
- **Human-scored** — interactive CLI prompt at TechWriter Step 10c
- **Derived** — computed from two or more auto/human fields
- **Out of scope** — not capturable in this context

### 2.1 Task Completion Metrics

| Metric | Capture | Formula |
|---|---|---|
| **Task Success Rate (TSR)** | Derived | `runs where overall_status == "pass"` ÷ `total_runs` |
| **First-Attempt Success Rate** | Derived | `runs where retry_count == 0 AND overall_status == "pass"` ÷ `total_runs` |
| **Partial Completion Rate** | Derived | `runs where overall_status == "pass_with_warnings"` ÷ `total_runs` |
| **Abandonment Rate** | Auto | New field `abandoned: bool` on run log |
| **Steps-to-Completion** | Derived | `SUM(steps_completed)` across all agents per run |

### 2.2 Quality Metrics

| Metric | Capture | Formula / Notes |
|---|---|---|
| **Output Accuracy** | Human-scored | 1–5; stored as `human_score.accuracy` |
| **Relevance Score** | Human-scored | 1–5; does output match stated intent? `human_score.relevance` |
| **Planning Accuracy** | Human-scored | 0/1; did PM+Architect decompose correctly on first attempt? `human_score.planning_ok` |
| **Grounding Check Pass Rate** | Auto | `checks_passed / checks_total` — already in grounding_trend |
| **Tool Call Precision** | Auto | Engineer grounding checks pass rate (proxy for correct tool use) |
| **Error Rate by Type** | Derived | Count per FC code across runs, by role |
| **Hallucination Rate** | Out of scope | No ground-truth reference available |

### 2.3 Token Forecasting (replaces cost metrics)

This is a **pre-run planning tool**, not a post-run cost tracker. Before a new /enhance run, the system estimates total and per-role token consumption based on historical data and feature complexity.

**Complexity Classification — 4 signals derived from the feature request:**

| Signal | Small (×0.7) | Medium (×1.0) | Large (×1.5) |
|---|---|---|---|
| Files to change | 1–3 | 4–8 | 9+ |
| New endpoint / DB model | No | One of these | Both |
| Frontend changes | None or labels only | New panel or section | New page or major refactor |
| Integration with existing logic | Additive only | Extends existing module | Cross-cutting or new pipeline |

Complexity score = average of 4 signal multipliers → rounds to Small / Medium / Large.

**Forecast formula per role:**

```
forecast_tokens[role] = avg_token_cost[role] × complexity_multiplier × feature_type_modifier
```

Feature type modifiers (from historical data):
- `rita` features: ×1.0 baseline
- `ops` features: ×0.6 (typically narrower scope)
- `fno` features: ×0.8
- `invest-game` features: ×1.1 (multi-file game logic)

**Output — forecast block written to run log before pipeline starts:**

```json
"token_forecast": {
  "complexity": "large",
  "complexity_score": 1.5,
  "feature_type": "rita",
  "per_role": {
    "pm": 11400,
    "architect": 14900,
    "engineer": 46700,
    "qa": 16900,
    "techwriter": 10000
  },
  "total_forecast": 99900,
  "confidence": "±40%",
  "basis_runs": 4
}
```

Confidence is `±40%` when `basis_runs < 5`, `±25%` when `basis_runs >= 5`.

**Forecast vs Actual tracking** — after run completes, `aggregate_metrics.py` computes:
- `forecast_error_pct` = `|total_tokens_estimated - total_forecast| / total_forecast × 100`
- Tracked across runs to improve the multipliers over time.

### 2.4 Efficiency Metrics

| Metric | Capture | Formula |
|---|---|---|
| **Duration (wall-clock)** | Auto | `duration_minutes` — already in run log |
| **Token Usage per Run** | Auto | `total_tokens_estimated` — already in run log |
| **Forecast vs Actual Error** | Derived | `|actual - forecast| / forecast × 100%` |
| **Retry Count** | Auto | New field `retry_count: int` — agent re-invocations within the run |
| **Agent Efficiency Index** | Derived | `grounding_score / (token_estimate / 10000)` per role — quality per 10K tokens |

### 2.5 Reliability & Robustness Metrics

| Metric | Capture | Formula |
|---|---|---|
| **Error Recovery Rate** | Auto | FC code present but `status != "fail"` → self-recovered; recoveries ÷ total FC events |
| **Graceful Degradation Rate** | Derived | `pass_with_warnings` ÷ (`pass_with_warnings` + `fail`) |
| **Tool Failure Handling** | Auto | New grounding check `tool_error_handled: bool` on Engineer |
| **Uptime/Availability** | Out of scope | Not a running service |

### 2.6 Human-in-the-Loop (HITL) Metrics

| Metric | Capture | Formula |
|---|---|---|
| **Human Intervention Count** | Auto | New array `hitl_events[]` — one entry per human correction/override |
| **Escalation Rate** | Derived | `runs with hitl_events.length > 0` ÷ `total_runs` |
| **Human Correction Rate** | Derived | `SUM(events where type == "correction")` ÷ `total_runs` |
| **Time Saved vs Manual (hours)** | Human-scored | User estimate; stored as `human_score.time_saved_hours` |
| **User Satisfaction (CSAT)** | Human-scored | 1–5 overall rating; stored as `human_score.csat` |

### 2.7 Agentic-Specific Metrics

| Metric | Capture | Formula |
|---|---|---|
| **Context Adherence Rate** | Auto | `plan_status_read + spec_reference_valid` pass rate across all runs |
| **Memory Utilization Rate** | Auto | New grounding check `memory_used: bool` on Engineer |
| **Loop Detection Rate** | Auto | New field `loop_events: int` per run |
| **Planning Accuracy** | Human-scored | (covered in 2.2) |

---

## 3. Data Model — Schema Extensions

### 3.1 New Top-Level Run Log Fields

```json
{
  "retry_count": 0,
  "abandoned": false,
  "loop_events": 0,
  "hitl_events": [
    {
      "step": "engineer",
      "type": "correction",
      "description": "User redirected agent after spec was not updated",
      "timestamp": "2026-05-08T14:32:00Z"
    }
  ],
  "token_forecast": {
    "complexity": "medium",
    "complexity_score": 1.0,
    "feature_type": "ops",
    "per_role": { "pm": 7600, "architect": 9900, "engineer": 31100, "qa": 11300, "techwriter": 6600 },
    "total_forecast": 66500,
    "confidence": "±40%",
    "basis_runs": 2
  },
  "human_score": {
    "accuracy": 4,
    "relevance": 5,
    "planning_ok": true,
    "csat": 4,
    "time_saved_hours": 3.5
  }
}
```

### 3.2 New Engineer Grounding Checks

```json
"grounding_checks": {
  "branch_created": true,
  "code_changed": true,
  "spec_updated": true,
  "ruff_passed": true,
  "contract_matches_architect": true,
  "memory_used": true,
  "tool_error_handled": true
}
```

### 3.3 Extended `metrics.json` — New Sections

```json
{
  "task_completion": {
    "tsr": 0.857,
    "first_attempt_success_rate": 0.714,
    "partial_completion_rate": 0.071,
    "abandonment_rate": 0.0
  },
  "quality": {
    "avg_accuracy_score": 4.2,
    "avg_relevance_score": 4.5,
    "avg_csat": 4.1,
    "planning_accuracy_rate": 0.875,
    "grounding_pass_rate": 0.932
  },
  "token_forecasting": {
    "avg_forecast_error_pct": 18.4,
    "by_complexity": {
      "small":  { "avg_actual": 22000, "multiplier": 0.7 },
      "medium": { "avg_actual": 31000, "multiplier": 1.0 },
      "large":  { "avg_actual": 72000, "multiplier": 1.5 }
    },
    "by_feature_type": {
      "rita":        { "run_count": 4, "avg_tokens": 66600, "modifier": 1.0 },
      "ops":         { "run_count": 2, "avg_tokens": 21800, "modifier": 0.6 },
      "fno":         { "run_count": 0, "avg_tokens": null,  "modifier": 0.8 },
      "invest-game": { "run_count": 8, "avg_tokens": 34200, "modifier": 1.1 }
    }
  },
  "efficiency": {
    "avg_duration_minutes": 87,
    "avg_tokens_per_run": 24300,
    "avg_retry_count": 0.28,
    "avg_time_saved_hours": 3.2
  },
  "reliability": {
    "error_recovery_rate": 0.75,
    "graceful_degradation_rate": 0.83,
    "loop_event_total": 0
  },
  "hitl": {
    "escalation_rate": 0.21,
    "avg_corrections_per_run": 0.35,
    "total_hitl_events": 5
  },
  "agentic": {
    "context_adherence_rate": 0.96,
    "memory_utilization_rate": 0.88,
    "loop_detection_rate": 0.0
  }
}
```

---

## 4. Data Collection — How & When

### 4.1 Auto-captured (pipeline writes to run JSON)

| Field | When written |
|---|---|
| `token_forecast` | Before PM step — computed from request text + historical averages |
| `retry_count` | Incremented each time any step is re-invoked |
| `abandoned` | Set `true` if /enhance halts before TechWriter completes |
| `loop_events` | Incremented if agent cycles on same output ≥ 3 times |
| `hitl_events[]` | TechWriter appends entry for each human redirect observed in conversation |
| `grounding_checks.memory_used` | Engineer check: did eng-context.md get read? |
| `grounding_checks.tool_error_handled` | Derived from FC flags present but status != fail |

### 4.2 Human-scored — Interactive CLI Prompt at TechWriter Step 10c

TechWriter skill updated to emit the following prompt before closing the run log:

```
=== Agent Run Complete — Please score this run ===
Output accuracy (1–5, where 5 = exactly what was needed): _
Relevance to stated intent (1–5): _
Did PM + Architect decompose the task correctly first time? (y/n): _
Overall satisfaction / CSAT (1–5): _
Estimated hours this would have taken manually: _
Press Enter to skip any field.
=========================================
```

Scores written to `human_score{}` in the run JSON. Skipped fields default to `null`.

### 4.3 Backfill — Prior 14 Runs

A `backfill_metrics.py` script populates new fields with best-effort estimates:

| Field | Backfill method |
|---|---|
| `retry_count` | `0` for all (no retries observed in prior sessions) |
| `abandoned` | `false` for all (all prior runs completed) |
| `loop_events` | `0` for all |
| `hitl_events[]` | Empty array `[]` — not reconstructable |
| `token_forecast` | Compute retrospectively using formula from actual `total_tokens_estimated` ± 0 error for calibration |
| `human_score` | `null` for all fields — user can optionally fill in retrospectively |

After backfill, `aggregate_metrics.py` is re-run to regenerate `metrics.json`.

### 4.4 Aggregation

`aggregate_metrics.py` extended to:
1. Compute all 7 new metric sections
2. Calibrate forecast multipliers from historical actual vs forecast error
3. Write updated `metrics.json`
4. Print threshold alerts to stdout (see Section 6)

Run: `python riia-ai-org/agent-ops/aggregate_metrics.py` (unchanged invocation)

---

## 5. Dashboard — Agent Builds Page Extensions

All new UI lives on the **existing Agent Builds page** in the Ops dashboard. Three new panels appended below the existing run table.

### Panel A — Performance KPI Cards (4 cards, 1 row)

| Card | Metric | Format |
|---|---|---|
| Task Success Rate | `task_completion.tsr × 100` | `85.7%` + trend arrow vs prior 5 runs |
| Avg CSAT | `quality.avg_csat` | `4.1 / 5` |
| Avg Forecast Error | `token_forecasting.avg_forecast_error_pct` | `±18%` |
| HITL Escalation Rate | `hitl.escalation_rate × 100` | `21%` |

### Panel B — Token Forecast vs Actual (per-run bar chart)

- X-axis: Run ID (last 10 runs)
- Y-axis: Tokens (thousands)
- Two bars per run: **Forecast** (grey) vs **Actual** (blue)
- Tooltip on hover: per-role breakdown of actual tokens

### Panel C — Metric Trend Lines (4 line series, one chart)

- X-axis: Run ID (all runs, chronological)
- Y-axis: Score (0–1 or 0–5, normalised)
- Lines: TSR · Grounding Pass Rate · CSAT · Context Adherence Rate
- Legend toggle to show/hide each series

### Panel D — Failure Mode Heatmap (new column on existing run table)

Extends existing per-run table with:
- New column: **FC Codes** — badges for each failure code (e.g., `FC-001 ×2`)
- New column: **HITL** — count of human intervention events
- New column: **Forecast vs Actual** — `+12%` or `-8%` in green/red

### Pre-Run Token Estimate Widget

When the user is about to describe a new feature, the Agent Builds page includes a collapsible **"Estimate Token Budget"** form:

```
Feature type: [rita | fno | ops | invest-game]
Files to change: [1-3 | 4-8 | 9+]
New endpoint or DB model: [none | one | both]
Frontend change scope: [none | panel | page]
Integration type: [additive | extends module | cross-cutting]

→ [Estimate] button → shows forecast per role + total + confidence
```

This calls `GET /api/experience/ops/token-forecast?complexity=large&feature_type=rita`
and renders the result inline without navigating away.

---

## 6. Improvement Loop — Closing the Feedback Cycle

```
Run → metrics captured → FC logged → aggregate_metrics.py flags breach → 
skill file rule updated → next run improves → forecast multiplier calibrated
```

### 6.1 Threshold Alerts — stdout from `aggregate_metrics.py`

| Condition | Alert message |
|---|---|
| Any FC code total > 3 | `[ALERT] FC-{X} has fired {N} times — review skill file rule` |
| Role `first_pass_rate < 0.70` | `[ALERT] {role} first-pass rate {N}% — grounding checks need review` |
| `avg_csat < 3.5` | `[ALERT] CSAT {N}/5 below threshold — review last 3 runs` |
| `avg_forecast_error_pct > 35` | `[ALERT] Token forecast off by {N}% on average — recalibrate multipliers` |

### 6.2 Skill Version Tracking — Extended

`skill_version_history` in `metrics.json` gains two fields per entry:

```json
{
  "skill_file": "project-office/skills/skill-add-rita-feature.md",
  "last_updated": "979df5f",
  "improvement_applied": "FC-001",
  "before_first_pass_rate": 0.5,
  "after_first_pass_rate": 0.875
}
```

---

## 7. Build Deliverables

| # | Deliverable | Type | Location |
|---|---|---|---|
| 1 | Extended `schema.md` | Docs | `riia-ai-org/agent-ops/schema.md` |
| 2 | `backfill_metrics.py` | Python | `riia-ai-org/agent-ops/backfill_metrics.py` |
| 3 | Extended `aggregate_metrics.py` | Python | `riia-ai-org/agent-ops/aggregate_metrics.py` |
| 4 | Token forecast endpoint | FastAPI | `GET /api/experience/ops/token-forecast` |
| 5 | Updated `metrics.json` | Data | `riia-ai-org/agent-ops/metrics.json` (regenerated) |
| 6 | Agent Builds page — Panel A (KPI cards) | JS + HTML | `dashboard/js/ops/agent-builds.js` |
| 7 | Agent Builds page — Panel B (forecast vs actual chart) | JS | `dashboard/js/ops/agent-builds.js` |
| 8 | Agent Builds page — Panel C (trend lines chart) | JS | `dashboard/js/ops/agent-builds.js` |
| 9 | Agent Builds page — Panel D (table columns + heatmap badges) | JS | `dashboard/js/ops/agent-builds.js` |
| 10 | Pre-run token estimate widget | HTML + JS | `dashboard/ops.html` + `agent-builds.js` |
| 11 | TechWriter skill — human score prompts | Skill file | `project-office/skills/skill-add-ops-feature.md` (+ all app skills) |
| 12 | Unit tests | Python | `tests/unit/test_agent_metrics.py` |
| 13 | Spec updates | Docs | `project-office/specs/Spec_RITA_App.md`, `Spec-Agent-Workflow.md` |

---

## 8. Definition of Done

- [x] `schema.md` shows all new fields with types and examples
- [x] All 16 existing run logs have new fields (backfill complete — backfill_metrics.py run 2026-05-12)
- [x] `aggregate_metrics.py` runs without error and produces all 7 new metric sections
- [x] `metrics.json` regenerated with new sections present and values plausible
- [x] Token forecast endpoint returns JSON with per-role breakdown (`GET /api/experience/ops/token-forecast`)
- [x] Agent Builds page renders all 4 new panels without JS errors — verified 2026-05-14
- [x] Pre-run estimate widget submits and renders forecast inline — verified 2026-05-14
- [x] TechWriter skill prompts for human scores at close (added to all 3 skill files)
- [x] Unit tests pass: 30/30 (backend endpoint, schema, complexity, confidence, contract)
- [x] Both spec files updated — Spec_RITA_App.md + Spec_JS_Code.md + Spec-Agent-Workflow.md (commit 1790af4)

**Status:** 10/10 DoD items complete. Feature closed 2026-05-14.
**Run log:** `riia-ai-org/agent-ops/runs/run-20260512-0730.json` — human_score recorded (accuracy 3, relevance 4, planning_ok false, csat 2, time_saved_hours 32.0).
**DB:** seeded via `seed_agent_builds.py` (16 runs, 80 agent rows in `rita_output/rita.db`).
