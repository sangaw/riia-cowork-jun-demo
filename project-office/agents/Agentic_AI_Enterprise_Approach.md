# Agentic AI Enterprise Approach
# RITA / FnO / Ops — Multi-Agent Enhancement Orchestration

**Created:** 2026-04-29
**Status:** Design — ready to implement
**Owner:** Project Office

---

## 1. Vision

A user submits one natural-language request. A network of specialist AI agents — each with compiled domain knowledge — plans, designs, implements, tests, and documents the change autonomously. The user reviews and approves the output.

**Enterprise value proposition:**
- Consistency: every enhancement follows the same governed process
- Speed: parallel specialist agents compress multi-day work into minutes
- Auditability: every agent decision is logged in a traceable artifact
- Scalability: add a new app by adding one spec file and one skill file

**Target demo interaction:**

```
User: /enhance rita "Add a volatility regime indicator to the market signals panel"

  ── Orchestrator ──────────────────────────────────────────
  ✓ App identified: RITA
  ✓ Skill selected: skill-add-rita-feature.md
  ✓ Task brief created: task-brief-20260429-1142.md
  ── Architect Agent ───────────────────────────────────────
  ✓ Mini-spec written to task brief (API contract + DOM target)
  ── Engineer Agent (worktree: feature/volatility-regime) ──
  ✓ Endpoint added: GET /api/experience/rita/market-signals
  ✓ JS module updated: dashboard/js/rita/market-signals.js
  ✓ Spec_RITA_App.md updated
  ── QA Agent ──────────────────────────────────────────────
  ✓ 6 unit tests written; all pass
  ── TechWriter Agent ──────────────────────────────────────
  ✓ Confluence page updated: RITA App / Market Signals
  ─────────────────────────────────────────────────────────
  Done. Branch: feature/volatility-regime — ready for review.
```

---

## 2. What Already Exists (Foundation)

The three-layer foundation is already built. The missing piece is the orchestration wiring.

| Layer | What exists | Purpose |
|---|---|---|
| **Knowledge** | `project-office/specs/Spec_*.md` | Domain knowledge per app and concern |
| **Skills** | `project-office/skills/skill-*.md` | Task rules pre-merged (no spec reads at runtime) |
| **Interface** | `.claude/commands/*.md` | Slash commands (single-step) |
| **Role cards** | `project-office/agents/*.md` | What each agent does, its guardrails, ADRs |
| **Prompt templates** | `project-office/agents/prompts/` | Ready-to-use Agent() call prompts |
| **Memory** | `~/.claude/projects/.../memory/` | Persistent cross-session learning |

**Gap:** Nothing currently wires these agents together. Each is invoked manually. The `/enhance` orchestrator command is the missing piece.

---

## 3. Architecture

### 3.1 Five-Layer Architecture

```
┌─────────────────────────────────────────────────────────┐
│  LAYER 1 — USER INTERFACE                               │
│  /enhance <app> "<description>"                         │
│  Slash command — single entry point for all enhancements│
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│  LAYER 2 — ORCHESTRATOR                                 │
│  Reads intent → selects spec + skill → creates task     │
│  brief → spawns specialist agents in sequence           │
└──┬──────────┬──────────┬──────────┬──────────┬──────────┘
   │          │          │          │          │
┌──▼──┐  ┌───▼──┐  ┌────▼──┐  ┌───▼──┐  ┌───▼──────┐
│ PM  │  │ Arc  │  │ Eng   │  │ QA   │  │ TechWrite│
│Agent│  │ Agent│  │ Agent │  │ Agent│  │ Agent    │
│     │  │      │  │worktree│ │      │  │          │
└──┬──┘  └───┬──┘  └────┬──┘  └───┬──┘  └───┬──────┘
   │          │          │          │          │
└─────────────────────────────────────────────────────────┐
│  LAYER 3 — HANDOFF ARTIFACT (task-brief.md)             │
│  Shared markdown file each agent reads + appends        │
│  Carries intent → design → code plan → test results →  │
│  doc updates across the entire chain                    │
└─────────────────────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│  LAYER 4 — KNOWLEDGE BASE                               │
│  Spec files (what each app is)                          │
│  Skill files (how to do each class of work)             │
│  Agent role cards (guardrails per role)                 │
└─────────────────────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│  LAYER 5 — OUTPUTS                                      │
│  Git worktree branch (code)                             │
│  Updated spec file (contract)                           │
│  Unit tests (verification)                              │
│  Confluence page (documentation)                        │
└─────────────────────────────────────────────────────────┘
```

### 3.2 The Orchestrator

The orchestrator is not a "smart agent." It is a **router and sequencer**. Its jobs:
1. Parse the app target (rita / fno / ops) from the user's request
2. Select the matching spec + skill file
3. Create the task brief file
4. Spawn agents in the correct sequence, passing the task brief path to each
5. Report the final state to the user

The orchestrator does **not** make design decisions — that is the Architect agent's job.

### 3.3 The Task Brief — Inter-Agent Handoff Protocol

Each agent reads the task brief written by the previous agent, adds its own section, and saves it. The brief is a growing markdown document that becomes a complete audit trail.

**Structure:**

```markdown
# Task Brief — {timestamp}

## Request
{original user request, verbatim}

## App Target
{rita | fno | ops}

## Skill Selected
{path to skill file}

## Spec Reference
{path to relevant spec file}

---

## [PM] Validation
- Sprint alignment: {in scope / out of scope}
- Risk flags: {none | list}
- Approved to proceed: {yes / no}

---

## [Architect] Design
- Feature summary: {1-2 sentences}
- API contract: {method + path + request + response shape}
- Frontend target: {JS module + DOM element IDs}
- Files to touch: {table}
- Definition of Done: {checklist}

---

## [Engineer] Implementation Log
- Branch: {feature/branch-name}
- Files changed: {list}
- API contract verified: {yes}
- Spec updated: {yes / no — which file}

---

## [QA] Test Results
- Tests written: {n}
- Tests passed: {n}
- Coverage delta: {+/- n%}
- Contract check: {field list vs handler return — match / mismatch}

---

## [TechWriter] Documentation
- Confluence page updated: {URL}
- Spec file updated: {yes / no}
```

---

## 4. Orchestration Flow — Step by Step

### Trigger
User runs: `/enhance rita "Add volatility regime indicator to market signals"`

### Step 1 — Orchestrator (inline, no sub-agent)
1. Identify app from first argument: `rita`
2. Select skill: `skill-add-rita-feature.md` (or `skill-add-fno-feature.md` / `skill-add-ops-feature.md`)
3. Select spec: `Spec_RITA_App.md` + `Spec_JS_Code.md`
4. Create `project-office/task-briefs/task-brief-{timestamp}.md` with request header
5. Proceed to Step 2

### Step 2 — PM Agent (`general-purpose`)
**Reads:** PLAN_STATUS.md + task brief header
**Does:** Validates the request fits current sprint; flags blockers; writes `[PM] Validation` section to brief
**Outputs:** Task brief with PM section complete

### Step 3 — Architect Agent (`Plan` agent)
**Reads:** Task brief + relevant spec file excerpt (max 400 lines)
**Does:** Designs the API contract, identifies frontend DOM targets, lists files to touch
**Outputs:** Task brief with `[Architect] Design` section complete; this becomes the engineer's specification

### Step 4 — Engineer Agent (`general-purpose`, `isolation: "worktree"`)
**Reads:** Task brief (Architect section) + relevant skill file
**Does:** Implements code in the worktree branch; updates spec if contract changes
**Outputs:** Working code on a feature branch; task brief `[Engineer]` section complete

### Step 5 — QA Agent (`general-purpose`)
**Reads:** Task brief (Engineer section) + new code files
**Does:** Writes unit tests; verifies API-frontend contract; checks coverage
**Outputs:** Tests committed; task brief `[QA]` section complete

### Step 6 — TechWriter Agent (`general-purpose`)
**Reads:** Task brief (full) + Confluence guide
**Does:** Updates Confluence page for the affected app section; confirms spec is current
**Outputs:** Confluence updated; task brief `[TechWriter]` section complete; brief archived

### Final Report (Orchestrator)
Reads task brief summary; reports branch name + all quality gates passed to user.

---

## 5. App-to-Skill Routing Table

The orchestrator uses this table to select the correct skill for each app:

| App argument | Feature type | Skill selected | Spec loaded |
|---|---|---|---|
| `rita` | UI feature | `skill-add-rita-feature.md` | `Spec_RITA_App.md` + `Spec_JS_Code.md` |
| `fno` | UI feature | `skill-add-fno-feature.md` | `Spec_RITA_App.md` + `Spec_JS_Code.md` |
| `ops` | UI feature | `skill-add-ops-feature.md` | `Spec_RITA_App.md` + `Spec_JS_Code.md` |
| any | API endpoint | `skill-add-endpoint.md` | `Spec_Python_Code.md` + `Spec_DB.md` |
| any | DB model | `skill-add-db-model.md` | `Spec_DB.md` |
| any | Chat intent | `skill-add-chat-intent.md` | `Spec_Chat_Feature.md` |
| any | Data feature | `skill-add-data-feature.md` | `Spec_Data.md` |
| any | Bug fix | `fix-bug.md` | `Spec_JS_Code.md` |

---

## 6. Technology Stack

| Component | Technology | Role |
|---|---|---|
| **LLM** | Claude Sonnet 4.6 / Opus 4.7 | Reasoning, generation, tool use |
| **CLI harness** | Claude Code CLI | Executes agents, manages tools, sessions |
| **Agent spawning** | `Agent` tool (`general-purpose`, `Plan`) | Specialist agents invoked by orchestrator |
| **User interface** | Slash commands (`.claude/commands/`) | Single entry point — `/enhance`, `/fix-bug`, `/start-day` |
| **Knowledge base** | Spec files (`project-office/specs/`) | Domain knowledge per app/concern |
| **Agent memory** | Skill files (`project-office/skills/`) | Task rules pre-compiled — ~300 tokens vs ~4,000 for spec reads |
| **Handoff protocol** | Task brief (markdown file) | Inter-agent state; becomes audit trail |
| **Code isolation** | Git worktrees | Prevents engineer agents from polluting working tree |
| **Persistent memory** | `~/.claude/projects/.../memory/` | Cross-session learning — failure rules, feedback |
| **State tracking** | `PLAN_STATUS.md` | Sprint state; PM agent reads this |
| **CI verification** | `ruff check`, pytest, coverage | Quality gates each engineer agent must pass |
| **Documentation** | Confluence (`project-office/confluence/`) | TechWriter agent publishes here |

### Why Claude Code as the harness?

Claude Code provides the `Agent` tool natively — an orchestrator can spawn specialist agents as sub-processes, each with their own context window, tool access, and isolation. This is the key technical enabler. Without it, orchestration requires custom infrastructure.

For enterprise deployment, the same pattern runs on:
- Claude.ai/code (web)
- VS Code / JetBrains extension
- Scheduled routines via `CronCreate` (unattended operation)

---

## 7. Continuous Improvement — Training the Agents

In this architecture, "training" means **improving the knowledge layer** (skill files, spec files, orchestrator prompts) based on observed agent behaviour. The model weights are fixed; the context is what improves.

### 7.1 The Agent Training Loop

```
┌─────────────────────────────────────────────────────────┐
│  1. RUN                                                  │
│  Agent executes task using current skill file           │
└─────────────────────┬───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│  2. EVALUATE                                            │
│  Definition of Done checklist — pass / fail             │
│  Quality gates: ruff, tests, contract check, spec update│
└──────────┬──────────────────────────┬───────────────────┘
           │ pass                     │ fail
           │                          │
┌──────────▼──────┐        ┌──────────▼──────────────────┐
│  3a. RECORD WIN │        │  3b. DIAGNOSE FAILURE        │
│  If agent chose │        │  What context was missing?   │
│  a non-obvious  │        │  What rule was violated?     │
│  correct path,  │        │  What did the agent assume   │
│  add a positive │        │  that was wrong?             │
│  rule to skill  │        └──────────┬──────────────────┘
└─────────────────┘                   │
                           ┌──────────▼──────────────────┐
                           │  4. UPDATE                   │
                           │  Add rule to skill file      │
                           │  Add pitfall to agent card   │
                           │  Tighten orchestrator prompt │
                           └──────────┬──────────────────┘
                                      │
                           ┌──────────▼──────────────────┐
                           │  5. VERSION                  │
                           │  git commit: "skill: add     │
                           │  rule — [why it was added]"  │
                           │  Memory system updated       │
                           └─────────────────────────────┘
```

### 7.2 Three Improvement Targets

#### Target A — Skill Files (highest leverage)
Each skill file is a compiled ruleset. When an agent makes a mistake, the root cause is almost always a missing rule in the skill file. The fix is to add that rule so every future agent benefits.

**Rule: one failure = one new rule.**

Example: Engineer agent hardcoded `lot_size = 75` because the skill file didn't say where lot sizes come from.
→ Add to `skill-add-rita-feature.md`: "Never hardcode lot sizes — read from `settings.instruments.*`."

Over time, skill files accumulate a failure-mode library that prevents entire classes of mistakes.

#### Target B — Orchestrator Prompt
The orchestrator determines which skill + spec is selected for a given request. Failures here cause the wrong agent to be sent the wrong context.

**Improvement signals:**
- Agent chose wrong tier (system vs workflow vs experience endpoint)
- Wrong app's spec was loaded
- Architect section was too vague for Engineer to act on

**Fix:** Add routing rules or disambiguation questions to the orchestrator command.

#### Target C — Handoff Contract (task brief template)
If Engineer agents consistently misread Architect output, the handoff contract is under-specified.

**Fix:** Add required fields to the `[Architect] Design` section. Example: add "Edge cases to handle" as a required field after an agent missed a null-input scenario.

### 7.3 Improvement Metrics

Track these per task type over time. Improvement = lower cost, higher first-pass success.

| Metric | How to measure | Target |
|---|---|---|
| **Token cost per task** | Count tokens in task brief + agent context at end of session | Decrease session-to-session |
| **First-pass success rate** | Tasks where Definition of Done passed without user correction | > 85% |
| **Iteration count** | How many rounds before agent output was accepted | ≤ 2 |
| **Skill file staleness** | Days since skill file was last updated vs. days since spec changed | 0 drift |
| **Failure class distribution** | Which rule categories cause most failures (contract, guardrail, routing) | Shrinking set |

### 7.4 Improvement Cadence

| Cadence | Activity |
|---|---|
| **Every task** | If agent required correction, add rule to skill file before closing |
| **Every sprint** | Review task brief archive — identify top 3 failure classes; harden skill files |
| **Every release** | Audit spec files vs. actual code — skill files derived from stale specs produce stale context |
| **Quarterly** | Review orchestrator routing table — new app sections, new skill types, retired patterns |

### 7.5 Memory System Integration

The Claude Code memory system (`~/.claude/projects/.../memory/`) persists learning across sessions. Each feedback entry is stored as:

```markdown
---
name: feedback_[topic]
type: feedback
---
Rule: [what to do / not do]
Why: [the failure that caused this rule]
How to apply: [when this kicks in]
```

Memory entries complement skill files: memory applies *during this session*, skill files apply *inside each spawned agent*. Both must be updated when a new failure mode is discovered.

---

## 8. Scaling the Approach

### Adding a New App

To extend the orchestration to a new app (e.g. a fourth dashboard or a mobile feature):

1. Write `project-office/specs/Spec_NewApp.md` — domain knowledge, UI structure, API endpoints
2. Write `project-office/skills/skill-add-newapp-feature.md` — task rules compiled from the spec
3. Add one row to the orchestrator routing table in `/enhance` command
4. The entire agent chain works immediately for the new app

**Cost: ~2 hours of context authoring. Zero infrastructure change.**

### Adding a New Agent Role

Example: add a Security Reviewer agent between Engineer and QA.

1. Write `project-office/agents/security-reviewer.md` — role card with guardrails
2. Add `## [Security] Review` section to the task brief template
3. Add the agent spawn call to the orchestrator sequence

### Parallel Agent Execution

For independent tasks (e.g. FnO and Ops enhancements simultaneously), the orchestrator can spawn Engineer agents in parallel using background agent invocations. Each works in its own git worktree. QA and TechWriter run after both complete.

---

## 9. Implementation Roadmap

### Phase 1 — Orchestrator (next session, ~2 hours)

| Deliverable | Description |
|---|---|
| `/enhance` slash command | Orchestrator command: parses app + request, selects skill + spec, creates task brief, spawns agents in sequence |
| Task brief template | Standard markdown template file at `project-office/task-briefs/TEMPLATE.md` |
| `task-briefs/` directory | Archive folder for completed briefs |
| Updated orchestrator routing table | App → skill → spec mapping (inline in `/enhance` command) |

### Phase 2 — Per-App Skill Files (existing skills need review)

| Skill needed | Status |
|---|---|
| `skill-add-rita-feature.md` | Build from `Spec_RITA_App.md` + `Spec_JS_Code.md` |
| `skill-add-fno-feature.md` | Build from `Spec_RITA_App.md` + `Spec_JS_Code.md` (FnO section) |
| `skill-add-ops-feature.md` | Build from `Spec_RITA_App.md` + `Spec_JS_Code.md` (Ops section) |

### Phase 3 — Demo Hardening

| Activity | Description |
|---|---|
| End-to-end test run | Run `/enhance rita "..."` on a real small feature; record token cost and pass/fail |
| Failure mode capture | Add any failures as rules to skill files |
| Demo script | Document exact user input + expected agent output for enterprise presentation |

---

## 10. Enterprise Demo Script

**Setup:** Three apps visible in browser (RITA, FnO, Ops). Claude Code terminal visible.

**Narrative:** "We have a live trading system. A user wants a new feature. Instead of a developer sprint, a network of AI agents will plan, build, test, and document it in one session."

**Live command:**
```
/enhance fno "Add a net Greeks exposure summary (Delta, Gamma, Theta, Vega) to the portfolio overview panel"
```

**Walk through each agent phase as it runs:**
- Orchestrator: "It identifies the app, selects the right knowledge base"
- PM: "Validates it fits the current sprint — no blockers"
- Architect: "Designs the API contract and the exact DOM elements to update"
- Engineer: "Writes the endpoint and the JavaScript — in an isolated branch"
- QA: "Writes unit tests, verifies the API and frontend agree on field names"
- TechWriter: "Updates the product documentation automatically"

**Show:** The task brief as a complete audit trail. The feature branch ready to merge. The Confluence page updated.

**Key message:** "The skill files and spec files are the 'training' for these agents — every time an agent makes a mistake, we add a rule. The system gets smarter with every sprint."

---

## 11. Agent Operations System — Keeping Agents Grounded and Measurable

This section covers the second dimension of the enterprise approach: not just orchestrating agents, but **observing, validating, and improving them** as a continuous operational discipline. This is an emerging enterprise category — "AgentOps" — analogous to how DevOps monitors applications and MLOps monitors models.

### 11.1 Why Agents Drift (The Root Problem)

When you spawn an agent with instructions, the agent itself decides what to do next. A grounded system inverts this: **the orchestrator is the authority, not the agent**. Agents execute bounded tasks; the orchestrator validates output and gates progression to the next step.

Without this inversion, agents fail in three predictable ways:

| Drift Type | Example | Effect |
|---|---|---|
| **Role drift** | Engineer makes architectural decisions | Architect's design is bypassed |
| **Scope drift** | QA agent rewrites code instead of testing it | Engineer's work is silently overwritten |
| **Step drift** | Agent skips the Definition of Done checklist | Quality gate never runs; defect ships |

### 11.2 The Three-System Stack

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  GROUNDING      │───▶│  MONITORING     │───▶│  IMPROVEMENT    │
│                 │    │                 │    │                 │
│ Keep agents on  │    │ Measure what    │    │ Close the loop  │
│ defined process │    │ happened + why  │    │ Skill files     │
│                 │    │                 │    │ evolve from     │
│ Orchestrator as │    │ Dashboard +     │    │ failure data    │
│ authority       │    │ run logs        │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 11.3 Grounding — Keeping Agents On-Process

**Mechanism 1: Schema-validated task brief sections**

The orchestrator does not blindly pass the task brief to the next agent. It reads and validates each completed section first. Required fields must be present; if missing, the same agent is re-invoked with an explicit gap message.

```
Architect completes → Orchestrator reads [Architect] section
                    → Checks: API contract present? Files to touch listed? DoD checklist filled?
                    → PASS  → spawn Engineer
                    → FAIL  → re-invoke Architect: "section incomplete — missing: [field list]"
```

**Mechanism 2: Explicit role boundaries in every prompt**

Each agent prompt states what files it may and may not access. The skill file enforces this. An Engineer agent is told it cannot modify spec files (TechWriter's job); a QA agent is told it cannot modify source code (Engineer's job). This prevents scope drift.

**Mechanism 3: Mandatory Definition of Done check before handoff**

Every agent prompt ends with: *"Before completing, verify each item in the Definition of Done is checked. Write the result (pass/fail) for each item into your task brief section. Do not report complete if any item is unchecked."* The orchestrator reads this checklist — not just the agent's prose — before spawning the next agent.

**Mechanism 4: Orchestrator as gatekeeper (not passthrough)**

The orchestrator never auto-advances on agent completion alone. It reads the section, validates the schema, and makes an explicit gate decision. This is the single most important architectural choice: the workflow controls the agents, not the other way around.

### 11.4 Monitoring — The Agent Run Log

Every `/enhance` run produces a structured JSON log. This is the telemetry layer — no external SaaS required, no data leaving the environment.

**Log structure per run:**

```json
{
  "run_id": "20260429-1142",
  "app": "fno",
  "request": "Add Greeks summary to portfolio panel",
  "skill_file": "skill-add-fno-feature.md",
  "agents": [
    {
      "role": "architect",
      "status": "pass",
      "steps_required": 4,
      "steps_completed": 4,
      "adherence_score": 1.0,
      "token_estimate": 3200,
      "grounding_checks": {
        "api_contract_present": true,
        "files_to_touch_listed": true,
        "dod_checklist_filled": true
      },
      "failure_modes": []
    },
    {
      "role": "engineer",
      "status": "pass_with_warnings",
      "steps_required": 5,
      "steps_completed": 4,
      "adherence_score": 0.80,
      "token_estimate": 6100,
      "grounding_checks": {
        "spec_updated": false,
        "ruff_passed": true,
        "contract_verified": true,
        "worktree_used": true
      },
      "failure_modes": ["spec_not_updated"]
    }
  ],
  "overall_status": "pass_with_warnings",
  "total_tokens_estimated": 14800,
  "duration_minutes": 11,
  "branch": "feature/greeks-summary-fno"
}
```

**Log files location:** `project-office/agent-ops/runs/run-{timestamp}.json`

### 11.5 The AgentOps Dashboard — Visual Layer

A static HTML dashboard (`project-office/agent-ops/dashboard.html`) reads the JSON run logs directly — no server, no external dependency. Same technology pattern as RITA/FnO/Ops dashboards.

**Dashboard panels:**

| Panel | What it shows | Why it matters |
|---|---|---|
| **Pipeline Run History** | Timeline of each `/enhance` run — app, status, duration, branch | See overall throughput and failure rate at a glance |
| **Agent Scorecards** | Per-role: adherence rate, first-pass rate, avg token cost | Identify which agent role needs skill file work |
| **Grounding Score Trend** | % of validation checkpoints passed per run, over time | Shows whether grounding is improving sprint-to-sprint |
| **Failure Mode Heatmap** | Which failure types occur most, per agent role | Points directly to which skill file needs updating |
| **Token Cost Trend** | Estimated tokens per task type over time | Measures whether agents are becoming more efficient |
| **Skill File Version History** | When each skill file changed + quality metric before/after update | Closes the improvement loop visually |

### 11.6 The Improvement Loop — Closing the Feedback Cycle

The dashboard's most important feature: it surfaces which skill file to update and shows whether the update worked.

```
Dashboard: Engineer role → "spec_not_updated" in 3 of last 5 runs
        ↓
User identifies: skill-add-fno-feature.md missing explicit spec update rule
        ↓
Adds rule to skill file: "After changing any API contract, update specs/Spec_RITA_App.md
                          in the same task. Mark dod_item 'spec_updated' as true."
        ↓
Git commit: "skill(fno): enforce spec update — 3 failures sprint 3"
        ↓
Next 5 runs: 'spec_not_updated' failure disappears
        ↓
Dashboard: skill file v2 → zero 'spec_not_updated' failures
          (closed loop — improvement is measurable)
```

This is "training the agents" in practice: not fine-tuning model weights, but evolving the knowledge layer from failure evidence. The dashboard makes this process visible and auditable.

### 11.7 Market Context — Why This Is an Enterprise Use Case

The current market for agent monitoring (LangSmith, Arize AI, Datadog LLM Observability, AgentOps.ai) requires:
- External SaaS accounts and API keys
- Instrumentation code embedded in applications
- Trace data sent to a third-party cloud service

The embedded approach described here is different:

| Dimension | SaaS tools | This approach |
|---|---|---|
| Infrastructure | External cloud service | Local JSON + HTML |
| Data residency | Third-party servers | Stays in project repo |
| Instrumentation | Code changes in app | Task brief + orchestrator log |
| Cost | Per-trace pricing | Zero — reads existing artifacts |
| Audit trail | Vendor-managed | Git-versioned, project-owned |
| Customisation | Limited to vendor UI | Full control — HTML dashboard |

**Enterprise buyers care about:** audit trails for compliance, performance measurement for ROI justification, governance for risk management, and data residency for security. This approach addresses all four without external dependency.

This positions as a reusable pattern: any enterprise deploying Claude Code agents for business process automation can adopt the same stack — task brief + run logs + HTML dashboard — without building custom infrastructure or signing SaaS contracts.

### 11.8 Build Plan for the AgentOps System

Three deliverables, sequenced:

| Phase | Deliverable | Effort |
|---|---|---|
| **A** | `/enhance` orchestrator with grounding validation + run log writer | ~3 hours |
| **B** | `project-office/agent-ops/dashboard.html` — reads JSON logs, shows all 6 panels | ~3 hours |
| **C** | Failure catalog + skill file linkage — dashboard links failure types to skill files | ~1 hour |

Phase A is the prerequisite — it generates the data that Phase B visualises. Phase C adds the improvement loop closure on top of Phase B.

---

## 12. File Locations Reference

```
project-office/
├── agents/
│   ├── Agentic_AI_Enterprise_Approach.md  ← this document
│   ├── {role}.md                          ← agent role cards (guardrails per role)
│   └── prompts/                           ← complex agent prompt templates
├── specs/
│   └── Spec_*.md                          ← domain knowledge (one per app/concern)
├── skills/
│   └── skill-*.md                         ← compiled task rules (one per work class)
├── task-briefs/
│   ├── TEMPLATE.md                        ← task brief template
│   └── task-brief-{timestamp}.md          ← completed brief archive (audit trail)
└── agent-ops/                             ← AgentOps system (Phase A/B/C)
    ├── dashboard.html                     ← visual monitoring dashboard
    ├── metrics.json                       ← aggregated metrics over time
    ├── failure-catalog.md                 ← categorised failure modes + skill file links
    └── runs/
        └── run-{timestamp}.json           ← per-run structured log

riia-cowork-jun/
└── .claude/commands/
    ├── enhance.md                         ← orchestrator command (Phase 1)
    ├── engineer-task.md                   ← single-agent engineer (existing)
    ├── fix-bug.md                         ← bug trace command (existing)
    ├── start-day.md                       ← PM daily command (existing)
    └── end-day.md                         ← end-of-day routine (existing)
```
