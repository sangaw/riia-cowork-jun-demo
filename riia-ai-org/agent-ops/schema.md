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
