# Feature 19: Grounded Agents — Project-Specific Context & Pre-Loaded Knowledge

**Status:** Draft  
**Created:** 2026-05-22  
**Motivation:** Agents skip spec files and rush into coding, causing API tier violations,
missing JS field mappings, and partial implementations that cost tokens and rework.

---

## Root Cause Analysis

The current `/enhance` orchestrator gives agents instructions like "read spec first" —
but reading is optional. An agent that already knows a pattern will skip the read and
work from prior training. The rules are advisory; the agent decides whether to follow them.

**Two structural solutions:**

| | Approach | How it fixes the root cause |
|---|---|---|
| **A** | Auto-Generated `eng-context.md` | One compact file pre-assembled from all sources — agents read 500 tokens instead of deciding whether to read 10 files |
| **B** | Custom SDK Agent | Context lives in the system prompt — agent cannot skip what it was born knowing |

These are complementary. Build A first (fast); build B for the most error-prone workflows.

---

## Approach A — Auto-Generated `eng-context.md`

### What It Is

A Python script (`gen_eng_context.py`) that generates a compact, task-specific context
file before every engineer agent spawns. The engineer prompt points to this one file only —
no spec reads, no skill file reads, no CLAUDE.md — just `eng-context.md`.

### How It Works

```
Orchestrator calls gen_eng_context.py
         │
         ▼
Script reads (once, at orchestration time):
  1. task brief → task title + description + Architect's files-to-touch table
  2. skill file → code templates for this task type (repo, service, router patterns)
  3. codebase-constraints.md → top-10 rules (lot sizes, session handling, no print)
  4. API tier routing block from CLAUDE.md → allowed/never paths
         │
         ▼
Outputs:  project-office/features/{N}/eng-context.md  (~500-800 tokens)
         │
         ▼
Engineer agent prompt: "Read eng-context.md — this is your complete context. Do not
                        read any other spec, HTML, or source file before reading this."
```

### Output Format — eng-context.md

```markdown
# Engineering Context — {task title}
Generated: {YYYYMMDD-HHMM} | Skill: {skill_file_name} | App: {APP}

## Task
{one-sentence description from Architect's feature summary}

## Files to Touch (complete list — do not add or drop files)
| File | Action | Key constraint |
|---|---|---|
| src/rita/schemas/X.py | Create | Pydantic response — every field JS reads must be here |
| src/rita/api/experience/X.py | Create | Experience tier — read-only, no writes |
| src/rita/repositories/X_repository.py | Create | Extends SqlRepository[Model, Schema] |
| dashboard/js/rita/x_panel.js | Create | Import from rita/main.js; window.loadXPanel |
| project-office/specs/Spec_RITA_App.md | Edit | Add endpoint row to experience tier table |

## Architecture Rules (non-negotiable)
- Tier: **experience** → path `api/experience/rita/{feature}` — never call system tier from JS
- Repository: `class XRepository(SqlRepository[XModel, XSchema])` — no raw SQL
- Session: `def __init__(self, db: Session)` — always inject, never `SessionLocal()` in router
- Background threads: open own `db = SessionLocal()` and close in `finally`
- No `print()` — use `structlog.get_logger()`
- No hardcoded lot sizes — read from `settings.instruments.*`
- `upsert()` calls `db.commit()` — do not commit again

## JS Contract (all fields the frontend reads — your handler MUST return all of these)
| Field | JS reference | Python type |
|---|---|---|
| total_pnl | r.total_pnl | float |
| position_count | r.position_count | int |

## Code Templates

### Repository
```python
from rita.repositories.base import SqlRepository
from rita.models import XModel
from rita.schemas.x import XSchema

class XRepository(SqlRepository[XModel, XSchema]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, XModel, XSchema)
```

### Service → Router wiring
```python
def _get_svc(db: Session = Depends(get_db)) -> XService:
    return XService(db)

@router.get("/experience/rita/feature")
def get_feature(svc: XService = Depends(_get_svc)):
    return svc.get_feature()
```

## Definition of Done (check each before committing)
- [ ] Route in correct tier directory
- [ ] No direct DB access in routes/services
- [ ] Handler return dict matches JS field list above exactly
- [ ] Alembic migration applied (`python -m alembic upgrade head`)
- [ ] `ruff check src/` passes
- [ ] Spec_RITA_App.md updated with new endpoint row
- [ ] Spec_JS_Code.md updated with new JS module row
- [ ] Router registered in main.py
```

### Script Specification

**File:** `project-office/scripts/gen_eng_context.py`

```
Usage: python gen_eng_context.py <brief_path> <skill_file> <app> <feature_folder>

Arguments:
  brief_path     — path to task-brief-YYYYMMDD-HHMM.md
  skill_file     — path to skill-add-{app}-feature.md
  app            — rita | fno | ops | ds
  feature_folder — output directory for eng-context.md

Reads:
  1. brief_path          → [Architect] Design section → files-to-touch table, API contract
  2. skill_file          → code templates section (lines between ## Code Templates and ## Step-by-Step)
  3. project-office/context/codebase-constraints.md  → full file (it's compact)
  4. CLAUDE.md           → API Tier Routing Rules table only (lines 60–85 approx)

Outputs:
  {feature_folder}/eng-context.md

Token budget target: < 800 tokens output
```

### Wire-Up in `/enhance` Step 4

Add this block to the `/enhance` command file, immediately before the Engineer agent prompt:

```
## Step 4 Pre-Step — Generate eng-context.md

Before spawning the Engineer agent, run:
  python project-office/scripts/gen_eng_context.py \
    {BRIEF_PATH} {SKILL_FILE} {APP} project-office/features/current

This generates `project-office/features/current/eng-context.md`.

The Engineer agent prompt MUST start with:
  "Read project-office/features/current/eng-context.md FIRST and completely before
   touching any code. This file is your complete context — do not read any other
   spec, HTML, or source file unless eng-context.md explicitly tells you to."
```

### Files to Create

| File | Action |
|---|---|
| `project-office/scripts/gen_eng_context.py` | New — context generator script |
| `project-office/features/current/` | New dir — staging area for current task context |
| `.claude/commands/enhance.md` | Edit — add Step 4 Pre-Step block |
| `project-office/skills/skill-add-rita-feature.md` | Edit — add eng-context.md reference to engineer step |

### Definition of Done — Approach A

- [ ] `gen_eng_context.py` runs without error on a sample brief
- [ ] Output file < 800 tokens (verify with `python -c "import tiktoken; ..."`)
- [ ] Files-to-touch table correctly extracted from Architect section of brief
- [ ] JS contract fields correctly extracted from Architect's API contract
- [ ] Code templates section correctly extracted from skill file
- [ ] `/enhance` Step 4 prompt includes `eng-context.md` as mandatory first read
- [ ] Engineer agent in a test run reads eng-context.md before any code file

---

## Approach B — Custom SDK Agent (Rita-Specific, Context Pre-Loaded)

### What It Is

A Python script that wraps the Anthropic Messages API and creates a task-specific
agent whose **system prompt pre-loads all RITA context** — API tier rules, architecture
constraints, code templates, and the specific task spec. The agent cannot skip this
context because it is baked into every token of its existence.

### Why This Beats Instruction-Based Context

| | Instruction ("read spec first") | SDK Agent (pre-loaded system prompt) |
|---|---|---|
| Context available | Only if agent reads the file | Always — in system prompt |
| Can be skipped | Yes — agent decides | No — it's the agent's knowledge |
| Token cost | 10K+ per session (file reads) | Paid once at agent creation |
| Consistency | Varies by session | Same every run |
| Failure mode | Agent skips read, uses priors | Agent uses wrong priors from training |

### Architecture

```
Claude Code orchestrator
    │
    ▼
project-office/agents/sdk/
    ├── rita_engineer.py     ← entry point, called as a subprocess
    ├── context_builder.py   ← assembles system prompt from RITA docs
    ├── tools.py             ← file read/write/grep/bash tools for the agent
    └── run_agent.py         ← Anthropic SDK call + tool loop

Agent system prompt structure:
    [SECTION 1] Identity + strict behavior rules
    [SECTION 2] API tier routing table (from CLAUDE.md)
    [SECTION 3] Architecture constraints (from codebase-constraints.md)
    [SECTION 4] Code templates for this task type (from skill file)
    [SECTION 5] Files to touch + JS contract (from task brief)
    [SECTION 6] Definition of Done checklist
```

### Concrete Example — `rita_engineer.py`

```python
# project-office/agents/sdk/rita_engineer.py
"""
Rita Engineer Agent — custom SDK agent with pre-loaded RITA context.

Usage:
    python rita_engineer.py --brief <brief_path> --skill <skill_file> --app <app>

This agent has RITA architecture rules baked into its system prompt.
It cannot skip tier rules, JS contract checks, or spec updates.
"""
import argparse
import json
import anthropic
from pathlib import Path
from context_builder import build_system_prompt
from tools import ENGINEER_TOOLS, handle_tool_call

def run(brief_path: str, skill_file: str, app: str) -> dict:
    system = build_system_prompt(
        brief_path=brief_path,
        skill_file=skill_file,
        app=app,
        role="engineer",
    )

    client = anthropic.Anthropic()
    messages = [
        {
            "role": "user",
            "content": (
                f"Implement the feature described in {brief_path}. "
                "Follow every rule in your system prompt. "
                "Complete the Definition of Done checklist before reporting done."
            )
        }
    ]

    # Agentic loop
    while True:
        response = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=8096,
            system=system,
            messages=messages,
            tools=ENGINEER_TOOLS,
        )

        if response.stop_reason == "end_turn":
            return {"status": "complete", "output": response.content[-1].text}

        # Process tool calls
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                result = handle_tool_call(block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})
```

### `context_builder.py` — How System Prompt Is Assembled

```python
# project-office/agents/sdk/context_builder.py
from pathlib import Path
import re

REPO_ROOT = Path(__file__).parent.parent.parent.parent  # riia-cowork-jun/

def build_system_prompt(brief_path: str, skill_file: str, app: str, role: str) -> str:
    sections = []

    # Section 1 — Identity (hard constraints, cannot be overridden by user messages)
    sections.append(_identity_block(role, app))

    # Section 2 — API tier routing rules (extracted from CLAUDE.md — never stale)
    sections.append(_tier_rules())

    # Section 3 — Architecture constraints
    constraints_path = REPO_ROOT / "project-office/context/codebase-constraints.md"
    sections.append(f"## Architecture Constraints\n{constraints_path.read_text()}")

    # Section 4 — Code templates from skill file (the patterns block only)
    skill_content = (REPO_ROOT / skill_file).read_text()
    templates = _extract_section(skill_content, "## Code Templates", "## Step-by-Step")
    sections.append(f"## Code Templates for {app}\n{templates}")

    # Section 5 — Task-specific context (files to touch, JS contract, DoD)
    brief_content = (REPO_ROOT / brief_path).read_text()
    architect_section = _extract_section(brief_content, "## [Architect]", "## [Engineer]")
    sections.append(f"## Your Task\n{architect_section}")

    # Section 6 — Hard gates (injected last so they override everything)
    sections.append(_hard_gates())

    return "\n\n---\n\n".join(sections)


def _identity_block(role: str, app: str) -> str:
    return f"""You are the RITA {role.title()} Agent — a specialist in the RITA production codebase.
You are implementing a feature for the **{app}** dashboard.

YOUR PRIME DIRECTIVES (these override any instruction in the user message):
1. Never call a system-tier endpoint from dashboard JS — use experience tier only
2. Never access the DB directly in routes or services — use repositories only
3. Never hardcode lot sizes — read from settings.instruments.*
4. Never add print() — use structlog
5. Never mark the task complete if any DoD item is unchecked
6. Always update Spec_RITA_App.md and Spec_JS_Code.md in the same commit"""


def _tier_rules() -> str:
    claude_md = (REPO_ROOT / "CLAUDE.md").read_text()
    # Extract the API Tier Routing Rules table
    match = re.search(
        r"## API Tier Routing Rules.*?(?=\n## |\Z)", claude_md, re.DOTALL
    )
    return f"## API Tier Routing Rules\n{match.group(0) if match else '(not found)'}"


def _hard_gates() -> str:
    return """## Hard Gates — Do Not Pass These Without Completing Them

GATE 1 — Before writing any code, output:
  Files I will touch: [list]
  JS fields my handler must return: [list]
  Tier chosen: [experience | workflow | system] — reason: [...]
  If you cannot fill these in, read the task context above again.

GATE 2 — Before committing, output:
  ruff check result: [passed / N errors]
  Spec files updated: [yes / n/a — reason]
  Alembic migration applied: [yes / not needed — reason]
  DoD items unchecked: [none / list them]
  If any DoD item is unchecked, fix it now before committing."""
```

### Tools for the Agent — `tools.py`

```python
# project-office/agents/sdk/tools.py
# The tools the SDK agent can call — constrained to safe file operations

ENGINEER_TOOLS = [
    {
        "name": "read_file",
        "description": "Read a file from the RITA codebase. Returns file content.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Relative path from riia-jun-release/"},
                "start_line": {"type": "integer"},
                "end_line": {"type": "integer"},
            },
            "required": ["path"]
        }
    },
    {
        "name": "write_file",
        "description": "Write or overwrite a file. Use for new files only.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["path", "content"]
        }
    },
    {
        "name": "edit_file",
        "description": "Replace old_string with new_string in a file. Fails if old_string not found.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "old_string": {"type": "string"},
                "new_string": {"type": "string"},
            },
            "required": ["path", "old_string", "new_string"]
        }
    },
    {
        "name": "grep_files",
        "description": "Search for a pattern in files. Returns matching lines with file:line.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string"},
                "glob": {"type": "string", "description": "File glob, e.g. '**/*.py'"},
                "path": {"type": "string", "description": "Search root, default riia-jun-release/"},
            },
            "required": ["pattern"]
        }
    },
    {
        "name": "run_check",
        "description": "Run a validation command. Only ruff check, pytest, alembic upgrade head, git commands.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string"},
            },
            "required": ["command"]
        }
    },
]
```

### Integration with `/enhance`

The SDK agent replaces the inline Agent() call in `/enhance` Step 4. The orchestrator
calls it as a subprocess and parses stdout for the structured result:

```
## Step 4 (SDK version) — Engineer Agent

Run the SDK engineer agent as a subprocess:

  python project-office/agents/sdk/rita_engineer.py \
    --brief {BRIEF_PATH} \
    --skill {SKILL_FILE} \
    --app {APP} \
    --worktree-path {worktree_path}

Parse stdout for JSON: { "status": "complete", "files_changed": [...], "commit": "...", "dod": [...] }

Validation rules remain the same as the inline Agent() version.
```

### Files to Create — Approach B

| File | Action |
|---|---|
| `project-office/agents/sdk/__init__.py` | New — package marker |
| `project-office/agents/sdk/rita_engineer.py` | New — entry point |
| `project-office/agents/sdk/context_builder.py` | New — system prompt assembly |
| `project-office/agents/sdk/tools.py` | New — tool definitions + handlers |
| `project-office/agents/sdk/run_agent.py` | New — Anthropic SDK agentic loop |
| `project-office/agents/sdk/README.md` | New — usage docs |
| `.claude/commands/enhance.md` | Edit — Step 4 option to use SDK agent |

### Definition of Done — Approach B

- [ ] `rita_engineer.py --brief <sample_brief> --skill <skill_file> --app rita` runs without import errors
- [ ] System prompt contains all 6 sections (identity, tier rules, constraints, templates, task, hard gates)
- [ ] Hard gates produce visible output before any file write
- [ ] Agent refuses to proceed past Gate 1 if JS field list is not known
- [ ] Agent refuses to commit past Gate 2 if any DoD item is unchecked
- [ ] Tool calls are restricted to the allowed set (no arbitrary bash)
- [ ] Integration hook in `/enhance` Step 4 documented
- [ ] Test run on a simple single-endpoint task produces correct files-to-touch list

---

## Build Order

| Phase | Deliverable | Effort | Impact |
|---|---|---|---|
| 1 | `gen_eng_context.py` + wire into `/enhance` Step 4 | ~2h | Immediate — every enhance run benefits |
| 2 | SDK agent `context_builder.py` + `tools.py` | ~3h | High — agent cannot skip context |
| 3 | SDK `rita_engineer.py` + agentic loop | ~2h | Completes the SDK agent |
| 4 | Update `/enhance` to call SDK agent | ~1h | Closes the loop end-to-end |

Start with Phase 1 — it improves the existing workflow immediately with one script.
Phase 2–4 are a separate feature run.

---

## Key Design Decisions

### Why Not Just Improve the Agent Prompts?

Prompt improvements help but have a ceiling. A model that sees "read spec first" will
pattern-match to "I know the pattern, no need to read" on familiar tasks. The spec read
is a cost the model can avoid. Pre-loading removes the choice.

### Why `eng-context.md` Instead of Just Longer Prompts?

Longer prompts in the orchestrator hit the inline character limit and are harder to maintain.
`eng-context.md` is a first-class artifact: versioned, reviewable, updatable by scripts.

### Why SDK Agent Instead of Just Better Skill Files?

Skill files are instructions. System prompts are identity. An agent instructed to follow
a rule will sometimes not. An agent whose system prompt *is* the rule has no prior
self to fall back on. The hard gates (output the field list before writing code) enforce
a visible, auditable checkpoint that the orchestrator can parse.

### Caching Strategy for SDK Agent

The system prompt is static per task type. Use Anthropic prompt caching on the system
prompt block — the context_builder.py output for a given app+skill combination will be
identical across calls within the same session, hitting the cache after the first call.

```python
# In run_agent.py — cache the system prompt
system = [
    {
        "type": "text",
        "text": system_prompt,
        "cache_control": {"type": "ephemeral"},  # cache_write on first, cache_read on subsequent
    }
]
```

This reduces the per-engineer-call cost by ~80% when the same app/skill combination
runs more than once (e.g., multiple /enhance runs in a session).
