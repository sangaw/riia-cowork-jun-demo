"""
Publishes the Agent Skill System approach to Confluence.
Parent: How We Work (65241125)
Run: python -m project_office.confluence.pages.publish_skill_system
"""
import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from confluence.publish import ConfluenceClient, SECTION

TITLE = "Agent Skill System — Token-Efficient Workflow"

HTML = """
<h1>Agent Skill System</h1>
<p><strong>Created:</strong> 2026-04-23 &nbsp;|&nbsp; <strong>Status:</strong> Approved — ready to implement</p>
<p>
  This document captures the design for a three-layer agent skill system that reduces per-session
  token cost from ~25,000 tokens (multi-spec reads) to ~5,000 tokens (single skill-file reads).
</p>

<h2>Problem: Where Tokens Are Lost</h2>
<p>Each engineer session burns 15,000–25,000 tokens <em>before the first line of code</em>:</p>
<table>
  <thead><tr><th>Step</th><th>Tokens</th></tr></thead>
  <tbody>
    <tr><td>CLAUDE.md auto-load</td><td>~1,500</td></tr>
    <tr><td>PLAN_STATUS.md read</td><td>~1,000</td></tr>
    <tr><td>3–5 spec files read</td><td>~8,000–12,000</td></tr>
    <tr><td>Source file slices</td><td>~4,000–8,000</td></tr>
    <tr><td><strong>Total before acting</strong></td><td><strong>~15,000–25,000</strong></td></tr>
  </tbody>
</table>
<p>
  Root cause: agent cards describe <em>roles</em>, not <em>tasks</em>. Every session the agent
  rediscovers the same rules from the same spec files.
</p>

<h2>Solution: Three-Layer Skill System</h2>

<h3>Layer 1 — Custom Slash Commands (<code>.claude/commands/</code>)</h3>
<p>
  Claude Code auto-loads <code>*.md</code> files from <code>.claude/commands/</code> as project
  slash commands. Invoke as <code>/start-day</code>, <code>/engineer-task</code>,
  <code>/end-day</code> — no typing long agent prompts.
</p>
<table>
  <thead><tr><th>Command file</th><th>Invoked as</th><th>Does</th></tr></thead>
  <tbody>
    <tr><td><code>start-day.md</code></td><td><code>/start-day</code></td><td>Reads PLAN_STATUS.md, reports today's tasks, asks which to start</td></tr>
    <tr><td><code>engineer-task.md</code></td><td><code>/engineer-task &lt;description&gt;</code></td><td>Scoped engineer agent with inline rules — no spec reads</td></tr>
    <tr><td><code>end-day.md</code></td><td><code>/end-day</code></td><td>Runs all 4 end-of-day steps in sequence</td></tr>
    <tr><td><code>fix-bug.md</code></td><td><code>/fix-bug &lt;description&gt;</code></td><td>JS→API→DOM trace protocol, no server start</td></tr>
  </tbody>
</table>

<h3>Layer 2 — Task Skill Files (<code>project-office/skills/</code>)</h3>
<p>
  One file per <em>class of work</em> — pre-merging everything the agent needs.
  Agent reads ONE skill file (~300 tokens) instead of FOUR spec files (~4,000 tokens).
</p>
<table>
  <thead><tr><th>Skill file</th><th>Used when</th><th>Replaces reading</th></tr></thead>
  <tbody>
    <tr><td><code>skill-add-api-endpoint.md</code></td><td>Adding any new FastAPI route</td><td>Spec_Python_Code + ADR-001 + ADR-002 + JS contract rules</td></tr>
    <tr><td><code>skill-fix-js-bug.md</code></td><td>Debugging a frontend defect</td><td>Spec_JS_Code + JS pitfall table + debug trace protocol</td></tr>
    <tr><td><code>skill-add-db-model.md</code></td><td>New SQLAlchemy model + repo</td><td>Spec_DB + SqlRepository contract + migration commands</td></tr>
    <tr><td><code>skill-add-chat-intent.md</code></td><td>New chat classifier intent</td><td>Spec_Chat_Feature + intent→handler pattern</td></tr>
    <tr><td><code>skill-end-of-day.md</code></td><td>End-of-day routine</td><td>PM card — all 4 steps inline</td></tr>
  </tbody>
</table>

<h3>Layer 3 — Agent Prompt Templates (<code>project-office/agents/prompts/</code>)</h3>
<p>
  Complete, ready-to-use <code>Agent()</code> call prompts. User fills in <code>$TASK</code>,
  pastes the rest. Eliminates re-explaining context per session for complex multi-agent tasks.
</p>

<h2>Build Order</h2>

<h3>Phase 1 — Next Session</h3>
<ol>
  <li>Create <code>.claude/commands/engineer-task.md</code></li>
  <li>Create <code>.claude/commands/start-day.md</code></li>
  <li>Create <code>.claude/commands/end-day.md</code></li>
  <li>Create <code>project-office/skills/skill-add-api-endpoint.md</code></li>
</ol>

<h3>Phase 2</h3>
<ol>
  <li>Create <code>project-office/skills/skill-fix-js-bug.md</code></li>
  <li>Create <code>project-office/skills/skill-add-db-model.md</code></li>
  <li>Create <code>.claude/commands/fix-bug.md</code></li>
</ol>

<h3>Phase 3</h3>
<ol>
  <li><code>skill-add-chat-intent.md</code></li>
  <li><code>skill-end-of-day.md</code></li>
  <li>Agent prompt templates in <code>project-office/agents/prompts/</code></li>
</ol>

<h2>Skill File Template</h2>
<pre>
# Skill: &lt;Task Name&gt;

## When to use this skill
&lt;1-2 sentences — the class of work this covers&gt;

## Pre-conditions
- [ ] &lt;what must be true before acting&gt;

## Rules (inline — do not read spec files)
### Rule 1: &lt;name&gt;
&lt;rule text — condensed from spec&gt;

## Step-by-step
1. &lt;action&gt;
2. &lt;action&gt;

## Files to touch
| File | Action |
|---|---|
| path/to/file.py | Create/Edit — what to add |

## Definition of Done
- [ ] &lt;checklist item&gt;
- [ ] Spec file updated if API contract changed
</pre>

<h2>Token Budget Impact (Estimated)</h2>
<table>
  <thead><tr><th>Session type</th><th>Before skills</th><th>After skills</th><th>Saving</th></tr></thead>
  <tbody>
    <tr><td>Engineer — add endpoint</td><td>~22,000</td><td>~7,000</td><td>~68%</td></tr>
    <tr><td>Engineer — fix JS bug</td><td>~18,000</td><td>~5,000</td><td>~72%</td></tr>
    <tr><td>End of day</td><td>~12,000</td><td>~4,000</td><td>~67%</td></tr>
    <tr><td>Architect — new ADR</td><td>~25,000</td><td>~8,000</td><td>~68%</td></tr>
  </tbody>
</table>

<h2>Maintenance Rule</h2>
<p>
  When a spec file changes (new API contract, schema change, pattern update):
</p>
<ol>
  <li>Update the relevant spec file (existing Definition of Done rule)</li>
  <li><strong>Also update the relevant skill file</strong> — skills are derived from specs</li>
</ol>
<p>
  Skill files go stale if only the spec is updated. Both must be updated in the same commit.
</p>

<h2>Files Created</h2>
<ul>
  <li><code>project-office/agents/SKILL_SYSTEM_APPROACH.md</code> — local copy of this design</li>
  <li><code>project-office/confluence/pages/publish_skill_system.py</code> — this publish script</li>
</ul>
"""


def main():
    client = ConfluenceClient()
    page_id, url = client.create_page(
        title=TITLE,
        body_html=HTML,
        parent_id=SECTION["how_we_work"],
    )
    print(f"Published: {url}")


if __name__ == "__main__":
    main()
