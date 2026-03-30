"""
Publish RITA project pages to Confluence (plain HTML, no ac: macros).
Space: RIIAProjec | Parent: 65110332 (homepage)
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

def api(method, path, body=None):
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(f"{BASE}{path}", data=data, headers=HEADERS, method=method)
    try:
        with urllib.request.urlopen(req) as r:
            return json.load(r), r.status
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode()), e.code

def create_page(title, body_html, parent_id=PARENT):
    payload = {
        "type": "page",
        "title": title,
        "space": {"key": SPACE},
        "ancestors": [{"id": parent_id}],
        "body": {"storage": {"value": body_html, "representation": "storage"}}
    }
    result, status = api("POST", "/content", payload)
    if status in (200, 201):
        page_id = result["id"]
        url = f"https://ravionics.atlassian.net/wiki{result['_links']['webui']}"
        print(f"  CREATED [{page_id}] '{title}'")
        print(f"  URL: {url}")
        return page_id, url
    else:
        print(f"  FAILED '{title}': HTTP {status} -- {result.get('message','')}")
        return None, None

# ─────────────────────────────────────────────────────────────────────────────
# PAGE 1: Master Plan
# ─────────────────────────────────────────────────────────────────────────────
MASTER_PLAN = """
<h1>RITA Production Refactor &mdash; Master Plan</h1>
<p><strong>Version:</strong> 1.0 &nbsp;|&nbsp; <strong>Date:</strong> 2026-03-30 &nbsp;|&nbsp; <strong>Owner:</strong> Project Team</p>
<p style="background:#e8f4fd;border-left:4px solid #2196F3;padding:12px;">
<strong>Project Goal:</strong> Refactor RITA (Risk Informed Trading Approach) from a working POC into a production-grade, cloud-native, secure and maintainable system &mdash; using a Claude Cowork multi-agent team executing daily sprint cycles.
</p>

<h2>Project Repositories &amp; References</h2>
<table>
  <tbody>
    <tr><th>Item</th><th>Location</th></tr>
    <tr><td>POC Source</td><td><code>rita-cowork-demo/</code></td></tr>
    <tr><td>Production Target</td><td><code>riia-cowork-jun/</code></td></tr>
    <tr><td>Assessment Doc</td><td><code>production_ready.md</code> (v2.0, 1908 lines, 29-Mar-2026)</td></tr>
    <tr><td>Daily Status</td><td><code>PLAN_STATUS.md</code> (updated each session)</td></tr>
    <tr><td>Confluence Space</td><td>RIIA-Project-Refactor (this space)</td></tr>
  </tbody>
</table>

<h2>Team &mdash; Claude Cowork Agent Roles</h2>
<table>
  <tbody>
    <tr><th>Role</th><th>Agent Type</th><th>Responsibility</th></tr>
    <tr>
      <td><strong>Project Manager</strong></td>
      <td>general-purpose</td>
      <td>Sprint planning, daily work breakdown, risk tracking, status updates, dependency management</td>
    </tr>
    <tr>
      <td><strong>Architect</strong></td>
      <td>Plan agent</td>
      <td>Target folder structure, ADRs, API tier contracts, Pydantic schemas, dependency injection design</td>
    </tr>
    <tr>
      <td><strong>Design &amp; Code Reviewer</strong></td>
      <td>general-purpose</td>
      <td>Reviews designs before implementation; reviews diffs after engineering; checks ADR compliance, security patterns, coding standards; approves or requests changes</td>
    </tr>
    <tr>
      <td><strong>Engineer (x N)</strong></td>
      <td>general-purpose, isolated worktrees</td>
      <td>Code implementation split by domain: Config/Security, Data Layer, API tiers, Services, Observability, Frontend</td>
    </tr>
    <tr>
      <td><strong>QA Tester</strong></td>
      <td>general-purpose</td>
      <td>Unit tests, integration tests, e2e tests (Playwright), coverage reports, regression suites</td>
    </tr>
    <tr>
      <td><strong>Ops Engineer</strong></td>
      <td>general-purpose</td>
      <td>Multi-stage Dockerfile, GitHub Actions CI/CD pipeline, Kubernetes manifests, secrets config, canary rollout</td>
    </tr>
    <tr>
      <td><strong>Technical Writer</strong></td>
      <td>general-purpose</td>
      <td>Authors sprint documentation and publishes all 14 Confluence pages (ADRs, API reference, runbooks, release notes)</td>
    </tr>
  </tbody>
</table>

<h2>Critical Issues Being Addressed</h2>
<p>Source: <code>production_ready.md</code> v2.0</p>
<table>
  <tbody>
    <tr><th>Priority</th><th>Issue</th><th>Current State</th><th>Target (v1)</th></tr>
    <tr><td><strong>[P0 - CRITICAL]</strong></td><td>API Monolith</td><td>1,533-line rest_api.py, all logic in one file</td><td>Three-tier: BFF / Business Process / System</td></tr>
    <tr><td><strong>[P0 - CRITICAL]</strong></td><td>Security</td><td>API key hardcoded in HTML, CORS wildcard, no JWT</td><td>JWT auth, restricted CORS, rate limiting (slowapi)</td></tr>
    <tr><td><strong>[P0 - CRITICAL]</strong></td><td>Data Layer</td><td>Direct CSV I/O mixed into route handlers</td><td>Repository pattern + service layer</td></tr>
    <tr><td><strong>[P0 - CRITICAL]</strong></td><td>Configuration</td><td>Raw os.getenv(), no validation, no types</td><td>Pydantic Settings with field-level validation</td></tr>
    <tr><td><strong>[P0 - CRITICAL]</strong></td><td>Testing</td><td>Less than 5% coverage, no API or integration tests</td><td>80% coverage target, full test pyramid enforced in CI</td></tr>
    <tr><td><strong>[P1 - HIGH]</strong></td><td>Error Handling</td><td>Silent NaN failures, fire-and-forget AJAX, no trace IDs</td><td>Structured errors, global exception handler, trace IDs</td></tr>
    <tr><td><strong>[P1 - HIGH]</strong></td><td>Observability</td><td>print() statements throughout codebase</td><td>structlog JSON logging + Prometheus metrics</td></tr>
    <tr><td><strong>[P1 - HIGH]</strong></td><td>Frontend</td><td>3 HTML files at 4,000+ lines each, desktop-only</td><td>ES modules, responsive design (480/768/1100px breakpoints)</td></tr>
  </tbody>
</table>

<h2>Sprint Roadmap</h2>
<table>
  <tbody>
    <tr><th>Sprint</th><th>Name</th><th>Work Days</th><th>Key Deliverables</th><th>Status</th></tr>
    <tr>
      <td><strong>Sprint 0</strong></td>
      <td>Architecture &amp; Planning</td>
      <td>Days 1-3</td>
      <td>Target folder structure, ADR-001 (API tiers) &amp; ADR-002 (Repository pattern), Pydantic schemas for 15 CSV tables, Confluence bootstrapped</td>
      <td><strong>[IN PROGRESS]</strong></td>
    </tr>
    <tr>
      <td><strong>Sprint 1</strong></td>
      <td>Foundation</td>
      <td>Days 4-8</td>
      <td>Pydantic config + YAML hierarchy, repository layer (12 files), multi-stage Dockerfile, CI v2 with coverage gate, config and repository tests</td>
      <td>[PLANNED]</td>
    </tr>
    <tr>
      <td><strong>Sprint 2</strong></td>
      <td>API Decomposition</td>
      <td>Days 9-14</td>
      <td>Three-tier API routers replacing 1,533-line monolith, global exception handler, trace IDs, full API contract tests</td>
      <td>[PLANNED]</td>
    </tr>
    <tr>
      <td><strong>Sprint 3</strong></td>
      <td>Service Layer &amp; Observability</td>
      <td>Days 15-20</td>
      <td>WorkflowService, ManoeuvreService, PortfolioService, structlog JSON logging, Prometheus metrics, /health and /readyz endpoints</td>
      <td>[PLANNED]</td>
    </tr>
    <tr>
      <td><strong>Sprint 4</strong></td>
      <td>Frontend &amp; Responsive Design</td>
      <td>Days 21-26</td>
      <td>ES module decomposition of all 3 HTML apps, responsive CSS, Playwright e2e tests</td>
      <td>[PLANNED]</td>
    </tr>
    <tr>
      <td><strong>Sprint 5</strong></td>
      <td>Integration, Security &amp; Release</td>
      <td>Days 27-30</td>
      <td>Full regression suite, security audit, k8s manifests, canary rollout, Release v1.0 notes</td>
      <td>[PLANNED]</td>
    </tr>
  </tbody>
</table>

<h2>Agent Workflow (How Roles Interact Each Sprint)</h2>
<pre>
PM Agent
  +--&gt; Daily task list + risk updates
         |
         v
Architect Agent
  +--&gt; ADRs + module contracts + Pydantic schemas
         |
         v
Design &amp; Code Reviewer
  +--&gt; Approves design BEFORE engineers start
         |
         +--&gt; Engineer A (Config / Security)       [isolated worktree]
         +--&gt; Engineer B (Data Layer / Repos)      [isolated worktree]
         +--&gt; Ops (Dockerfile + CI/CD)             [isolated worktree]
         |
         v
Design &amp; Code Reviewer
  +--&gt; Reviews diffs, approves or requests changes
         |
         v
QA Agent
  +--&gt; Tests written and passing, coverage report
         |
         v
Technical Writer
  +--&gt; Confluence pages published
         |
         v
  (repeat per sprint)
</pre>

<h2>Risk Register</h2>
<table>
  <tbody>
    <tr><th>#</th><th>Risk</th><th>Likelihood</th><th>Impact</th><th>Mitigation</th></tr>
    <tr><td>R1</td><td>Token budget exceeded mid-sprint on large file reads</td><td>High</td><td>Medium</td><td>Agents read scoped file sections only; pre-digested production_ready.md excerpts passed as context</td></tr>
    <tr><td>R2</td><td>Parallel engineers create merge conflicts</td><td>Medium</td><td>High</td><td>Worktree isolation per agent branch; merge only at end-of-day code review</td></tr>
    <tr><td>R3</td><td>Greeks calculation regression during refactor</td><td>Medium</td><td>Critical</td><td>QA writes Black-Scholes reference tests before engineers touch core/ modules</td></tr>
    <tr><td>R4</td><td>CSV race conditions surface in production</td><td>Medium</td><td>High</td><td>Repository file locking is Sprint 1 Day 5 highest priority item</td></tr>
    <tr><td>R5</td><td>Security gaps missed during API decomposition</td><td>Medium</td><td>Critical</td><td>Design &amp; Code Reviewer explicitly checks all security patterns at every sprint boundary</td></tr>
  </tbody>
</table>

<h2>Definition of Done (v1 Release)</h2>
<ul>
  <li>All API endpoints in three-tier router structure (System / Business Process / BFF) &mdash; no monolith</li>
  <li>All CSV access via repository classes &mdash; no direct file I/O in route handlers</li>
  <li>Pydantic Settings validates config at startup; missing secrets crash at boot, not at runtime</li>
  <li>Test coverage at or above 80% (unit + integration), enforced by CI gate</li>
  <li>No hardcoded secrets, API keys, or localhost URLs in any code or HTML file</li>
  <li>Structured JSON logs (structlog) throughout &mdash; zero print() statements</li>
  <li>Prometheus metrics exported at /metrics; /health and /readyz endpoints live</li>
  <li>All dashboard HTML decomposed into ES modules; responsive at 480/768/1100px</li>
  <li>Kubernetes manifests valid and deployable with canary rollout strategy</li>
  <li>All 14 Confluence documentation pages published and current</li>
  <li>Design &amp; Code Reviewer sign-off recorded for each sprint</li>
</ul>
"""

# ─────────────────────────────────────────────────────────────────────────────
# PAGE 2: Token Budget & Work Planning
# ─────────────────────────────────────────────────────────────────────────────
TOKEN_BUDGET = """
<h1>Token Budget &amp; Daily Work Planning</h1>
<p><strong>Version:</strong> 1.0 &nbsp;|&nbsp; <strong>Date:</strong> 2026-03-30</p>
<p style="background:#fff8e1;border-left:4px solid #FFC107;padding:12px;">
<strong>Budget Rule:</strong> 80% of the Claude Pro daily token quota is allocated to this project. The remaining 20% is reserved for other simultaneous projects. All sprint work is planned around this constraint.
</p>

<h2>Understanding the Claude Pro Token Budget</h2>
<p>Claude Pro operates on a <strong>rolling usage window</strong> that resets approximately every 5 hours. Heavy usage (large file reads, multiple parallel agents, long code generation) consumes quota faster than light tasks (planning, status checks, documentation). There is no hard published token count; it is usage-based and context-size-dependent.</p>
<p>The key variable is <strong>context size per agent invocation</strong>:</p>
<table>
  <tbody>
    <tr><th>What drives context size up</th><th>Our mitigation</th></tr>
    <tr><td>Reading large files whole (e.g. rest_api.py at 1,533 lines)</td><td>Read in 300-400 line slices targeted at the section being modified</td></tr>
    <tr><td>Re-reading production_ready.md (1,908 lines) in every session</td><td>Pre-digested at project start; only relevant section excerpts passed to agents</td></tr>
    <tr><td>Launching 8+ agents in one session</td><td>Maximum 3-5 focused agent invocations per session</td></tr>
    <tr><td>Agent re-deriving architecture from scratch</td><td>Architect writes ADR files; subsequent agents read the file, not the codebase</td></tr>
  </tbody>
</table>

<h2>Session Types and Token Cost</h2>
<table>
  <tbody>
    <tr><th>Session Type</th><th>Token Cost</th><th>Examples</th><th>Max Per Day</th></tr>
    <tr>
      <td><strong>Heavy</strong></td>
      <td>HIGH</td>
      <td>Reading rita.html (4,000 lines) or rest_api.py (1,533 lines); 3 parallel engineer agents writing new code</td>
      <td>1-2</td>
    </tr>
    <tr>
      <td><strong>Medium</strong></td>
      <td>MEDIUM</td>
      <td>Architecture design, service layer work, QA test writing, Ops config files, code review of significant diffs</td>
      <td>2-3</td>
    </tr>
    <tr>
      <td><strong>Light</strong></td>
      <td>LOW</td>
      <td>Status check, daily plan, TechWriter publishing docs to Confluence, review of small diffs, PLAN_STATUS.md update</td>
      <td>4-5</td>
    </tr>
  </tbody>
</table>

<h2>Token Efficiency Rules (Applied to Every Agent)</h2>
<ol>
  <li><strong>No agent reads production_ready.md in full.</strong> Pre-digested at project start. Agents receive only the relevant section as a quoted excerpt.</li>
  <li><strong>Large files are read in slices.</strong> rest_api.py and rita.html are read in 300-400 line windows targeting only the section being modified that day.</li>
  <li><strong>Architect artifacts are written to files.</strong> Subsequent agents read the saved ADR/schema file rather than re-deriving design from the codebase.</li>
  <li><strong>Worktree isolation.</strong> Parallel engineer agents each work in an isolated git branch. The main context window stays clean between sessions.</li>
  <li><strong>Status tracked in PLAN_STATUS.md.</strong> Each session starts by reading this one small file, not a full codebase re-exploration.</li>
  <li><strong>3-5 agents per session maximum.</strong> Even if more work is available, stop at this limit to stay inside the 80% quota allocation.</li>
</ol>

<h2>Daily Session Structure</h2>
<pre>
START OF SESSION (light -- approx 5 min)
  1. Read PLAN_STATUS.md          &lt;-- 1 small file, minimal tokens
  2. Identify today's tasks
  3. Confirm agent assignments with user

WORK BLOCK (medium/heavy -- approx 30-60 min)
  4. Launch agents in sequence or targeted parallel pairs
     - Heavy agents (code write): one at a time, full focus
     - Light agents (review, docs): can run in pairs

END OF SESSION (light -- approx 10 min)
  5. Design &amp; Code Reviewer checks today's diffs
  6. Update PLAN_STATUS.md (completed / blocked)
  7. Git commit of day's work
  8. Technical Writer publishes Confluence update
</pre>

<h2>Sprint-by-Sprint Token Profile</h2>
<table>
  <tbody>
    <tr><th>Sprint</th><th>Days</th><th>Heaviest Agent Task</th><th>Token Profile</th><th>Mitigation Strategy</th></tr>
    <tr>
      <td>Sprint 0</td><td>1-3</td><td>Architect designing schemas and ADRs</td><td>LIGHT</td>
      <td>Reads only config.py and CSV headers; outputs new schema files</td>
    </tr>
    <tr>
      <td>Sprint 1</td><td>4-8</td><td>Engineer B writing 12 repository files</td><td>MEDIUM</td>
      <td>Each repository file is small and self-contained; split across 2 sessions if needed</td>
    </tr>
    <tr>
      <td>Sprint 2</td><td>9-14</td><td>Engineer C decomposing 1,533-line rest_api.py</td><td>HEAVY</td>
      <td>Read in 400-line slices; one router group per session (System Day 9, Business Process Day 10, BFF Day 11)</td>
    </tr>
    <tr>
      <td>Sprint 3</td><td>15-20</td><td>Engineer D/E writing new service and observability files</td><td>MEDIUM</td>
      <td>New files from ADR contracts; minimal legacy code reading required</td>
    </tr>
    <tr>
      <td>Sprint 4</td><td>21-26</td><td>Engineer F decomposing 4,000-line rita.html + fno.html</td><td>HEAVY</td>
      <td>One HTML section per session; 500-line read windows; 2 sessions per HTML file</td>
    </tr>
    <tr>
      <td>Sprint 5</td><td>27-30</td><td>QA full regression and security audit</td><td>MEDIUM</td>
      <td>Targeted fixes only; all code already written; short focused review sessions</td>
    </tr>
  </tbody>
</table>

<h2>If Quota Runs Low Mid-Session</h2>
<ol>
  <li>The current agent completes its task and saves output to a file immediately.</li>
  <li>PLAN_STATUS.md is updated to mark the task as <strong>[~] in-progress</strong> with a note of exactly what was completed.</li>
  <li>Work resumes in the next session &mdash; the agent is re-launched with the saved file as its starting point, not from scratch.</li>
  <li>No work is lost because all agent outputs are persisted to the repo before the session ends.</li>
</ol>
<p style="background:#e8f5e9;border-left:4px solid #4CAF50;padding:12px;">
<strong>Key habit:</strong> Always commit work to git at end of session, even if partial. The next session resumes cleanly from a known state without re-exploring the whole codebase.
</p>
"""

# ─────────────────────────────────────────────────────────────────────────────
# PAGE 3: Claude Cowork User Guide
# ─────────────────────────────────────────────────────────────────────────────
COWORK_GUIDE = """
<h1>How We Use Claude Cowork &mdash; User Guide</h1>
<p><strong>Version:</strong> 1.0 &nbsp;|&nbsp; <strong>Date:</strong> 2026-03-30</p>
<p style="background:#e8f4fd;border-left:4px solid #2196F3;padding:12px;">
<strong>What is Claude Cowork?</strong> Claude Cowork is Claude Code's sub-agent system. The main Claude instance (your conversation partner) acts as a coordinator and spawns specialised sub-agents &mdash; each with a focused role, scoped context, and specific tools. Sub-agents work autonomously, produce file artifacts, and report back. This lets an entire engineering team work in parallel without you managing each member manually.
</p>

<h2>The Agent Team &mdash; Who Does What</h2>
<table>
  <tbody>
    <tr><th>Role</th><th>When Launched</th><th>Reads</th><th>Produces</th></tr>
    <tr>
      <td><strong>Project Manager</strong></td>
      <td>Start of each sprint; start of each day</td>
      <td>PLAN_STATUS.md, previous sprint output</td>
      <td>Prioritised task list, risk updates, updated PLAN_STATUS.md</td>
    </tr>
    <tr>
      <td><strong>Architect</strong></td>
      <td>Sprint 0; before any new module is designed</td>
      <td>POC source files (targeted), production_ready.md excerpt</td>
      <td>ADR files, Pydantic schema files, module interface contracts</td>
    </tr>
    <tr>
      <td><strong>Design &amp; Code Reviewer</strong></td>
      <td>After Architect produces design; after each Engineer finishes code</td>
      <td>ADR files, git diff of new/changed code</td>
      <td>Review report: APPROVED or CHANGES REQUESTED with specific comments</td>
    </tr>
    <tr>
      <td><strong>Engineer (x N)</strong></td>
      <td>After Design Reviewer approves the design</td>
      <td>ADR/schema files, scoped slice of POC source</td>
      <td>New production code files committed to isolated worktree branch</td>
    </tr>
    <tr>
      <td><strong>QA Tester</strong></td>
      <td>After Engineer completes code; before sprint closes</td>
      <td>New code files, schema contracts</td>
      <td>Test files in tests/, coverage report, pass/fail summary</td>
    </tr>
    <tr>
      <td><strong>Ops Engineer</strong></td>
      <td>Sprint 1 (Dockerfile/CI) and Sprint 5 (k8s/canary)</td>
      <td>pyproject.toml, existing Dockerfile, CI yml</td>
      <td>Updated Dockerfile, .github/workflows/ci.yml, k8s/ manifests</td>
    </tr>
    <tr>
      <td><strong>Technical Writer</strong></td>
      <td>End of each sprint; end of significant work days</td>
      <td>All sprint artifacts (ADRs, code, test reports)</td>
      <td>Confluence pages published to RIIA-Project-Refactor space</td>
    </tr>
  </tbody>
</table>

<h2>Your Daily Routine &mdash; What You Need to Do</h2>

<h3>Step 1: Start the Day (1 minute)</h3>
<p>Open Claude Code and type:</p>
<pre>Start Day N</pre>
<p>Claude will read PLAN_STATUS.md, confirm today's tasks, and tell you exactly which agents it will launch. <strong>You approve before any work begins.</strong></p>

<h3>Step 2: Approve Agent Plans (2-3 minutes)</h3>
<p>Before each agent runs, Claude summarises what it will read and write. You respond:</p>
<ul>
  <li><strong>Yes, proceed</strong> &mdash; agent runs autonomously and reports back when done</li>
  <li><strong>Adjust scope</strong> &mdash; Claude refines the task before running</li>
</ul>
<p>For destructive operations (file deletes, large rewrites, git operations), Claude will always ask explicitly and wait for confirmation.</p>

<h3>Step 3: Review Design &amp; Code (5-10 minutes)</h3>
<p>After the Design &amp; Code Reviewer agent runs, Claude shows you:</p>
<ul>
  <li>A summary of what was reviewed (design doc or code diff)</li>
  <li>Any issues found, each with a severity level (critical / major / minor)</li>
  <li>A pass/fail recommendation</li>
</ul>
<p>You decide: <strong>merge to main</strong> or <strong>request changes</strong>. If changes are needed, the relevant Engineer agent is re-launched with the reviewer's comments as input.</p>

<h3>Step 4: End-of-Day Sign-Off (2 minutes)</h3>
<p>Type <code>End day</code> to trigger the close-out flow:</p>
<ol>
  <li>Claude updates PLAN_STATUS.md with completed and blocked items</li>
  <li>Claude asks you to confirm a git commit for the day's work</li>
  <li>Technical Writer agent publishes the Confluence documentation update</li>
</ol>

<h2>Decision Points That Require Your Input</h2>
<table>
  <tbody>
    <tr><th>Situation</th><th>What Claude Will Ask</th><th>Your Action</th></tr>
    <tr><td>Architect produces ADRs</td><td>"Review ADR-001 and ADR-002 -- approve to proceed?"</td><td>Read the 1-2 page ADR files; approve or comment</td></tr>
    <tr><td>Design Reviewer flags an issue</td><td>"Reviewer found 2 issues -- fix now or defer to next sprint?"</td><td>Choose fix-now or log as tracked tech debt</td></tr>
    <tr><td>QA reports coverage below 80%</td><td>"Coverage is 72% -- write more tests now or accept with a tracking ticket?"</td><td>Decide threshold or direct QA to write more tests</td></tr>
    <tr><td>Ops proposes a CI change</td><td>"CI pipeline will now fail builds on coverage below 80%. Confirm?"</td><td>Confirm or adjust threshold</td></tr>
    <tr><td>Sprint complete</td><td>"Sprint N done -- review deliverables before closing?"</td><td>Skim the sprint Confluence page and confirm close</td></tr>
    <tr><td>Two valid design options</td><td>"Option A: X. Option B: Y. Which approach?"</td><td>Choose one; Claude proceeds without further questions</td></tr>
  </tbody>
</table>

<h2>What You Do NOT Need to Do</h2>
<ul>
  <li>Read or write any code yourself &mdash; agents handle all implementation</li>
  <li>Track individual file changes &mdash; PLAN_STATUS.md is the single source of truth</li>
  <li>Manually publish to Confluence &mdash; Technical Writer agent handles this after each sprint</li>
  <li>Remember context between sessions &mdash; memory files and PLAN_STATUS.md carry all state</li>
  <li>Manage git branches or worktrees &mdash; isolation and merges are handled automatically</li>
  <li>Re-read production_ready.md &mdash; it was pre-digested; relevant sections are passed to agents as needed</li>
</ul>

<h2>How to Handle Blockers</h2>
<pre>
When an agent is blocked (missing data, ambiguous requirement, failing test):
  1. Claude surfaces the blocker with full context
  2. You provide the missing information or make a decision
  3. The agent resumes from where it stopped -- no restart from scratch
  4. The blocker and resolution are logged in PLAN_STATUS.md

Common blockers you may be asked to resolve:
  - "Need the lot size for BANKNIFTY" -- you provide the value
  - "Two valid design options -- which approach?" -- you choose
  - "Test fixture missing for Greeks calculation" -- you supply a sample value
  - "CI is failing -- approve this dependency upgrade?" -- you approve or reject
</pre>

<h2>Project Success Criteria &mdash; Your Commitments</h2>
<ul>
  <li><strong>Review and approve</strong> each sprint's Confluence documentation page before the sprint is closed</li>
  <li><strong>Be available</strong> for a 5-15 minute daily session to approve plans, review outputs, and unblock decisions</li>
  <li><strong>Commit</strong> the day's work to git at end of each session when Claude prompts you</li>
  <li><strong>Do not skip</strong> the Design &amp; Code Reviewer step &mdash; this is the quality gate that prevents regressions</li>
  <li><strong>Move</strong> the Confluence API key out of the plain text file and into an environment variable (done in Sprint 1)</li>
</ul>

<p style="background:#e8f5e9;border-left:4px solid #4CAF50;padding:12px;font-size:1.1em;">
<strong>One sentence to remember:</strong> Your job is to <em>decide and approve</em>; the agent team's job is to <em>design, build, test, and document</em>.
</p>

<h2>Quick Reference &mdash; Commands to Know</h2>
<table>
  <tbody>
    <tr><th>Command</th><th>What it does</th></tr>
    <tr><td><code>Start Day N</code></td><td>Begins the session: reads status, confirms tasks, launches agents</td></tr>
    <tr><td><code>End day</code></td><td>Closes the session: updates status, commits work, publishes docs</td></tr>
    <tr><td><code>What's next?</code></td><td>Shows current day number and today's planned tasks</td></tr>
    <tr><td><code>Show blockers</code></td><td>Lists all current blocked items from PLAN_STATUS.md</td></tr>
    <tr><td><code>Skip to Sprint N</code></td><td>Jumps to a different sprint (with your confirmation)</td></tr>
    <tr><td><code>Review Day N output</code></td><td>Re-runs the Design &amp; Code Reviewer on a previous day's work</td></tr>
  </tbody>
</table>
"""

# ─────────────────────────────────────────────────────────────────────────────
# Publish all pages
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== Publishing RITA Confluence Pages ===\n")

print("1. Master Plan...")
mp_id, mp_url = create_page("RITA Production Refactor -- Master Plan", MASTER_PLAN)
time.sleep(1)

print("\n2. Token Budget & Work Planning...")
tb_id, tb_url = create_page("Token Budget and Daily Work Planning", TOKEN_BUDGET)
time.sleep(1)

print("\n3. Claude Cowork User Guide...")
cg_id, cg_url = create_page("How We Use Claude Cowork -- User Guide", COWORK_GUIDE)

print("\n=== Done ===")
if mp_url: print(f"\nMaster Plan:     {mp_url}")
if tb_url: print(f"Token Budget:    {tb_url}")
if cg_url: print(f"Cowork Guide:    {cg_url}")
