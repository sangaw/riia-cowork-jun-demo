"""
Publish 3 new Confluence pages:
  1. Sprint Planning & Metrics
  2. Claude Cowork vs Human Team -- The Case For It
  3. Claude Cowork Setup Guide (technical)
"""
import urllib.request, urllib.error, json, base64, time, os
from pathlib import Path

def _load_token():
    if os.environ.get("CONFLUENCE_API_TOKEN"):
        return os.environ["CONFLUENCE_API_TOKEN"]
    key_file = Path(__file__).parent.parent.parent.parent / "confluence-api-key.txt"
    if key_file.exists():
        return key_file.read_text().strip()
    raise RuntimeError("Set CONFLUENCE_API_TOKEN env var or place token in project root confluence-api-key.txt")

EMAIL = os.environ.get("CONFLUENCE_EMAIL", "")
TOKEN = _load_token()
BASE  = os.environ.get("CONFLUENCE_BASE_URL", "https://ravionics.atlassian.net/wiki/rest/api")
SPACE = os.environ.get("CONFLUENCE_SPACE_KEY", "RIIAProjec")
PARENT = "65110332"

CREDS = base64.b64encode(f"{EMAIL}:{TOKEN}".encode()).decode()
HEADERS = {
    "Authorization": f"Basic {CREDS}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

def create_page(title, body_html, parent_id=PARENT):
    payload = {
        "type": "page", "title": title,
        "space": {"key": SPACE},
        "ancestors": [{"id": parent_id}],
        "body": {"storage": {"value": body_html, "representation": "storage"}}
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(f"{BASE}/content", data=data, headers=HEADERS, method="POST")
    try:
        with urllib.request.urlopen(req) as r:
            result = json.load(r)
            url = f"https://ravionics.atlassian.net/wiki{result['_links']['webui']}"
            print(f"  CREATED [{result['id']}] '{title}'\n  {url}")
            return result["id"], url
    except urllib.error.HTTPError as e:
        print(f"  FAILED '{title}': HTTP {e.code} -- {json.loads(e.read())['message'][:120]}")
        return None, None

# ─────────────────────────────────────────────────────────────────────────────
# PAGE 1: Sprint Planning & Metrics
# ─────────────────────────────────────────────────────────────────────────────
SPRINT_PLANNING = """
<h1>Sprint Planning &amp; Metrics</h1>
<p><strong>Version:</strong> 1.0 &nbsp;|&nbsp; <strong>Date:</strong> 2026-03-30</p>

<h2>Tooling Decision: Jira vs Confluence</h2>
<p>Your Atlassian account (<code>ravionics.atlassian.net</code>) has <strong>Jira Product Discovery</strong> active but not Jira Software. Jira Product Discovery is designed for roadmaps and idea capture, not sprint execution. For this project we will use:</p>
<table>
  <tbody>
    <tr><th>Need</th><th>Tool</th><th>Why</th></tr>
    <tr><td>Sprint board &amp; task status</td><td><strong>Confluence page (this space)</strong></td><td>Already connected, no extra cost, updated by PM agent automatically</td></tr>
    <tr><td>Daily task tracking</td><td><strong>PLAN_STATUS.md</strong> (git file)</td><td>Lives in the repo; read by agents at session start; versioned with the code</td></tr>
    <tr><td>Roadmap &amp; priorities</td><td><strong>Master Plan page</strong> (Confluence)</td><td>Published and maintained by Technical Writer agent</td></tr>
    <tr><td>Bug / defect tracking</td><td><strong>PLAN_STATUS.md blockers section</strong></td><td>Lightweight; QA agent writes defects, PM agent tracks resolution</td></tr>
  </tbody>
</table>
<p style="background:#fff8e1;border-left:4px solid #FFC107;padding:10px;">
<strong>Upgrade path:</strong> If you add Jira Software to your Atlassian plan later, the PM agent can be updated to create Jira issues via the REST API using the same credentials. The workflow does not change.
</p>

<h2>Sprint Ceremonies (Adapted for AI Team)</h2>
<p>Traditional Agile ceremonies are adapted for a single human decision-maker + AI agent team. No standups, no scheduling. All ceremonies are triggered by you with a single command.</p>
<table>
  <tbody>
    <tr><th>Ceremony</th><th>Traditional</th><th>RITA Cowork Version</th><th>Trigger</th><th>Duration</th></tr>
    <tr>
      <td><strong>Sprint Planning</strong></td>
      <td>2-4 hour meeting, whole team</td>
      <td>PM agent reads PLAN_STATUS.md and produces the sprint task list with priorities, dependencies, and token budget estimate</td>
      <td><code>Start Sprint N</code></td>
      <td>~5 min (you review + approve)</td>
    </tr>
    <tr>
      <td><strong>Daily Standup</strong></td>
      <td>15 min meeting, each person reports</td>
      <td>Claude reads PLAN_STATUS.md and reports: what was done yesterday, what's planned today, any blockers</td>
      <td><code>Start Day N</code></td>
      <td>~2 min</td>
    </tr>
    <tr>
      <td><strong>Sprint Review</strong></td>
      <td>Demo to stakeholders</td>
      <td>Technical Writer publishes sprint summary to Confluence; you review the page and confirm sprint close</td>
      <td><code>End Sprint N</code></td>
      <td>~10 min (you read + confirm)</td>
    </tr>
    <tr>
      <td><strong>Retrospective</strong></td>
      <td>Team reflection on process</td>
      <td>PM agent reads all of the sprint's PLAN_STATUS entries and produces a retro report: what worked, what slowed us down, token budget analysis</td>
      <td><code>Retro Sprint N</code></td>
      <td>~5 min (you read)</td>
    </tr>
  </tbody>
</table>

<h2>Sprint Board Structure (Confluence)</h2>
<p>Each sprint gets its own Confluence page under this space with a live task board. The Technical Writer agent creates and updates it. Structure:</p>
<pre>
Sprint N -- [Name]
  Status: IN PROGRESS | COMPLETE
  Period: Day X to Day Y

  [ ] = To Do   [~] = In Progress   [x] = Done   [!] = Blocked

  BACKLOG
    [ ] Task description | Owner: Agent | Depends on: -

  IN PROGRESS
    [~] Task description | Owner: Engineer B | Started: Day N

  DONE
    [x] Task description | Owner: Architect | Completed: Day N | Reviewer: APPROVED

  BLOCKERS
    [!] Blocker description | Raised: Day N | Resolution: pending
</pre>

<h2>Metrics We Track</h2>
<table>
  <tbody>
    <tr><th>Metric</th><th>What it measures</th><th>Target</th><th>Updated by</th></tr>
    <tr>
      <td><strong>Task Completion Rate</strong></td>
      <td>% of planned tasks completed per sprint</td>
      <td>90%+</td>
      <td>PM agent at sprint end</td>
    </tr>
    <tr>
      <td><strong>Test Coverage</strong></td>
      <td>% of code covered by tests</td>
      <td>80% by Sprint 5</td>
      <td>QA agent after each test run; shown in CI badge</td>
    </tr>
    <tr>
      <td><strong>CI Green Rate</strong></td>
      <td>% of commits that pass the full CI pipeline</td>
      <td>95%+</td>
      <td>GitHub Actions; reported in sprint review</td>
    </tr>
    <tr>
      <td><strong>Code Review Pass Rate</strong></td>
      <td>% of engineer submissions approved first time (no changes requested)</td>
      <td>80%+</td>
      <td>Design &amp; Code Reviewer agent; logged in PLAN_STATUS.md</td>
    </tr>
    <tr>
      <td><strong>Blocker Resolution Time</strong></td>
      <td>Days from blocker raised to resolved</td>
      <td>&lt;1 day</td>
      <td>PM agent; tracked in PLAN_STATUS.md</td>
    </tr>
    <tr>
      <td><strong>Token Budget Usage</strong></td>
      <td>Sessions used vs. daily 80% allocation</td>
      <td>Stay within 80%</td>
      <td>Manually tracked; PM agent estimates at sprint start</td>
    </tr>
    <tr>
      <td><strong>Sprint Velocity</strong></td>
      <td>Planned tasks per sprint vs. actual completed</td>
      <td>Stabilise after Sprint 1</td>
      <td>PM agent retrospective report</td>
    </tr>
  </tbody>
</table>

<h2>Definition of Done (Per Task)</h2>
<p>A task is only marked <strong>[x] Done</strong> when ALL of the following are true:</p>
<ul>
  <li>Code is written and committed to the production repo</li>
  <li>Design &amp; Code Reviewer has approved the diff (or waiver is logged)</li>
  <li>Relevant tests are written and passing</li>
  <li>CI pipeline is green</li>
  <li>PLAN_STATUS.md is updated</li>
  <li>If it's a sprint-end task: Confluence page is published by Technical Writer</li>
</ul>

<h2>Sprint Calendar Overview</h2>
<table>
  <tbody>
    <tr><th>Sprint</th><th>Days</th><th>Focus</th><th>Key Metrics Goal</th></tr>
    <tr><td>Sprint 0</td><td>1-3</td><td>Architecture &amp; Planning</td><td>ADRs approved, schemas written, Confluence bootstrapped</td></tr>
    <tr><td>Sprint 1</td><td>4-8</td><td>Foundation</td><td>Config validated at startup, 12 repo classes, CI v2 green</td></tr>
    <tr><td>Sprint 2</td><td>9-14</td><td>API Decomposition</td><td>Monolith replaced, all endpoints tested, first coverage report</td></tr>
    <tr><td>Sprint 3</td><td>15-20</td><td>Services &amp; Observability</td><td>Zero print() statements, Prometheus /metrics live, coverage 60%+</td></tr>
    <tr><td>Sprint 4</td><td>21-26</td><td>Frontend &amp; Responsive</td><td>No monolithic HTML, responsive at 3 breakpoints</td></tr>
    <tr><td>Sprint 5</td><td>27-30</td><td>Integration &amp; Release</td><td>Coverage 80%+, security audit passed, k8s deployable, v1.0 tagged</td></tr>
  </tbody>
</table>
"""

# ─────────────────────────────────────────────────────────────────────────────
# PAGE 2: Claude Cowork vs Human Effort
# ─────────────────────────────────────────────────────────────────────────────
COWORK_VS_HUMAN = """
<h1>Claude Cowork vs Human Team &mdash; The Case For It</h1>
<p><strong>Version:</strong> 1.0 &nbsp;|&nbsp; <strong>Date:</strong> 2026-03-30</p>
<p style="background:#e8f4fd;border-left:4px solid #2196F3;padding:12px;">
<strong>The short answer:</strong> Claude Cowork is not a replacement for a senior engineering team. It is a <em>force multiplier</em> for a single expert owner (you). You supply domain expertise, architecture vision, and decisions. The agents supply tireless implementation, consistent standards, parallel execution, and documentation discipline &mdash; at a fraction of the cost and time.
</p>

<h2>Direct Comparison</h2>
<table>
  <tbody>
    <tr><th>Dimension</th><th>Human Team</th><th>Claude Cowork</th><th>Winner</th></tr>
    <tr>
      <td><strong>Cost</strong></td>
      <td>5-7 engineers: EUR 50,000-120,000/month (salaries, benefits, overhead)</td>
      <td>Claude Pro subscription: ~USD 20/month</td>
      <td>Cowork (by orders of magnitude)</td>
    </tr>
    <tr>
      <td><strong>Availability</strong></td>
      <td>Business hours, time zones, holidays, sick days</td>
      <td>24/7, any day, any hour, on-demand</td>
      <td>Cowork</td>
    </tr>
    <tr>
      <td><strong>Speed of execution</strong></td>
      <td>Weeks for this scope (code review queues, coordination, meetings)</td>
      <td>Days if sessions are planned efficiently</td>
      <td>Cowork</td>
    </tr>
    <tr>
      <td><strong>Consistency</strong></td>
      <td>Variable: junior vs senior quality, style drift, mood</td>
      <td>Applies the same rules every time, every agent</td>
      <td>Cowork</td>
    </tr>
    <tr>
      <td><strong>Onboarding time</strong></td>
      <td>2-4 weeks for a new engineer to be productive on a codebase like RITA</td>
      <td>Zero: CLAUDE.md + memory files = instant full context</td>
      <td>Cowork</td>
    </tr>
    <tr>
      <td><strong>Parallel work</strong></td>
      <td>Limited by team size and coordination overhead</td>
      <td>Multiple agents in isolated worktrees simultaneously, no conflicts</td>
      <td>Cowork</td>
    </tr>
    <tr>
      <td><strong>Code review objectivity</strong></td>
      <td>Can be political, inconsistent, skipped under deadline pressure</td>
      <td>Reviewer agent applies ADR rules mechanically, no exceptions</td>
      <td>Cowork</td>
    </tr>
    <tr>
      <td><strong>Documentation discipline</strong></td>
      <td>Often skipped or outdated; developers hate writing docs</td>
      <td>Technical Writer agent publishes to Confluence after every sprint, automatically</td>
      <td>Cowork</td>
    </tr>
    <tr>
      <td><strong>Domain intuition</strong></td>
      <td>Senior engineers can sense when something is architecturally wrong</td>
      <td>Only flags what the rules explicitly say; needs your validation for financial nuances</td>
      <td>Human</td>
    </tr>
    <tr>
      <td><strong>Creative problem-solving</strong></td>
      <td>Engineers invent novel solutions; bring experience from other companies</td>
      <td>Works within the design it is given; will not spontaneously re-architect</td>
      <td>Human</td>
    </tr>
    <tr>
      <td><strong>Financial domain judgment</strong></td>
      <td>A senior quant engineer will challenge a Greeks calculation proactively</td>
      <td>Implements what is specified; you must define the acceptance criteria</td>
      <td>Human</td>
    </tr>
    <tr>
      <td><strong>Risk of errors</strong></td>
      <td>Human errors caught in review; some slip through</td>
      <td>Deterministic errors in edge cases not covered by rules; caught by QA tests</td>
      <td>Roughly equal</td>
    </tr>
  </tbody>
</table>

<h2>What Claude Cowork Does Uniquely Well for RITA</h2>

<h3>1. Role Specialisation at Zero Coordination Cost</h3>
<p>With a human team you would need to: schedule meetings, write tickets, wait for PR reviews, manage availability. With Cowork, seven specialised roles operate in one session with zero coordination overhead. The Architect writes the ADR, the Reviewer approves it, and the Engineer starts implementing &mdash; all in the same hour, triggered by one command.</p>

<h3>2. Parallel Execution on Independent Domains</h3>
<p>In Sprint 1, three things can happen simultaneously:</p>
<ul>
  <li>Engineer A writes the new Pydantic config (no file overlap with B or Ops)</li>
  <li>Engineer B writes the 12 repository classes (no file overlap with A or Ops)</li>
  <li>Ops Engineer rewrites the Dockerfile and CI pipeline (no file overlap with A or B)</li>
</ul>
<p>With a human team this coordination would require a kick-off meeting, agreed file ownership, and a merge strategy. With Cowork it is a single command with worktree isolation.</p>

<h3>3. Consistent Application of Your Architecture Vision</h3>
<p>Once you approve ADR-001 (three-tier API) and ADR-002 (repository pattern), every agent in every future sprint applies those decisions without drift. There is no junior engineer who "didn't quite get the pattern" or senior engineer who has their own preferred approach. The design decisions you make in Sprint 0 propagate faithfully to Sprint 5.</p>

<h3>4. Living Documentation as a Side Effect of Work</h3>
<p>In most engineering teams, documentation is what gets cut when deadlines slip. In this setup, the Technical Writer agent is part of the sprint definition of done. Confluence is updated after every sprint as an automatic output, not an afterthought.</p>

<h3>5. Cost-Effective for a Single Expert Owner</h3>
<p>This project suits Cowork because you are the sole domain expert and decision-maker. You understand RITA, the RL model, the FnO portfolio mechanics, and the production requirements. You do not need a team to tell you <em>what</em> to build &mdash; you need execution capacity to actually build it. That is precisely what Cowork provides.</p>

<h2>Where You Still Need to Be Present</h2>
<p>Claude Cowork is not autonomous end-to-end. These are the areas where your input is essential:</p>
<table>
  <tbody>
    <tr><th>Area</th><th>Why your input is required</th></tr>
    <tr><td>Greeks calculation accuracy</td><td>Agents implement what is specified. You must define the acceptance criteria and validate reference values from first principles.</td></tr>
    <tr><td>Lot size and contract spec changes</td><td>NIFTY lot size changed from 50 to 75 in 2024. Agents do not track NSE regulatory changes. You do.</td></tr>
    <tr><td>Architecture decisions when two valid options exist</td><td>The Architect will present options; you decide. Agents implement your choice, not the "best" one in abstract.</td></tr>
    <tr><td>Security threat model</td><td>The Reviewer checks rules. You decide what threat model the system needs to defend against (e.g. internal users only vs. public-facing).</td></tr>
    <tr><td>Sprint scope adjustments</td><td>If a task is harder than planned, you decide: push to next sprint, simplify scope, or increase effort.</td></tr>
  </tbody>
</table>

<h2>The Mental Model</h2>
<p>Think of Claude Cowork as a <strong>highly skilled contractor team that only works when you call them, executes exactly what you specify, never argues, and costs nothing extra for nights and weekends</strong>. The trade-off is that they have no judgment beyond what you programme into the rules (ADRs, CLAUDE.md, review criteria). Your expertise sets the ceiling of what they can achieve.</p>
<p>For RITA specifically: <strong>you are the quant, the product owner, and the tech lead. The agents are the engineering execution team.</strong></p>
"""

# ─────────────────────────────────────────────────────────────────────────────
# PAGE 3: Claude Cowork Setup Guide
# ─────────────────────────────────────────────────────────────────────────────
SETUP_GUIDE = """
<h1>Claude Cowork Setup Guide</h1>
<p><strong>Version:</strong> 1.0 &nbsp;|&nbsp; <strong>Date:</strong> 2026-03-30</p>
<p style="background:#e8f4fd;border-left:4px solid #2196F3;padding:12px;">
This guide explains exactly how Claude Cowork is configured for the RITA project, what files make it work, and how to maintain it across sessions. No special install is required &mdash; Cowork is built into Claude Code.
</p>

<h2>How Claude Cowork Works (Architecture)</h2>
<pre>
You (human)
    |
    | "Start Day 3"
    v
Claude Code (main session -- coordinator)
    |
    |-- reads CLAUDE.md (auto-loaded every session)
    |-- reads PLAN_STATUS.md (session state)
    |
    |-- spawns Agent: Project Manager
    |       reads: PLAN_STATUS.md
    |       writes: task list for today
    |
    |-- spawns Agent: Architect (Plan agent)
    |       reads: docs/adr-template.md + scoped POC files
    |       writes: docs/ADR-001.md, src/rita/schemas/positions.py
    |       isolation: worktree (own branch)
    |
    |-- spawns Agent: Design &amp; Code Reviewer
    |       reads: docs/ADR-001.md + git diff
    |       writes: review report to coordinator
    |
    |-- spawns Agent: Engineer A (general-purpose)
    |       reads: docs/ADR-001.md + config.py lines 1-83
    |       writes: src/rita/config.py (rewritten), config/*.yaml
    |       isolation: worktree (own branch, no conflicts with B)
    |
    |-- spawns Agent: Technical Writer
    |       reads: all sprint artifacts
    |       writes: Confluence page via REST API
    |
    v
You review outputs, approve, confirm git commit
</pre>

<h2>The Four Setup Files</h2>
<p>Claude Cowork for RITA is configured through four files. Together they mean that every session starts with full project context in seconds, not minutes of re-exploration.</p>

<h3>1. CLAUDE.md (project root)</h3>
<p><strong>What it is:</strong> The project-level system prompt. Claude Code automatically loads this file at the start of every session in this directory.</p>
<p><strong>What it contains:</strong></p>
<ul>
  <li>Project purpose and file locations</li>
  <li>Agent team table (roles, scopes, agent types)</li>
  <li>Token efficiency rules (applied to every agent)</li>
  <li>Target folder structure</li>
  <li>Key design decisions summary (ADR-001, ADR-002)</li>
  <li>Confluence publishing credentials and page IDs</li>
  <li>Financial domain notes (lot sizes, Greeks, data locations)</li>
  <li>Hard rules: what agents must never do</li>
</ul>
<p><strong>When to update:</strong> After each sprint if new rules, file paths, or design decisions are made. The Technical Writer agent is responsible for keeping CLAUDE.md current.</p>

<h3>2. PLAN_STATUS.md (project root)</h3>
<p><strong>What it is:</strong> The daily status tracker. Read by the PM agent at the start of every session; updated by the PM agent at the end of every session.</p>
<p><strong>What it contains:</strong></p>
<ul>
  <li>Current sprint and current day</li>
  <li>All tasks with status: <code>[ ]</code> todo, <code>[~]</code> in-progress, <code>[x]</code> done, <code>[!]</code> blocked</li>
  <li>Blockers with raised date and resolution notes</li>
  <li>Session notes (decisions made, scope changes)</li>
</ul>
<p><strong>Why it matters:</strong> This is what prevents agents from re-exploring the whole codebase at the start of each session. One small file read = full context recovery.</p>

<h3>3. Memory Files (.claude/projects/riia-cowork-jun/memory/)</h3>
<p><strong>What they are:</strong> Persistent facts that survive across sessions and projects. Automatically loaded by Claude Code into every conversation in this directory.</p>
<p><strong>Current memory files:</strong></p>
<ul>
  <li><code>MEMORY.md</code> -- index of all memory entries</li>
  <li><code>project_rita_refactor.md</code> -- project goal, source/target paths, critical issues, tech stack</li>
  <li><code>user_profile.md</code> -- who you are and how you prefer to work</li>
  <li><code>reference_confluence.md</code> -- Confluence space details, published page IDs, auth notes</li>
</ul>
<p><strong>When to update:</strong> The coordinator (main Claude session) updates memory files when significant facts change (new decisions, new page IDs, new preferences). Memory is not used for ephemeral session state -- that belongs in PLAN_STATUS.md.</p>

<h3>4. docs/ ADR files (created in Sprint 0)</h3>
<p><strong>What they are:</strong> Architecture Decision Records. Once approved by you, these become the authoritative source of truth that all Engineer agents read before writing any code.</p>
<p><strong>Why this matters for Cowork:</strong> Without ADRs, each Engineer agent would derive its own interpretation of the design from the codebase. With ADRs, all agents implement the same design. ADRs are the mechanism by which your Sprint 0 architecture decisions propagate faithfully to Sprint 5 execution.</p>
<p><strong>Planned ADRs:</strong></p>
<ul>
  <li>ADR-001: Three-Tier API Design (BFF / Business Process / System)</li>
  <li>ADR-002: Repository Pattern (CSV v1 / PostgreSQL v2 swap-in)</li>
  <li>ADR-003: Pydantic Settings and Config Hierarchy</li>
  <li>ADR-004: Security Model (JWT, CORS, rate limiting)</li>
  <li>ADR-005: Frontend Module Structure and Responsive Breakpoints</li>
</ul>

<h2>Agent Type Reference</h2>
<table>
  <tbody>
    <tr><th>Agent Type</th><th>Used for</th><th>Key capability</th></tr>
    <tr>
      <td><code>general-purpose</code></td>
      <td>PM, Engineer, QA, Ops, TechWriter, Reviewer</td>
      <td>Full tool access: read, write, edit, bash, web search, web fetch</td>
    </tr>
    <tr>
      <td><code>Plan</code></td>
      <td>Architect</td>
      <td>Specialised for designing implementation strategies, identifying critical files, architectural trade-offs</td>
    </tr>
    <tr>
      <td><code>Explore</code></td>
      <td>Initial codebase discovery only</td>
      <td>Fast read-only search across the codebase; used once at project start, not in sprints</td>
    </tr>
  </tbody>
</table>

<h2>Worktree Isolation (How Parallel Engineers Avoid Conflicts)</h2>
<p>When two Engineer agents need to write code simultaneously (e.g. Engineer A writes config, Engineer B writes repositories), each agent runs with <code>isolation: "worktree"</code>. This creates a temporary git worktree &mdash; an isolated copy of the repository on its own branch. The agents cannot see or overwrite each other's files.</p>
<p>At end of day, the Design &amp; Code Reviewer reviews each worktree diff, then the coordinator merges approved branches to main in sequence.</p>
<pre>
main branch
    |
    +-- worktree-engineer-a (config changes)
    |       src/rita/config.py
    |       config/base.yaml
    |
    +-- worktree-engineer-b (repository changes)
            src/rita/repositories/positions.py
            src/rita/repositories/orders.py

After review and approval:
    main &lt;-- merge engineer-a (no conflicts: different files)
    main &lt;-- merge engineer-b (no conflicts: different files)
</pre>

<h2>Confluence Integration</h2>
<p>The Technical Writer agent publishes to Confluence using the REST API v1 storage format. The publisher script (<code>publish_confluence.py</code>) is committed to the repo. The API token is currently in <code>confluence-api-key.txt</code> and will be moved to an environment variable in Sprint 1.</p>
<p><strong>Page creation pattern used by all TechWriter agents:</strong></p>
<pre>
POST https://ravionics.atlassian.net/wiki/rest/api/content
Authorization: Basic {base64(email:token)}
Content-Type: application/json

{
  "type": "page",
  "title": "Page Title",
  "space": {"key": "RIIAProjec"},
  "ancestors": [{"id": "65110332"}],
  "body": {
    "storage": {
      "value": "&lt;h1&gt;...plain HTML, no ac: macros...&lt;/h1&gt;",
      "representation": "storage"
    }
  }
}
</pre>
<p><strong>Important constraint:</strong> Use plain HTML only in page bodies. The <code>ac:structured-macro</code> Confluence macro syntax is not supported by this instance's Fabric editor and returns HTTP 400.</p>

<h2>Session Recovery After Token Limit</h2>
<p>If a session ends due to token limits before all planned work is complete:</p>
<ol>
  <li>The in-progress agent saves its output file before stopping</li>
  <li>PLAN_STATUS.md is updated: the task is marked <code>[~]</code> with a note of exactly what was completed and what file to resume from</li>
  <li>Work is committed to git (partial commit is fine)</li>
  <li>New session: <code>Start Day N</code> reads PLAN_STATUS.md and the agent resumes from the saved file, not from scratch</li>
</ol>

<h2>Maintenance Checklist (Per Sprint)</h2>
<ul>
  <li>Update CLAUDE.md if new file paths, design rules, or ADRs were added this sprint</li>
  <li>Update PLAN_STATUS.md at end of every session (done by PM agent)</li>
  <li>Update memory files if significant project facts changed (done by coordinator)</li>
  <li>Ensure <code>confluence-api-key.txt</code> is in <code>.gitignore</code> (Sprint 1 moves it to env var)</li>
  <li>Tag the sprint in git: <code>git tag sprint-N-complete</code></li>
</ul>

<h2>Quick Reference: All Commands</h2>
<table>
  <tbody>
    <tr><th>Command</th><th>What happens</th></tr>
    <tr><td><code>Start Day N</code></td><td>PM agent reads status, confirms tasks, you approve, agents launch</td></tr>
    <tr><td><code>End day</code></td><td>PM updates status, git commit, TechWriter publishes Confluence</td></tr>
    <tr><td><code>What's next?</code></td><td>PM reads status and reports current day and planned tasks</td></tr>
    <tr><td><code>Show blockers</code></td><td>PM reads and lists all blocked items</td></tr>
    <tr><td><code>Start Sprint N</code></td><td>PM generates sprint task breakdown; you approve before Day 1 of sprint begins</td></tr>
    <tr><td><code>End Sprint N</code></td><td>TechWriter publishes sprint review; PM produces retro; sprint marked complete</td></tr>
    <tr><td><code>Retro Sprint N</code></td><td>PM analyses sprint data and produces retrospective report</td></tr>
    <tr><td><code>Review Day N output</code></td><td>Design &amp; Code Reviewer re-runs on a previous day's diff</td></tr>
    <tr><td><code>Skip to Sprint N</code></td><td>Marks current sprint complete (with your confirmation) and starts next</td></tr>
  </tbody>
</table>
"""

# ─────────────────────────────────────────────────────────────────────────────
# Publish
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== Publishing 3 new Confluence pages ===\n")

print("1. Sprint Planning & Metrics...")
p1_id, p1_url = create_page("Sprint Planning and Metrics", SPRINT_PLANNING)
time.sleep(1)

print("\n2. Claude Cowork vs Human Team...")
p2_id, p2_url = create_page("Claude Cowork vs Human Team -- The Case For It", COWORK_VS_HUMAN)
time.sleep(1)

print("\n3. Claude Cowork Setup Guide...")
p3_id, p3_url = create_page("Claude Cowork Setup Guide", SETUP_GUIDE)

print("\n=== Done ===")
if p1_url: print(f"\nSprint Planning:  {p1_url}")
if p2_url: print(f"Cowork vs Human:  {p2_url}")
if p3_url: print(f"Setup Guide:      {p3_url}")
