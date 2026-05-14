# Feature 0501 — Agent Builds Page: Defect Fix + Actual Token Tracking
**Last updated:** 2026-05-14
**Status:** Analysis complete — ready to implement

---

## Fixes Applied This Session

| Fix | Root Cause | Commit |
|---|---|---|
| Ops nav completely broken | `utilities.js` imported `{ api }` which doesn't exist in `ops/api.js` — fatal ES module linking error, `window.nav` never set | `8ca753d` |
| DB empty, no runs showing | `agent_build_runs` table had 0 rows — `seed_agent_builds.py` not re-run after 2 new run logs added | Re-ran seed — 18 runs now in DB |

---

## Remaining Defects (Identified 2026-05-14)

### P1 — Metric Trend Lines: 3 of 4 lines always empty

**File:** `riia-jun-release/dashboard/js/ops/agent-builds.js` — `mountTrendChart()`

**Root cause:**
`mountTrendChart` reads `overall_status`, `human_score.csat`, `plan_status_read`, and `spec_reference_valid`
off each item in `grounding_trend`. But `GroundingPoint` (the API model) only carries:
```
{ run_id, app, grounding_score, checks_passed, checks_total }
```
None of the other fields exist, so TSR, CSAT, and Context Adherence lines are always null/flat.
Only the Grounding Score line renders real data.

**Fix required:**
- API (`ops.py` `/agent-builds`): add `human_score_csat: Optional[float]` to `AgentBuildRunOut` by reading `human_score.csat` from the per-run JSON file (same place `token_forecast` and `hitl_events` are read)
- JS (`agent-builds.js`): change `mountTrendChart` to compute TSR and CSAT from `data.runs` instead of `grounding_trend` items:
  - TSR per run: `r.overall_status === 'pass' ? 1 : 0` (from `data.runs`)
  - CSAT per run: `r.human_score_csat != null ? r.human_score_csat / 5 : null`
  - Context Adherence: derive from `r.agents` — check if pm.grounding_checks.plan_status_read AND architect.grounding_checks.spec_reference_valid
  - Grounding: keep reading from `grounding_trend` (already correct)
- Schema (`agent_builds.py`): add `human_score_csat: Optional[float] = None` to `AgentBuildRunOut`

---

### P1 — Skill Version History: improvement data not shown

**File:** `riia-jun-release/src/rita/api/experience/ops.py` — `get_agent_builds()`

**Root cause:**
The endpoint builds `skill_version_history` from distinct `skill_file` names in the DB,
always with `last_updated=None`, `recent_commits=[]`, `improvement_applied=None`.
The `SkillVersion` schema already has all the right fields — they just aren't populated.
`metrics.json` has the full data: `improvement_applied`, `before/after_first_pass_rate`, `last_updated`.

**Fix required:**
- In `get_agent_builds`, after computing `skill_files` from the DB, read `metrics.json` and
  join against its `skill_version_history` array by `skill_file` name.
- Populate: `last_updated`, `improvement_applied`, `before_first_pass_rate`, `after_first_pass_rate`
- JS `renderSkillVersions`: add columns for `improvement_applied` and rate delta display.
- Also fix the `recent_commits` rendering bug: items are `{hash, message}` objects, not strings.
  Change `esc(c)` to `esc(c.hash) + ' — ' + esc(c.message)`.

---

### P2 — Token Estimate widget: result cards never populate

**File:** `riia-jun-release/dashboard/js/ops/agent-builds.js` — `submitTokenEstimate()`

**Root cause:**
`renderTokenEstimateWidget()` renders three result cards in the form grid:
`#ab-res-complexity`, `#ab-res-total`, `#ab-res-confidence`
But `submitTokenEstimate()` writes its output only to `#ab-estimate-result` (separate div).
The three grid cards remain blank after every estimate.

**Fix required:**
In `submitTokenEstimate`, after receiving `resp`, also set:
```js
document.getElementById('ab-res-complexity').innerHTML =
  `<span class="ab-kpi-lbl">Complexity</span><span class="ab-kpi-val">${esc(resp.complexity)}</span>`;
document.getElementById('ab-res-total').innerHTML =
  `<span class="ab-kpi-lbl">Total tokens</span><span class="ab-kpi-val">${resp.total_forecast?.toLocaleString()}</span>`;
document.getElementById('ab-res-confidence').innerHTML =
  `<span class="ab-kpi-lbl">Confidence</span><span class="ab-kpi-val">${esc(resp.confidence)}</span>`;
```

---

### P3 — recent_commits rendered as [object Object] (dormant)

**File:** `riia-jun-release/dashboard/js/ops/agent-builds.js` — `renderSkillVersions()`

**Root cause:**
```js
const commits = (s.recent_commits ?? []).slice(0, 2)
  .map(c => `<code ...>${esc(c)}</code>`)
```
`recent_commits` items are objects `{hash, message}`, not strings.
Currently dormant because the API always returns `recent_commits=[]`.
Will surface when P1 Skill Version History fix is applied.

**Fix:** change `esc(c)` to `` `${esc(c.hash)} — ${esc(c.message)}` ``

---

## New Feature: Actual Token Tracking from Claude API

### Motivation
Token estimates shown on the Agent Builds page are based on per-agent `token_estimate` fields
in the run JSON files — these are the orchestrator's rough guesses, not actual Claude API usage.
The user noted a visible gap between estimated and actual consumption (run 20260514-1945).

Accurate token data requires reading the actual `usage` object returned by the Claude API
(`input_tokens`, `output_tokens`, `cache_read_input_tokens`, `cache_creation_input_tokens`).

### Requirements

#### R1 — Capture actual token usage per agent run
- When any agent completes a task (PM, Architect, Engineer, QA, TechWriter), capture the
  Claude API response `usage` object and store it alongside the agent result in the run JSON.
- Fields to capture per agent:
  - `input_tokens` — tokens sent to Claude
  - `output_tokens` — tokens generated by Claude
  - `cache_read_input_tokens` — tokens served from prompt cache (if any)
  - `cache_creation_input_tokens` — tokens written to cache
  - `total_tokens` = input + output (the billable measure)

#### R2 — Store actual tokens in run JSON and DB
- In `riia-ai-org/agent-ops/runs/run-*.json`, each agent entry gains an `actual_tokens` block:
  ```json
  {
    "role": "engineer",
    "token_estimate": 33000,
    "actual_tokens": {
      "input_tokens": 28400,
      "output_tokens": 4200,
      "cache_read_input_tokens": 18000,
      "cache_creation_input_tokens": 0,
      "total_tokens": 32600
    }
  }
  ```
- `AgentBuildAgentModel` DB table: add `actual_tokens_total INT` column (via Alembic migration).
- `AgentOut` schema: add `actual_tokens: Optional[dict] = None`.

#### R3 — Show actual vs estimated in Agent Builds UI
- Run History table: replace "Forecast Δ" column with "Est / Actual" showing both numbers.
  Colour code: green if actual ≤ estimate, amber if within 25%, red if over by >25%.
- Token Cost Trend chart: add a second dataset per role ("Actual") alongside the existing "Estimate".
- Token Forecast vs Actual chart: replace `total_tokens_estimated` (sum of estimates) with
  `total_actual_tokens` (sum of `actual_tokens.total_tokens` from all agents in the run).

#### R4 — Feed actual data into forecast calibration
- `aggregate_metrics.py`: when computing `token_forecasting.by_feature_type[x].avg_tokens`,
  prefer `actual_tokens.total_tokens` over `total_tokens_estimated` where available.
- This automatically improves the token forecast endpoint accuracy over time.

#### R5 — Display cache efficiency on Agent Builds page
- Add a "Cache Hit Rate" KPI card: `avg(cache_read / input_tokens)` across recent runs.
- High cache hit rate = prompt caching working correctly and saving cost.

### Files to Touch
| File | Change |
|---|---|
| `riia-ai-org/agent-ops/runs/run-*.json` (new runs only) | Add `actual_tokens` block to each agent |
| `.claude/commands/enhance.md` Step 7 | Record `actual_tokens` from each agent's API response into the run log |
| `src/rita/models/agent_builds.py` | Add `actual_tokens_total` column |
| `src/rita/schemas/agent_builds.py` | Add `actual_tokens` field to `AgentOut`, `actual_tokens_total` to run response |
| `src/rita/api/experience/ops.py` | Surface `actual_tokens` from per-run JSON alongside `token_forecast` |
| `dashboard/js/ops/agent-builds.js` | Update Run History table + Token chart to show actual vs estimated |
| `riia-ai-org/agent-ops/aggregate_metrics.py` | Prefer actual tokens in `by_feature_type` avg calculation |

### Implementation Note
The `/enhance` orchestrator controls when run logs are written (Step 7). The actual token
counts need to be recorded by each agent step as it reports back, not derived after the fact.
This means the orchestrator must ask each agent to report its token usage when it completes,
or the harness must expose `usage` from the Claude API response automatically.

For Claude Code agents (general-purpose, Plan, etc.), token usage is visible in the API
response object. The orchestrator should capture this and write it into the agent result
block before closing the run log.

---

## Implementation Order (Next Session)

1. Fix P1: Trend Lines (ops.py + agent-builds.js) — ~1 enhance run
2. Fix P1: Skill Version History (ops.py + agent-builds.js) — small ops.py edit
3. Fix P2: Estimate result cards (agent-builds.js only) — 5-line fix
4. New Feature: Actual Token Tracking — full /enhance run (medium complexity)
