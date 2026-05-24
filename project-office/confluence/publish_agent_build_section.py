"""
Create the "Agent Build" section on Confluence at the same level as "Engineering Documentation".

Parent: RIIA App (76611585)
Sibling: Engineering Documentation (65404944)

Page structure:
  Agent Build (section root)
  └── AI Skills & Slash Commands (child page — created in one pass)

Run from project root:
  python3 project-office/confluence/publish_agent_build_section.py
"""
import urllib.request, urllib.error, json, base64
from pathlib import Path

import os

EMAIL  = os.environ.get("CONFLUENCE_EMAIL", "contact@ravionics.nl")
BASE   = "https://ravionics.atlassian.net/wiki/rest/api"
SPACE  = "RIIAProjec"

def _load_token() -> str:
    if os.environ.get("CONFLUENCE_API_TOKEN"):
        return os.environ["CONFLUENCE_API_TOKEN"]
    key_file = Path(__file__).parent.parent.parent / "confluence-api-key.txt"
    if key_file.exists():
        return key_file.read_text().splitlines()[0].strip()
    raise RuntimeError(
        "Set CONFLUENCE_API_TOKEN env var or place token in project root confluence-api-key.txt"
    )

TOKEN  = _load_token()

RIIA_APP_ID = "76611585"   # RIIA App — parent of Engineering, same level target

creds   = base64.b64encode(f"{EMAIL}:{TOKEN}".encode()).decode()
HEADERS = {
    "Authorization": f"Basic {creds}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}


def req(method, path, body=None):
    data = json.dumps(body).encode() if body else None
    r = urllib.request.Request(f"{BASE}/{path}", data=data, headers=HEADERS, method=method)
    try:
        with urllib.request.urlopen(r) as resp:
            return json.loads(resp.read()), resp.status
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode()), e.code


def create_page(title, html, parent_id):
    body, status = req("POST", "content", {
        "type": "page",
        "title": title,
        "space": {"key": SPACE},
        "ancestors": [{"id": parent_id}],
        "body": {"storage": {"value": html, "representation": "storage"}},
    })
    if status not in (200, 201):
        raise RuntimeError(f"Create failed ({status}): {body}")
    page_id  = body["id"]
    page_url = body["_links"]["base"] + body["_links"]["webui"]
    print(f"  Created: '{title}' [{page_id}] → {page_url}")
    return page_id, page_url


# ── Page 1: Agent Build (section root) ──────────────────────────────────────

AGENT_BUILD_ROOT_HTML = """\
<p>
  <strong>Last updated:</strong> 2026-05-24 &nbsp;|&nbsp;
  <strong>Maintainer:</strong> Ops Engineer skill
  (<code>project-office/skills/skill-ops-engineer.md</code>)
</p>
<p>
  This section documents the AI-driven operations layer for RITA &mdash; the slash commands,
  skill files, and knowledge bases that power every deployment, debug session, and feature build.
</p>

<h2>Why We Have AI Skills</h2>
<p>
  RITA&rsquo;s operations and debugging work is driven by Claude Code slash commands backed by
  structured skill files. These skills encode the institutional knowledge of every deployment,
  every failure pattern, and every fix procedure in a machine-readable format. This approach:
</p>
<ul>
  <li><strong>Prevents knowledge loss</strong> &mdash; every incident is written to
      <code>DEPLOYMENT_KNOWLEDGE.md</code> so the next session starts informed, not from scratch.</li>
  <li><strong>Makes diagnostics repeatable</strong> &mdash; a 5-phase debug protocol replaces
      ad-hoc investigation; each phase has a clear output and exit condition.</li>
  <li><strong>Scales to any operator</strong> &mdash; a new session or a new engineer types
      <code>/debug-model-build</code> and gets the same structured run-book that an experienced
      ops engineer would follow.</li>
  <li><strong>Captures tribal knowledge</strong> &mdash; Cloudflare caching stale JS, JWT expiry
      causing silent 401s, relative config paths writing to read-only image layers &mdash; these
      subtleties are recorded once and checked automatically on every future session.</li>
</ul>

<h2>How to Invoke a Skill</h2>
<p>Type the slash command directly in the Claude Code chat window:</p>
<ac:structured-macro ac:name="code" ac:schema-version="1">
  <ac:parameter ac:name="language">bash</ac:parameter>
  <ac:plain-text-body><![CDATA[/debug-model-build
/aws-production-deploy
/start-day
/end-day
/enhance
/fix-bug
/add-endpoint]]></ac:plain-text-body>
</ac:structured-macro>
<p>
  Claude Code loads the corresponding skill file from
  <code>project-office/skills/</code> and the command file from
  <code>.claude/commands/</code>, then executes the defined protocol.
  No parameters are needed &mdash; the skill reads context (git log, PLAN_STATUS.md,
  DEPLOYMENT_KNOWLEDGE.md) automatically.
</p>
<p><strong>To add a new slash command:</strong> create
  <code>.claude/commands/&lt;command-name&gt;.md</code> with a frontmatter
  <code>description:</code> line and instructions. The skill file with detailed knowledge
  lives separately in <code>project-office/skills/skill-&lt;name&gt;.md</code>.
</p>

<h2>Skills Catalogue</h2>
<table>
  <thead>
    <tr>
      <th>Slash Command</th>
      <th>Skill File</th>
      <th>Purpose</th>
      <th>When to Use</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>/debug-model-build</code></td>
      <td><code>skill-model-build-debug.md</code></td>
      <td>5-phase diagnostic for stuck, failed, or silent RITA model builds</td>
      <td>Pipeline button does nothing; 401 on POST /pipeline; PermissionError; training stuck in pending/running</td>
    </tr>
    <tr>
      <td><code>/aws-production-deploy</code></td>
      <td><code>skill-ops-engineer.md</code></td>
      <td>Safe 7-phase production deployment to EC2 via GitHub Actions</td>
      <td>Deploying a new feature, fix, or config change to production</td>
    </tr>
    <tr>
      <td><code>/enhance</code></td>
      <td><code>skill-add-*-feature.md</code> (orchestrator)</td>
      <td>Multi-agent feature orchestrator — Engineer + QA + TechWriter in sequence</td>
      <td>Adding a new feature to RITA, FnO, Ops, or DS dashboard</td>
    </tr>
    <tr>
      <td><code>/start-day</code></td>
      <td><code>skill-start-of-day.md</code></td>
      <td>Reads PLAN_STATUS.md, reports today&rsquo;s tasks, blockers, and risks</td>
      <td>Beginning of every work session</td>
    </tr>
    <tr>
      <td><code>/end-day</code></td>
      <td><code>skill-end-of-day.md</code></td>
      <td>Runs 5 mandatory end-of-day steps: PLAN_STATUS + run log + HITL + Confluence + git commit</td>
      <td>End of every work session</td>
    </tr>
    <tr>
      <td><code>/fix-bug</code></td>
      <td><code>skill-fix-js-bug.md</code></td>
      <td>Diagnose and fix RITA dashboard JS bugs by tracing code (no server start)</td>
      <td>JS console errors, broken UI interactions, fetch failures</td>
    </tr>
    <tr>
      <td><code>/add-endpoint</code></td>
      <td><code>skill-add-api-endpoint.md</code></td>
      <td>Add or modify a FastAPI endpoint with correct tier placement</td>
      <td>New API route needed; existing endpoint needs a change</td>
    </tr>
    <tr>
      <td><code>/refresh-all-instruments-data</code></td>
      <td>&mdash;</td>
      <td>Refresh all instruments&rsquo; price data from yfinance and update DB cache</td>
      <td>Daily data update or after adding a new instrument</td>
    </tr>
  </tbody>
</table>

<h2>Knowledge Base Files</h2>
<table>
  <thead>
    <tr><th>File</th><th>Purpose</th><th>Updated when</th></tr>
  </thead>
  <tbody>
    <tr>
      <td><code>project-office/ops-deployments/DEPLOYMENT_KNOWLEDGE.md</code></td>
      <td>Institutional memory for all RITA production deployments and model build incidents.
          Contains PATTERN-NNN (infra/deploy) and BUILD-PATTERN-NNN (model pipeline) entries.</td>
      <td>After every incident or successful deploy</td>
    </tr>
    <tr>
      <td><code>PLAN_STATUS.md</code></td>
      <td>Daily work tracker &mdash; current sprint, task status, blockers, session notes</td>
      <td>Start and end of every session</td>
    </tr>
    <tr>
      <td><code>project-office/skills/</code></td>
      <td>Skill files: detailed how-to knowledge for each slash command</td>
      <td>After any incident that reveals a gap or after a skills improvement run</td>
    </tr>
  </tbody>
</table>
"""

# ── Page 2: /debug-model-build deep-dive (child of Agent Build root) ────────

DEBUG_SKILL_HTML = """\
<p>
  <strong>Command:</strong> <code>/debug-model-build</code> &nbsp;|&nbsp;
  <strong>Skill file:</strong> <code>project-office/skills/skill-model-build-debug.md</code><br/>
  <strong>Knowledge base:</strong> <code>project-office/ops-deployments/DEPLOYMENT_KNOWLEDGE.md</code>
  &mdash; Known Model Build Failure Patterns section
</p>

<h2>Why This Skill Exists</h2>
<p>
  The RITA DQN training pipeline runs in a background daemon thread. When it fails,
  the API still returns <code>202 Accepted</code> immediately &mdash; the failure is completely
  silent from the browser&rsquo;s perspective. Without a structured diagnostic, an operator
  would need to know which log events to grep, which DB tables to query, how to interpret
  OOM-killed container state, and how Cloudflare caching interacts with deployed JS fixes.
  This skill encodes all of that knowledge in a 5-phase protocol.
</p>

<h2>How to Invoke</h2>
<ac:structured-macro ac:name="code" ac:schema-version="1">
  <ac:parameter ac:name="language">bash</ac:parameter>
  <ac:plain-text-body><![CDATA[/debug-model-build]]></ac:plain-text-body>
</ac:structured-macro>
<p>
  Claude immediately reads <code>DEPLOYMENT_KNOWLEDGE.md</code>, scans all known patterns,
  attempts SSH to EC2, and walks through diagnostics autonomously. The user only needs to
  describe what they observed &mdash; Claude does the rest.
</p>

<h2>When to Invoke</h2>
<ul>
  <li>Pipeline button appears to do nothing (no spinner, no status update in DS dashboard)</li>
  <li><code>401 Unauthorized</code> on <code>POST /api/v1/pipeline</code> in browser DevTools console</li>
  <li><code>PermissionError</code> or <code>pipeline.failed</code> logged immediately after a 202 response</li>
  <li>Training run stuck in <code>pending</code> or <code>running</code> for more than 5 minutes</li>
  <li>No model <code>.zip</code> file after a pipeline completes</li>
  <li>Sharpe = 0, zero trades in backtest results</li>
  <li>Container OOM-killed during training</li>
</ul>

<h2>The 5-Phase Protocol</h2>
<table>
  <thead>
    <tr><th>Phase</th><th>What it does</th><th>Output</th></tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>1 &mdash; Pre-flight</strong></td>
      <td>Read <code>DEPLOYMENT_KNOWLEDGE.md</code> Known Model Build Failure Patterns.
          Match symptom against all known patterns.</td>
      <td>Pattern match or &ldquo;no known match&rdquo;</td>
    </tr>
    <tr>
      <td><strong>2 &mdash; Gather Context</strong></td>
      <td>Reads prior agent notes, git log, PLAN_STATUS.md.
          Asks user only for information not available in the codebase.</td>
      <td>Instrument, trigger method, observed symptom confirmed</td>
    </tr>
    <tr>
      <td><strong>3 &mdash; Remote Diagnostics</strong></td>
      <td>SSH to EC2. Pre-debug checklist: Cloudflare cache status, nginx access log
          (real user IPs vs local curl), production config path. Then: container logs,
          model artifacts, DB training run status, memory &amp; OOM state.</td>
      <td>Raw diagnostic data from production</td>
    </tr>
    <tr>
      <td><strong>4 &mdash; Diagnose and Fix</strong></td>
      <td>Decision tree maps findings to root cause. Applies fix (or walks user through it).
          Can generate a fresh JWT server-side to test endpoints directly.</td>
      <td><em>Root cause: one sentence. Fix: exact steps.</em></td>
    </tr>
    <tr>
      <td><strong>5 &mdash; Knowledge Base Update</strong></td>
      <td>New failure pattern → appended to <code>DEPLOYMENT_KNOWLEDGE.md</code>.
          Known pattern recurred → Recurrences counter incremented. Committed to both repos.</td>
      <td>Knowledge base updated; debug session summary</td>
    </tr>
  </tbody>
</table>

<h2>Pre-Debug Checklist (Phase 3 — runs before touching container logs)</h2>
<p>
  Three quick checks that cover the most common silent failures in under 2 minutes:
</p>
<ac:structured-macro ac:name="code" ac:schema-version="1">
  <ac:parameter ac:name="language">bash</ac:parameter>
  <ac:plain-text-body><![CDATA[# 1. Cloudflare serving stale JS? (BUILD-PATTERN-009)
curl -sI https://riia.ravionics.nl/dashboard/js/shared/api.js | grep -i cf-cache-status
# HIT = users getting old JS → Cloudflare Dashboard → Purge Everything
# BYPASS = OK

# 2. Real browser traffic — only health checks? (JWT expired or stale JS)
tail -50 /var/log/nginx/access.log | grep -v '127.0.0.1'
# Only GET /health from 172.69.x.x = no POSTs reaching server → stale JS or expired token

# 3. Production config paths correct? (BUILD-PATTERN-010)
docker exec rita python3 -c "from rita.config import settings; print(settings.model.path)"
# Expected: /app/rita_output/models
# If: models (relative) → production.yaml missing absolute path override]]></ac:plain-text-body>
</ac:structured-macro>

<h2>Known Model Build Failure Patterns (as of 2026-05-24)</h2>
<table>
  <thead>
    <tr><th>#</th><th>Pattern</th><th>Key Symptom</th><th>Root Cause</th></tr>
  </thead>
  <tbody>
    <tr><td>001</td><td>CSV not found for instrument</td>
        <td><code>FileNotFoundError</code> near <code>ml_dispatch.load_data</code></td>
        <td>OHLCV CSV not synced to EC2 before triggering pipeline</td></tr>
    <tr><td>002</td><td>OOM kill during training</td>
        <td><code>OOMKilled=true</code>; training stuck in <code>running</code></td>
        <td>stable-baselines3 DQN buffer exhausts EC2 instance memory</td></tr>
    <tr><td>003</td><td>Training stuck in <code>pending</code></td>
        <td>202 returned, DB row stays <code>pending</code>; no <code>ml_dispatch.load_data</code></td>
        <td>Container restarted between 202 and thread first log; daemon thread lost</td></tr>
    <tr><td>004</td><td>ZIP missing despite <code>training_complete</code></td>
        <td>Log says complete but no <code>.zip</code> file</td>
        <td>Disk full; <code>model.save()</code> fails silently</td></tr>
    <tr><td>005</td><td>Sharpe = 0 after successful training</td>
        <td><code>val_sharpe=0.0</code>, <code>val_trades=0</code> in history CSV</td>
        <td>Validation episode exception silently swallowed in <code>ml_dispatch.train()</code></td></tr>
    <tr><td>006</td><td>Wrong instrument trained</td>
        <td>ZIP exists but for wrong instrument</td>
        <td><code>active_instrument_id</code> in DB doesn&rsquo;t match user&rsquo;s intent</td></tr>
    <tr><td>007</td><td>Backtest never starts</td>
        <td><code>training_complete</code> logged, ZIP exists, no backtest in dashboard</td>
        <td><code>sim_start</code>/<code>sim_end</code> date parsing failure in pipeline thread</td></tr>
    <tr><td>008</td><td>Pipeline POST silently fails with 401</td>
        <td>Pipeline button does nothing; no POST in container logs</td>
        <td><code>shared/api.js</code> <code>api()</code> missing <code>Authorization: Bearer</code> header</td></tr>
    <tr><td>009</td><td>Cloudflare caches stale JS after deploy</td>
        <td><code>CF-Cache-Status: HIT</code>; only <code>/health</code> requests from browser</td>
        <td>Cloudflare caches <code>api.js</code> for 4 hours; users get old JS even after deploy</td></tr>
    <tr><td>010</td><td>PermissionError &mdash; model dir not writable</td>
        <td><code>pipeline.failed</code> immediately; <code>PermissionError: models/NIFTY</code></td>
        <td>Relative <code>model.path</code> in <code>production.yaml</code> resolves to read-only image layer</td></tr>
  </tbody>
</table>

<h2>Safety Rules</h2>
<ul>
  <li>Never skip Phase 1 knowledge base read &mdash; known patterns resolve most cases in under 2 minutes</li>
  <li>Never re-trigger pipeline without knowing the root cause &mdash; re-running a broken config wastes EC2 resources</li>
  <li>Never run <code>force_retrain=true</code> on production without user confirmation &mdash; overwrites the existing model ZIP</li>
  <li>Never skip Phase 5 &mdash; every new failure must be recorded</li>
</ul>
"""

# ── Run ──────────────────────────────────────────────────────────────────────

print("Creating Agent Build section on Confluence...")

root_id, root_url = create_page(
    "Agent Build",
    AGENT_BUILD_ROOT_HTML,
    RIIA_APP_ID,
)

child_id, child_url = create_page(
    "/debug-model-build — Model Build Debugger",
    DEBUG_SKILL_HTML,
    root_id,
)

print()
print("Done.")
print(f"  Section root : {root_url}")
print(f"  Debug skill  : {child_url}")
