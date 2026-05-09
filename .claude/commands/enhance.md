# /enhance — Multi-Agent Feature Orchestrator

Orchestrates a chain of specialist agents to plan, build, test, and document a feature enhancement for the RITA, FnO, or Ops dashboard.

**Usage:** `/enhance <app> "<description>"`
**Examples:**
- `/enhance rita "Add a volatility regime indicator to the market signals panel"`
- `/enhance fno "Add a net Greeks exposure summary to the portfolio overview"`
- `/enhance ops "Add a failed test trend chart to the test results section"`

---

## How to Execute This Command

You are the orchestrator. Read these instructions fully before taking any action. Execute each step in sequence. Do not skip steps. Do not spawn the next agent until the current agent's section passes validation.

---

## Step 0 — Parse Arguments

Parse `$ARGUMENTS` to extract:
- `APP` — the first word (must be one of: `rita`, `fno`, `ops`)
- `DESCRIPTION` — everything after the first word (strip surrounding quotes)

If `APP` is not one of the three valid values, reply:
> "Unknown app '{APP}'. Valid apps: rita, fno, ops. Usage: /enhance <app> \"<description>\""

Then stop.

**Routing table — select skill + spec based on APP:**

| APP | Skill file | Primary spec | Secondary spec |
|---|---|---|---|
| `rita` | `project-office/skills/skill-add-rita-feature.md` | `project-office/specs/Spec_RITA_App.md` | `project-office/specs/Spec_JS_Code.md` |
| `fno` | `project-office/skills/skill-add-fno-feature.md` | `project-office/specs/Spec_RITA_App.md` | `project-office/specs/Spec_JS_Code.md` |
| `ops` | `project-office/skills/skill-add-ops-feature.md` | `project-office/specs/Spec_RITA_App.md` | `project-office/specs/Spec_JS_Code.md` |

Set:
- `SKILL_FILE` = skill file path from routing table
- `SPEC_FILE` = primary spec path
- `TIMESTAMP` = current datetime as `YYYYMMDD-HHMM`
- `BRIEF_PATH` = `project-office/task-briefs/task-brief-{TIMESTAMP}.md`
- `RUN_LOG_PATH` = `riia-ai-org/agent-ops/runs/run-{TIMESTAMP}.json`

Initialize in-memory tracking (carry these values forward through all steps):
- `AGENT_RESULTS` = empty list — each agent appends one record after validation
- `RUN_BRANCH` = "" — set by Engineer validation
- `RUN_WARNINGS` = [] — accumulates ⚠ warning strings

---

## Step 1 — Create Task Brief

Read `project-office/task-briefs/TEMPLATE.md`.

Create `{BRIEF_PATH}` by copying the template and filling in the header block:
- Replace `{timestamp}` with `{TIMESTAMP}`
- Replace `{YYYYMMDD-HHMM}` with `{TIMESTAMP}`
- Replace `{in-progress | complete | failed}` with `in-progress`
- Replace the `## Request` placeholder with the exact `DESCRIPTION` text
- Replace the `## App Target` placeholder with `{APP}`
- Replace the skill file path with `{SKILL_FILE}`
- Replace the spec references with the correct paths for `{APP}`

Leave all agent sections (`[PM]`, `[Architect]`, `[Engineer]`, `[QA]`, `[TechWriter]`) as template placeholders — each agent will fill in its own section.

Report to user:
```
── Orchestrator ──────────────────────────────────────────
✓ App identified: {APP}
✓ Skill selected: {SKILL_FILE}
✓ Task brief created: {BRIEF_PATH}
─────────────────────────────────────────────────────────
```

---

## Step 2 — PM Agent

Spawn a `general-purpose` agent with this prompt:

```
You are the PM Agent for the RITA project.

Read these files:
1. PLAN_STATUS.md (first 80 lines only — for sprint context)
2. {BRIEF_PATH} (the ## Request and ## App Target sections)

Your job: validate that the requested feature fits the current sprint scope.

Write the [PM] Validation section into {BRIEF_PATH}. Fill in every field:
- Sprint alignment: state whether this is in scope for the current sprint and why
- Risk flags: list any technical risks, dependencies, or blockers you identify. Write "none" if there are none.
- Dependencies: list prerequisite tasks or external dependencies. Write "none" if there are none.
- Approved to proceed: write "yes" or "no". Write "yes" unless there is a clear blocker (out of scope for sprint, hard dependency unmet, risk too high). Default to yes for reasonable feature additions.

Save the updated brief file after writing your section.
Report: "PM section complete. Approved: yes/no."
```

**After the PM agent completes:**

Read `{BRIEF_PATH}` — find the `[PM] Validation` section.
Check: does `Approved to proceed:` equal `yes`?

- If **yes**: report `✓ PM Agent — approved` and proceed to Step 3.
- If **no**: report the reason to the user and stop:
  > "Enhancement halted at PM validation. Reason: {reason from brief}. Resolve the blocker and re-run /enhance."

**Record PM agent result** (append to `AGENT_RESULTS`):
```json
{
  "role": "pm",
  "status": "<pass if approved=yes, else fail>",
  "steps_required": 4,
  "steps_completed": "<4 if approved=yes, else 3>",
  "adherence_score": "<steps_completed / 4>",
  "token_estimate": 2100,
  "grounding_checks": {
    "plan_status_read": true,
    "sprint_fit_confirmed": "<true if sprint alignment is stated>",
    "risk_flags_assessed": "<true if risk flags section is non-empty>",
    "approved": "<true or false>"
  },
  "failure_modes": []
}
```

---

## Step 3 — Architect Agent + TechWriter (Design Recording)

### Step 3a — Architect Agent

Spawn a `Plan` agent with this prompt:

```
You are the Architect Agent for the RITA project.

Read these files in order:
1. {BRIEF_PATH} — focus on ## Request, ## App Target, ## Skill Selected
2. {SKILL_FILE} — read fully (endpoint inventory, module reference, code patterns, guardrails are all here)

Do NOT read spec files, HTML files, JS files, or Python source files. The skill file contains all the app context you need.

Your job: design the complete technical specification for this feature. You make design decisions — do not implement code and do not write files.

Produce a complete design covering all of the following. Output it clearly labelled so it can be recorded:

1. Feature summary: 1-2 sentences describing what the feature does for the user.

2. API contract: method, path, query params, request body, response shape (list every field the JS will read), auth required.
   - Choose the correct API tier: Experience tier for UI aggregation reads, Portfolio tier for FnO computation, System tier for raw CRUD.
   - Experience tier path format: /api/experience/{app}/feature-name
   - The path must not duplicate any existing endpoint in the spec.

3. Frontend target: JS module filename, section id (sec-name format), DOM element IDs the JS will target, window bindings needed.

4. Files to touch: list every file that must be created or modified, with a brief description of the change.

5. Edge cases to handle: list at least 2 (empty API response, null fields, API error).

6. Definition of Done checklist: the 8 items from the skill file for {APP} — mark none as checked (Engineer will check them).

Report: your complete design output. Do not write to any file.
```

**After the Architect agent completes:**

Capture the full design output returned by the Architect agent. Store it as `ARCHITECT_DESIGN`.

Validate `ARCHITECT_DESIGN` against these checks:

| Check | Pass condition |
|---|---|
| Feature summary present | Not empty |
| API contract present | Method, path, and at least 2 response fields |
| Frontend target present | JS module name, section id, at least 1 DOM id |
| Files to touch listed | At least 3 files |
| Edge cases listed | At least 2 edge cases |

- If **any fail**: re-invoke the Architect agent with:
  ```
  Your design output was incomplete. Missing: {list the failed checks}.
  Produce the complete design again covering all 6 sections. Do not write files.
  ```
  Re-validate. If it fails a second time, report to user and stop:
  > "Architect agent failed to produce a complete design after 2 attempts. Review the request and re-run /enhance."

### Step 3b — TechWriter (Record Architect Design)

Once `ARCHITECT_DESIGN` passes validation, spawn a `general-purpose` agent with this prompt:

```
You are the TechWriter Agent for the RITA project. You are recording a design produced by the Architect Agent into the task brief.

The Architect's design output is:

{ARCHITECT_DESIGN}

Write this into the [Architect] Design section of the task brief at {BRIEF_PATH}.

Replace the placeholder line "{to be filled by Architect Agent}" with the formatted [Architect] Design section. Use the table and checklist format from the template — structure the Architect's output into the correct fields (Feature summary, API contract table, Frontend target table, Files to touch table, Edge cases, Definition of Done checklist).

Do not add your own opinions or changes — record the Architect's design faithfully.

Save the updated brief file.
Report: "Architect design recorded into task brief."
```

**After TechWriter completes Step 3b:**

Report `✓ Architect Agent — design complete and recorded` and proceed to Step 4.

**Record Architect agent result** (append to `AGENT_RESULTS`):
```json
{
  "role": "architect",
  "status": "<pass if all 5 validation checks passed on first attempt, pass_with_warnings if passed on second attempt>",
  "steps_required": 4,
  "steps_completed": "<4 if all checks passed>",
  "adherence_score": "<steps_completed / 4>",
  "token_estimate": 3400,
  "grounding_checks": {
    "api_contract_present": "<true/false from validation>",
    "files_listed": "<true/false from validation>",
    "dod_checklist_filled": "<true/false from validation>",
    "spec_reference_valid": "<true/false from validation>"
  },
  "failure_modes": ["FC-002" if api_contract was missing on first attempt, else []]
}
```

---

## Step 4 — Engineer Agent

Spawn a `general-purpose` agent with `isolation: "worktree"` and this prompt:

```
You are the Engineer Agent for the RITA project. You are working in an isolated git worktree.

IMPORTANT — WORKTREE RULES:
- You are in a git worktree. Your working directory is the worktree root.
- All file reads and writes must use paths relative to your worktree root, or absolute paths within it.
- Do NOT write to files outside your worktree. Do not reference the parent repo's working directory.
- Run `git rev-parse --show-toplevel` first to confirm your worktree root path.
- Your branch name is the current branch in this worktree — run `git branch --show-current` to get it.

Read these files in order (use absolute paths from your worktree root):
1. {BRIEF_PATH} — focus on [Architect] Design section (API contract, files to touch, DoD checklist)
2. {SKILL_FILE} — read fully (all rules, guardrails, code templates, and Definition of Done)

Do NOT read HTML files, spec files, or other source files beyond the specific files you are editing. The skill file and task brief contain all the patterns and context you need.

Your job: implement the feature exactly as designed in the Architect section. Follow every rule in the skill file.

Implementation order:
1. Run `git rev-parse --show-toplevel` — confirm worktree root. All your edits go inside this path.
2. Run `git branch --show-current` — record your branch name.
3. Create the Pydantic schema file first (src/rita/schemas/) — inside the worktree
4. Add the backend endpoint (correct tier as per Architect design) — inside the worktree
5. Register the router in main.py only if you created a new router file
6. Create the JS module (dashboard/js/{APP}/) — inside the worktree
7. Register the section loader and window bindings in dashboard/js/{APP}/main.js
8. Update Spec_RITA_App.md — add the new endpoint to the correct tier table
9. Update Spec_JS_Code.md — add the new JS module to the {APP} module structure table
10. Run: ruff check src/ — fix any errors before proceeding

After all changes are made, commit them to your branch:
- Stage all changed files: `git add -p` or `git add <file>` for each file you modified
- Commit with message: `feat({APP}): {brief 1-line description of the feature}`
- Confirm the commit exists: `git log --oneline -3`

After committing, fill in the [Engineer] Implementation Log section of {BRIEF_PATH}:
- Branch: your branch name (from git branch --show-current)
- Worktree path: your worktree root (from git rev-parse --show-toplevel)
- Files changed: list every file you created or modified
- Commit hash: the short hash from git log --oneline -1
- API contract verified: yes/no
- Spec updated: yes/no
- Ruff result: passed/failed

Then go through the 8-item Definition of Done checklist from the Architect section — check each item.
Write the result (checked/unchecked) for each item in the Engineer section of the brief.

Do NOT mark the task complete if any DoD item is unchecked. Fix the gap first.

Save the updated brief file.
Report: "Engineer section complete. Branch: {branch}. Commit: {hash}. DoD: {n}/8 passed."
```

**After the Engineer agent completes:**

Read `{BRIEF_PATH}` — find the `[Engineer] Implementation Log` section. Check:

| Check | Pass condition |
|---|---|
| Branch present | Not empty, not "master" |
| Commit hash present | Not empty |
| Files changed listed | At least 2 files |
| Ruff result | "passed" |
| Spec updated | "yes" |

- If **branch is master**: report error and stop — `Engineer agent wrote to master instead of a worktree branch. Do not proceed. Check worktree isolation.`
- If **commit hash missing**: report error and stop — `Engineer agent did not commit. Changes may be lost. Check worktree and commit manually.`
- If **ruff failed**: report as warning — `⚠ Engineer Agent — ruff errors present. Review before merging.` — add `"FC-003"` to Engineer failure_modes
- If **spec not updated**: report as warning — `⚠ Engineer Agent — spec not updated. Add rule to {SKILL_FILE}: "Always update spec in same task."` — add `"FC-001"` to Engineer failure_modes
- Otherwise: report `✓ Engineer Agent — implementation complete. Branch: {branch}. Commit: {hash}`

Set `RUN_BRANCH` = branch name from the Engineer section.

**Record Engineer agent result** (append to `AGENT_RESULTS`):
```json
{
  "role": "engineer",
  "status": "<fail if branch=master or no commit; pass_with_warnings if ruff failed or spec not updated; pass otherwise>",
  "steps_required": 5,
  "steps_completed": "<count of checks that passed: branch_created, code_changed, spec_updated, ruff_passed, contract_matches_architect>",
  "adherence_score": "<steps_completed / 5>",
  "token_estimate": 5200,
  "grounding_checks": {
    "branch_created": "<true if branch present and not master>",
    "code_changed": "<true if files_changed >= 2>",
    "spec_updated": "<true/false from brief>",
    "ruff_passed": "<true/false from brief>",
    "contract_matches_architect": "<true if no contract mismatch reported>"
  },
  "failure_modes": ["FC-001" if spec not updated, "FC-003" if ruff failed — use [] if none]
}
```

---

## Step 5 — QA Agent

Spawn a `general-purpose` agent with this prompt:

```
You are the QA Agent for the RITA project.

Read this file only:
1. {BRIEF_PATH} — read fully (all sections: Architect Design for contract + edge cases, Engineer log for files changed)

Do NOT read source files, HTML files, or spec files. All contract information is in the task brief.

Your job: write unit tests for the new endpoint and verify the API-frontend contract.

Tasks:
1. Write at least 1 unit test per new endpoint function. Place tests in tests/unit/.
   Test structure: happy path + at least 1 edge case from the Architect's edge cases list.
   Use pytest. Mock the database session where needed.

2. Verify the API-frontend contract:
   - List every field in the Pydantic response schema
   - List every field the JS module reads from the response (from the JS file in files changed)
   - Check they match. Flag any mismatch as a failure.

3. Run the tests: pytest tests/unit/ -v
   Record: tests written, tests passed, any failures.

Fill in the [QA] Test Results section of {BRIEF_PATH}:
- Tests written: n
- Test file: path
- Tests passed: n/n
- Coverage delta: estimate from pytest output
- Contract check table: schema field vs handler return vs match
- Edge cases tested: list each from Architect section, note tested/not tested

Save the updated brief file.
Report: "QA section complete. Tests: {n}/{n} passed. Contract: match/mismatch."
```

**After the QA agent completes:**

Report `✓ QA Agent — {n} tests, {n} passed` (or flag failures as warnings).

**Record QA agent result** (append to `AGENT_RESULTS`):
```json
{
  "role": "qa",
  "status": "<pass if all tests passed and contract matched; pass_with_warnings if any test failed or mismatch found>",
  "steps_required": 4,
  "steps_completed": "<count: tests_written + tests_passed + coverage_delta_recorded + contract_check_done>",
  "adherence_score": "<steps_completed / 4>",
  "token_estimate": 2800,
  "grounding_checks": {
    "tests_written": "<true if tests_written > 0>",
    "tests_passed": "<true if all written tests passed>",
    "coverage_delta_recorded": "<true if coverage delta noted in brief>",
    "contract_check_done": "<true if contract check table present in brief>"
  },
  "failure_modes": ["FC-004" if contract mismatch found, else []]
}
```

---

## Step 6 — TechWriter Agent

Spawn a `general-purpose` agent with this prompt:

```
You are the TechWriter Agent for the RITA project.

Read these files in order:
1. {BRIEF_PATH} — read the full brief (all sections)
2. project-office/context/confluence-guide.md — for Confluence publish instructions

Your job: update the Confluence documentation for the affected app section and confirm the spec files are current.

Tasks:
1. Identify which Confluence page covers the {APP} dashboard. For engineering changes, use the Engineering page (ID 76611602). Refer to confluence-guide.md for the full page ID map.
2. Fetch the current page content using the ConfluenceClient from project-office/confluence/publish.py. The key file is at riia-cowork-jun/confluence-api-key.txt — it contains the token on line 1 and the email on line 2. Always run Confluence scripts from the riia-cowork-jun/ project root so the key file path resolves correctly.
3. Update the page to reflect the new feature: add a row to the endpoint table or a description of the new panel/DOM element.
4. Confirm that Spec_RITA_App.md and Spec_JS_Code.md already reflect the new endpoint and module (Engineer should have done this — if not, update them now).

Fill in the [TechWriter] Documentation section of {BRIEF_PATH}:
- Confluence page updated: URL of the page updated (or "n/a — reason" if not reachable)
- Page section modified: which section of the page was changed
- Spec file confirmed current: yes/no
- Task brief archived: yes (set the Status field at the top of the brief to "complete")

Save the updated brief file.
Report: "TechWriter section complete."
```

**After the TechWriter agent completes:**

Update `{BRIEF_PATH}` status field from `in-progress` to `complete`.

**Record TechWriter agent result** (append to `AGENT_RESULTS`):
```json
{
  "role": "techwriter",
  "status": "<pass if confluence_updated and spec_file_confirmed; pass_with_warnings if confluence was n/a>",
  "steps_required": 3,
  "steps_completed": "<count: confluence_updated + spec_file_confirmed + branch_noted>",
  "adherence_score": "<steps_completed / 3>",
  "token_estimate": 1900,
  "grounding_checks": {
    "confluence_updated": "<true if Confluence page was updated or a valid n/a reason given>",
    "spec_file_confirmed": "<true if spec confirmed current in brief>",
    "branch_noted": "<true if branch name recorded in documentation>"
  },
  "failure_modes": ["FC-005" if spec_file_confirmed=false, else []]
}
```

---

## Step 6.5 — Merge Confirmation + Engineer Merge

After TechWriter completes, present the branch to the user and ask for confirmation before merging.

Report to user:
```
── Merge Review ──────────────────────────────────────────
  Branch: {RUN_BRANCH}
  Commit: {commit hash from Engineer section}
  Files changed: {file list from Engineer section}

  Review the branch above. Reply "merge" to merge into master, or "skip" to leave the branch open.
─────────────────────────────────────────────────────────
```

**Wait for user reply before proceeding.**

- If user replies **"skip"** (or anything other than "merge"): note in run log that merge was deferred. Proceed to Step 7.
- If user replies **"merge"**: spawn a `general-purpose` agent with this prompt:

```
You are the Engineer Agent for the RITA project. Your only job in this task is to merge a feature branch into master.

Branch to merge: {RUN_BRANCH}
Working directory: the main repo root (not a worktree)

Steps:
1. Run: git checkout master
2. Run: git merge --no-ff {RUN_BRANCH} -m "merge({APP}): {DESCRIPTION}"
3. Confirm the merge: git log --oneline -3
4. Report: "Merge complete. Commit: {merge commit hash}."
```

After the Engineer merge agent completes:
- Set `MERGE_STATUS` = `"merged"` and `MERGE_COMMIT` = the merge commit hash
- Report: `✓ Merge complete — {MERGE_COMMIT}`

If user replied "skip":
- Set `MERGE_STATUS` = `"deferred"`
- Report: `⚠ Merge deferred — branch {RUN_BRANCH} left open for manual review`

---

## Step 7 — Write Run Log

After all agents have completed and `AGENT_RESULTS` contains 5 records, write the run log JSON.

**Derive `overall_status`:**
- If any agent has `status = "fail"` → `"fail"`
- Else if any agent has `status = "pass_with_warnings"` → `"pass_with_warnings"`
- Else → `"pass"`

**Compute `total_tokens_estimated`:** sum all agent `token_estimate` values from `AGENT_RESULTS`.

**Compute `duration_minutes`:** elapsed time from Step 0 parse to now (estimate in whole minutes).

**Write `{RUN_LOG_PATH}`** with this structure (fill in all values from tracked state):

```json
{
  "run_id": "{TIMESTAMP}",
  "app": "{APP}",
  "request": "{DESCRIPTION}",
  "skill_file": "{SKILL_FILE}",
  "agents": {AGENT_RESULTS},
  "overall_status": "{derived above}",
  "total_tokens_estimated": {sum of token_estimate values},
  "duration_minutes": {elapsed minutes},
  "branch": "{RUN_BRANCH}",
  "merge_status": "{MERGE_STATUS}",
  "merge_commit": "{MERGE_COMMIT | null if deferred}"
}
```

Report: `✓ Run log written: {RUN_LOG_PATH}`

**Regenerate `riia-ai-org/agent-ops/metrics.json`:**

Run from the repo root (`riia-cowork-jun/`):
```
python riia-ai-org/agent-ops/aggregate_metrics.py
```

This reads all `runs/run-*.json` files and rewrites `metrics.json` with fresh aggregates. The Agent Builds dashboard reads `metrics.json` on next load — no further action needed.

Report: `✓ metrics.json regenerated`

---

## Final Report

Report the completed run to the user:

```
── /enhance complete ─────────────────────────────────────
  App:         {APP}
  Request:     {DESCRIPTION}
  Branch:      {branch from Engineer section}
  Task brief:  {BRIEF_PATH}
  Run log:     {RUN_LOG_PATH}

  Agent results:
  ✓ PM Agent          — approved
  ✓ Architect Agent   — design complete
  ✓ Engineer Agent    — {n}/8 DoD items passed
  ✓ QA Agent          — {n}/{n} tests passed
  ✓ TechWriter Agent  — docs updated
  ✓ Merge             — {merged: {MERGE_COMMIT} | deferred: branch left open}

  Overall status: {overall_status}
  Total tokens:   ~{total_tokens_estimated}
  Duration:       {duration_minutes} min

  {list any ⚠ warnings here}

  Next step: review the branch and merge when ready.
─────────────────────────────────────────────────────────
```

---

## Failure Rules

- **Never auto-advance** past a failed validation gate. Read the section, check the conditions, decide explicitly.
- **PM blocks**: halt the entire run and tell the user why.
- **Architect incomplete after 2 attempts**: halt, tell user to complete manually.
- **Engineer branch missing**: halt.
- **Ruff failures, spec not updated**: warn but continue — these are quality issues, not blockers.
- **QA test failures**: warn and continue — tests are logged in the brief for the user to review.
- **TechWriter Confluence unreachable**: log as "n/a" and continue — not a blocker.
