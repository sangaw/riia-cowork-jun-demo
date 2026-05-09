# Agentic AI Orchestration — Build Plan
**Folder:** `riia-ai-org/`
**Design doc:** `../project-office/agents/Agentic_AI_Enterprise_Approach.md`
**Status:** Ready to build

---

## Context Boundary

Steps 1–4 are built in the first session. After Step 4, **clear context** to reclaim tokens.
Steps 5–10 are built in the second session — load this file first to resume.

---

## Steps 1–4 — Orchestrator Foundation
*(Build in Session 1, then clear context)*

### Step 1 — Per-App UI Skill Files
**What:** Create three skill files compiled from the RITA/FnO/Ops specs.
**Files to create:**
- `project-office/skills/skill-add-rita-feature.md`
- `project-office/skills/skill-add-fno-feature.md`
- `project-office/skills/skill-add-ops-feature.md`

**Source specs to read:**
- `project-office/specs/Spec_RITA_App.md` (app overview, API routes, UI panels)
- `project-office/specs/Spec_JS_Code.md` (JS conventions, module layout)

**What each skill file contains:**
- App identity (which HTML file, which JS modules, which API tier)
- File map (which files to touch for a UI feature)
- Step-by-step task rules (endpoint → service → repo → JS → spec update)
- Named guardrails (never hardcode, never skip spec update, use worktree)
- Definition of Done checklist (6 items the Engineer agent must verify)

**Done when:** Three skill files exist in `project-office/skills/`, each ~150–200 lines.

---

### Step 2 — Task Brief Template + Archive Directory
**What:** Create the inter-agent handoff document template and the archive folder.
**Files to create:**
- `project-office/task-briefs/TEMPLATE.md`
- `project-office/task-briefs/.gitkeep` (so the directory is tracked)

**Template sections:**
- `## Request` — original user request verbatim
- `## App Target` — rita | fno | ops
- `## Skill Selected` — path to skill file
- `## Spec Reference` — path to spec file(s)
- `## [PM] Validation` — sprint fit, risk flags, approved to proceed
- `## [Architect] Design` — API contract, frontend DOM targets, files to touch, DoD checklist
- `## [Engineer] Implementation Log` — branch, files changed, contract verified, spec updated
- `## [QA] Test Results` — tests written, passed, coverage delta, contract check
- `## [TechWriter] Documentation` — Confluence page updated, spec file confirmed

**Done when:** Template file exists with all sections; directory is committed.

---

### Step 3 — `/enhance` Orchestrator Slash Command
**What:** The core wiring — the single entry point that runs the full agent chain.
**File to create:** `riia-cowork-jun/.claude/commands/enhance.md`

**Command behaviour (inline, no sub-agent for orchestration logic):**
1. Parse `<app>` argument (rita / fno / ops) and `<description>` from user input
2. Select skill file + spec files using the routing table (inline in the command)
3. Create `project-office/task-briefs/task-brief-{timestamp}.md` from TEMPLATE.md
4. Spawn **PM Agent** (`general-purpose`) — reads PLAN_STATUS.md + brief header; writes `[PM]` section
5. Validate PM section (approved: yes/no) — halt if no
6. Spawn **Architect Agent** (`Plan`) — reads brief + spec excerpt (max 400 lines); writes `[Architect]` section
7. Validate Architect section (API contract present? files listed? DoD filled?) — re-invoke if incomplete
8. Spawn **Engineer Agent** (`general-purpose`, `isolation: "worktree"`) — reads brief + skill file; writes code + `[Engineer]` section
9. Validate Engineer section (branch created? spec updated? ruff passed?) — flag warnings
10. Spawn **QA Agent** (`general-purpose`) — reads brief + new code; writes tests + `[QA]` section
11. Spawn **TechWriter Agent** (`general-purpose`) — reads full brief; updates Confluence + `[TechWriter]` section
12. Report final state: branch name, all gate results, task brief path

**Routing table (inline in command):**
| App | Skill file | Spec files |
|---|---|---|
| `rita` | `skill-add-rita-feature.md` | `Spec_RITA_App.md` + `Spec_JS_Code.md` |
| `fno` | `skill-add-fno-feature.md` | `Spec_RITA_App.md` + `Spec_JS_Code.md` |
| `ops` | `skill-add-ops-feature.md` | `Spec_RITA_App.md` + `Spec_JS_Code.md` |

**Done when:** Command file exists; `/enhance rita "test"` can be invoked without errors.

---

### Step 4 — Smoke Test
**What:** Run `/enhance` on a small real feature to verify the full chain fires correctly.
**Test request:** `/enhance rita "Add a last-updated timestamp label to the market signals panel"`

**What to verify:**
- [ ] Task brief file created with correct timestamp
- [ ] PM section written (approved: yes)
- [ ] Architect section written (API contract + files listed)
- [ ] Engineer section written (branch created, code changed)
- [ ] QA section written (at least 1 test)
- [ ] TechWriter section written
- [ ] Feature branch exists in git

**Capture:** Note any agent failures or missing sections. Add one rule per failure to the relevant skill file before closing the session.

**Done when:** Full task brief exists with all 5 agent sections complete; feature branch exists.

---

## Steps 5–10 — AgentOps Monitoring System
*(Build in Session 2 — load this file first)*

---

### Step 5 — Run Log Structure + JSON Schema
**What:** Define the per-run JSON format and create the directory.
**Files to create:**
- `riia-ai-org/agent-ops/runs/.gitkeep`
- `riia-ai-org/agent-ops/schema.md` — documents the JSON fields

**JSON schema (one file per `/enhance` run):**
```json
{
  "run_id": "YYYYMMDD-HHMM",
  "app": "rita | fno | ops",
  "request": "original user request",
  "skill_file": "path/to/skill-file.md",
  "agents": [
    {
      "role": "pm | architect | engineer | qa | techwriter",
      "status": "pass | pass_with_warnings | fail",
      "steps_required": 4,
      "steps_completed": 4,
      "adherence_score": 1.0,
      "token_estimate": 3200,
      "grounding_checks": {},
      "failure_modes": []
    }
  ],
  "overall_status": "pass | pass_with_warnings | fail",
  "total_tokens_estimated": 14800,
  "duration_minutes": 11,
  "branch": "feature/branch-name"
}
```

**Done when:** Directory exists; schema documented; sample `run-sample.json` created for dashboard testing.

---

### Step 6 — Wire Run Log Writing into `/enhance`
**What:** Update the `/enhance` command to write a JSON run log after the full chain completes.
**File to modify:** `riia-cowork-jun/.claude/commands/enhance.md`

**Changes:**
- After all agents complete, orchestrator writes `riia-ai-org/agent-ops/runs/run-{timestamp}.json`
- Grounding check results per agent are captured into the JSON
- `overall_status` is derived from agent statuses (any fail = fail; any warning = pass_with_warnings)

**Done when:** After a real `/enhance` run, a valid JSON log file appears in `runs/`.

---

### Step 7 — Metrics Aggregator Python Script
**What:** Python script that rolls up all `runs/*.json` files into `metrics.json` for the dashboard.
**File to create:** `riia-ai-org/agent-ops/aggregate_metrics.py`

**What it computes:**
- Per-role: average adherence score, first-pass rate, average token cost
- Per-app: run count, pass/fail breakdown
- Grounding score trend (per-run % of checks passed)
- Failure mode frequency table (which failure types appear most)
- Skill file version history (from git log on skill files)

**Output:** `riia-ai-org/agent-ops/metrics.json`

**Run:** `python riia-ai-org/agent-ops/aggregate_metrics.py`

**Done when:** Script runs without error; `metrics.json` is generated with correct structure.

---

### Step 8 — AgentOps Dashboard HTML
**What:** Static HTML/JS dashboard that reads `runs/*.json` + `metrics.json` and renders all 6 panels.
**File to create:** `riia-ai-org/agent-ops/dashboard.html`

**6 panels:**
1. **Pipeline Run History** — timeline table of each run (app, status, duration, branch)
2. **Agent Scorecards** — per-role: adherence rate, first-pass rate, avg token cost
3. **Grounding Score Trend** — line chart: % validation checks passed per run over time
4. **Failure Mode Heatmap** — grid: failure type × agent role, colour = frequency
5. **Token Cost Trend** — line chart: tokens per task type over time
6. **Skill File Version History** — table: skill file, last updated, quality metric before/after

**Technology:** Same pattern as RITA/FnO/Ops dashboards — vanilla JS, `fetch()` to load JSON, Chart.js for charts, no server.

**Done when:** Dashboard opens in browser; all 6 panels render with sample data from Step 5.

---

### Step 9 — Failure Catalog + Skill File Linkage
**What:** Create a structured failure catalog and wire it into the dashboard.
**Files to create:**
- `riia-ai-org/agent-ops/failure-catalog.md` — categorised failure modes + which skill file fixes each

**Failure catalog structure:**
```markdown
## FC-001 spec_not_updated
- Agent role: Engineer
- Skill file to update: skill-add-{app}-feature.md
- Rule to add: "After changing any API contract, update the relevant Spec file in the same task."
- Observed: N times

## FC-002 api_contract_missing
- Agent role: Architect
...
```

**Dashboard linkage:** Failure mode heatmap cells link to the relevant catalog entry.

**Done when:** Catalog exists with at least 5 common failure modes pre-populated; dashboard links are functional.

---

### Step 10 — End-to-End Demo Run + Hardening ✓ COMPLETE
**What:** Run a full demo-quality `/enhance` on a real feature; record the run; verify dashboard shows it.
**Demo request (pivoted):** `/enhance rita "Show date and time on the ms-last-updated label in the market signals panel"` — FnO Greeks feature was dropped as too token-heavy.

**Hardening checklist:**
- [x] Full task brief written with all 5 sections — `task-brief-20260430-1809.md`
- [x] Run log JSON written to `runs/` — `run-20260430-1809.json`
- [x] `aggregate_metrics.py` runs and updates `metrics.json` — 2 runs aggregated
- [x] Dashboard renders the new run in Pipeline Run History
- [x] Merge step added to `/enhance` (Step 6.5) — gap caught and fixed during this run
- [x] Any new rules added to relevant skill file
- [ ] Demo script documented (exact input → expected output per agent)

**Done when:** Demo can be walked through live — user types one command, five agents run, dashboard shows the result.

---

## File Map (Complete)

```
riia-cowork-jun/
├── .claude/commands/
│   └── enhance.md                          ← Step 3
└── project-office/
    ├── skills/
    │   ├── skill-add-rita-feature.md       ← Step 1
    │   ├── skill-add-fno-feature.md        ← Step 1
    │   └── skill-add-ops-feature.md        ← Step 1
    └── task-briefs/
        ├── TEMPLATE.md                     ← Step 2
        └── task-brief-{timestamp}.md       ← generated at runtime

riia-ai-org/
└── agent-ops/
    ├── dashboard.html                      ← Step 8
    ├── aggregate_metrics.py                ← Step 7
    ├── metrics.json                        ← generated by Step 7
    ├── schema.md                           ← Step 5
    ├── failure-catalog.md                  ← Step 9
    └── runs/
        └── run-{timestamp}.json            ← generated at runtime (Step 6)
```


cd riia-ai-org/agent-ops
python -m http.server 8900

Then open http://localhost:8900/dashboard.html.