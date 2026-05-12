# AgentOps Run Log — JSON Schema

One file per `/enhance` run. Stored at `riia-ai-org/agent-ops/runs/run-{YYYYMMDD-HHMM}.json`.

---

## Top-Level Fields

| Field | Type | Description |
|---|---|---|
| `run_id` | string | Timestamp ID in format `YYYYMMDD-HHMM` — unique per run |
| `app` | string | Target app: `rita` \| `fno` \| `ops` |
| `request` | string | Original user request verbatim |
| `skill_file` | string | Relative path to the skill file used (e.g. `project-office/skills/skill-add-rita-feature.md`) |
| `agents` | array | Ordered list of agent result objects (see below) |
| `overall_status` | string | Derived: `pass` \| `pass_with_warnings` \| `fail` — any fail = fail; any warning = pass_with_warnings |
| `total_tokens_estimated` | integer | Sum of all agent `token_estimate` values |
| `duration_minutes` | number | Wall-clock time from run start to completion |
| `branch` | string | Git branch created by the Engineer agent (e.g. `feature/add-timestamp-label`) |

---

## New Top-Level Run Log Fields (v2)

Added by `backfill_metrics.py` for all existing runs; included by default in new runs.

| Field | Type | Description |
|---|---|---|
| `retry_count` | integer | Number of times the run was retried after an initial failure |
| `abandoned` | boolean | `true` if the run was abandoned before completion |
| `loop_events` | integer | Count of agentic loop cycles detected during the run |
| `hitl_events` | array of objects | Human-in-the-loop interventions; empty array if none |
| `hitl_events[].step` | string | Agent role/step where the intervention occurred |
| `hitl_events[].type` | string | `"correction"` or `"override"` |
| `hitl_events[].description` | string | Free-text description of the human action |
| `hitl_events[].timestamp` | string | ISO 8601 timestamp of the intervention |
| `token_forecast` | object | Pre-run token budget forecast (see sub-fields below) |
| `token_forecast.complexity` | string | `"small"` / `"medium"` / `"large"` |
| `token_forecast.complexity_score` | float | Weighted average of 4 complexity signals (0.7–1.5) |
| `token_forecast.feature_type` | string | `"rita"` / `"ops"` / `"fno"` / `"invest-game"` |
| `token_forecast.per_role` | object | Keys: pm, architect, engineer, qa, techwriter; values: integer token estimates |
| `token_forecast.total_forecast` | integer | Sum of all per-role forecast values |
| `token_forecast.confidence` | string | `"±25%"` if `basis_runs >= 5`, else `"±40%"` |
| `token_forecast.basis_runs` | integer | Number of prior runs for the same `feature_type` used to calibrate the forecast |
| `human_score` | object or null | Post-run human quality score (null until scored) |
| `human_score.accuracy` | integer (1–5) or null | How accurately the agents implemented the spec |
| `human_score.relevance` | integer (1–5) or null | How relevant the output was to the original request |
| `human_score.planning_ok` | boolean or null | Whether the PM / Architect plan was sound |
| `human_score.csat` | integer (1–5) or null | Overall customer satisfaction score |
| `human_score.time_saved_hours` | float or null | Estimated developer hours saved by the run |

---

## Agent Object Fields (`agents[]`)

| Field | Type | Description |
|---|---|---|
| `role` | string | `pm` \| `architect` \| `engineer` \| `qa` \| `techwriter` |
| `status` | string | `pass` \| `pass_with_warnings` \| `fail` |
| `steps_required` | integer | Number of steps defined in the skill file for this role |
| `steps_completed` | integer | Number of steps the agent actually completed |
| `adherence_score` | float | `steps_completed / steps_required` — range 0.0–1.0 |
| `token_estimate` | integer | Estimated tokens consumed by this agent invocation |
| `grounding_checks` | object | Key/value map of validation gate name → `true` \| `false` (see per-role checks below) |
| `failure_modes` | array | List of failure code strings observed (see `failure-catalog.md`), empty if none |

---

## Grounding Checks — Per Role

### PM (`pm`)
| Check | Description |
|---|---|
| `plan_status_read` | Agent read PLAN_STATUS.md before approving |
| `sprint_fit_confirmed` | Feature fits within current sprint scope |
| `risk_flags_assessed` | Risk flags section populated |
| `approved` | Final approval decision: `true` = proceed, `false` = halt |

### Architect (`architect`)
| Check | Description |
|---|---|
| `api_contract_present` | API endpoint defined with method, path, request/response shape |
| `files_listed` | All files to touch listed explicitly |
| `dod_checklist_filled` | Definition of Done checklist populated |
| `spec_reference_valid` | Spec file path referenced and readable |

### Engineer (`engineer`)
| Check | Description |
|---|---|
| `branch_created` | Feature branch exists in git |
| `code_changed` | At least one source file modified |
| `spec_updated` | Relevant spec file updated in same task |
| `ruff_passed` | Python linter passed (or N/A for JS-only changes) |
| `contract_matches_architect` | Implemented API matches Architect-defined contract |
| `memory_used` | Engineer read `eng-context.md` during the run |
| `tool_error_handled` | FC code present but status not `"fail"` (self-recovered) |

### QA (`qa`)
| Check | Description |
|---|---|
| `tests_written` | At least one test file created or modified |
| `tests_passed` | All written tests pass |
| `coverage_delta_recorded` | Coverage change (positive or negative) noted |
| `contract_check_done` | API contract re-verified against implementation |

### TechWriter (`techwriter`)
| Check | Description |
|---|---|
| `confluence_updated` | Confluence page published or updated |
| `spec_file_confirmed` | Spec file reflects final implemented state |
| `branch_noted` | Branch name recorded in documentation |

---

## Status Derivation Rules

```
overall_status = "fail"               if any agent.status == "fail"
overall_status = "pass_with_warnings" if any agent.status == "pass_with_warnings" AND no "fail"
overall_status = "pass"               if all agent.status == "pass"

agent.status = "fail"               if steps_completed / steps_required < 0.5
agent.status = "pass_with_warnings" if steps_completed / steps_required >= 0.5 AND < 1.0
agent.status = "pass"               if steps_completed == steps_required AND all grounding_checks pass
```

---

## Sample File Name

```
runs/run-20260430-1415.json
```
