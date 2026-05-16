"""
Update the Engineering Confluence page (76611602) after Feature 07 —
Agent Build Runs DB Write (task-brief-20260515-1500).

Changes:
  1. Add Agent Builds / /enhance toolchain note describing:
     - upsert_run() and upsert_agents() write methods added to AgentBuildRepository
     - New standalone CLI helper: riia-ai-org/agent-ops/write_run_to_db.py
     - Alembic migration a3f9c1e82b5d applied (actual_tokens_total column)
     - /enhance Step 7 now calls write_run_to_db.py (non-blocking)
  2. Bump version date in the page header to 2026-05-16.

Run from project root:
    python project-office/confluence/_update_engineering_agent_builds_db_write.py
"""
import urllib.request, urllib.error, json, base64
from pathlib import Path

PAGE_ID = "76611602"
EMAIL   = Path("confluence-api-key.txt").read_text().splitlines()[1].strip()
TOKEN   = Path("confluence-api-key.txt").read_text().splitlines()[0].strip()
BASE    = "https://ravionics.atlassian.net/wiki/rest/api"

creds   = base64.b64encode(f"{EMAIL}:{TOKEN}".encode()).decode()
HEADERS = {"Authorization": f"Basic {creds}", "Content-Type": "application/json"}


def get(path):
    req = urllib.request.Request(f"{BASE}/{path}", headers=HEADERS)
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def put(path, payload):
    data = json.dumps(payload).encode()
    req  = urllib.request.Request(f"{BASE}/{path}", data=data, headers=HEADERS, method="PUT")
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


# ── 1. Fetch current page ────────────────────────────────────────────────────
page    = get(f"content/{PAGE_ID}?expand=body.storage,version")
title   = page["title"]
version = page["version"]["number"]
body    = page["body"]["storage"]["value"]

print(f"Fetched: '{title}' v{version}, {len(body)} chars")
body_updated = body

# ── 2. Add Agent Builds DB Write note ────────────────────────────────────────
MARKER = "agent-builds-db-write-2026-05-16"

AGENT_BUILDS_NOTE = (
    f"<!-- {MARKER} -->\n"
    "<h3>Agent Build Runs &mdash; DB Write Feature (2026-05-16)</h3>\n"
    "<p>Feature 07 closes the loop between the <code>/enhance</code> orchestrator and the "
    "<code>agent_build_runs</code> database table. Actual token counts are now written "
    "directly to the DB after each <code>/enhance</code> run, enabling the Agent Builds "
    "page to display estimated vs. actual token counts side by side.</p>\n"
    "<h4>Repository Write Methods (<code>src/rita/repositories/agent_builds.py</code>)</h4>\n"
    "<ul>\n"
    "  <li><code>upsert_run(run_data: dict)</code> &mdash; upserts an "
    "<code>AgentBuildRunModel</code> row by <code>run_id</code>; sets "
    "<code>recorded_at</code> on insert only; commits.</li>\n"
    "  <li><code>upsert_agents(run_id, agents, actual_tokens_total)</code> &mdash; "
    "upserts one <code>AgentBuildAgentModel</code> row per agent using "
    "<code>agent_id = f&quot;{run_id}-{role}&quot;</code>; maps <code>actual_tokens</code> "
    "dict to integer column; single commit per call.</li>\n"
    "</ul>\n"
    "<h4>CLI Helper Script (<code>riia-ai-org/agent-ops/write_run_to_db.py</code>)</h4>\n"
    "<p>Standalone script &mdash; same import pattern as <code>seed_agent_builds.py</code>. "
    "Accepts a run JSON file path and an optional <code>--actual-tokens</code> integer:</p>\n"
    "<pre>python riia-ai-org/agent-ops/write_run_to_db.py &lt;run_json_path&gt; "
    "[--actual-tokens &lt;integer&gt;]</pre>\n"
    "<ul>\n"
    "  <li>Validates required fields (<code>run_id</code>, <code>app</code>, "
    "<code>overall_status</code>) before upsert.</li>\n"
    "  <li>If <code>--actual-tokens</code> is supplied, injects the value back into the "
    "JSON file so <code>aggregate_metrics.py</code> (which reads JSON) stays consistent "
    "without code changes.</li>\n"
    "  <li>Catches <code>OperationalError</code> (missing table) with a clear message "
    "pointing to <code>alembic upgrade head</code>; exits 0 on success, 1 on error.</li>\n"
    "</ul>\n"
    "<h4>Alembic Migration</h4>\n"
    "<p>Migration <code>a3f9c1e82b5d</code> applied: adds "
    "<code>actual_tokens_total</code> column to <code>agent_build_agents</code> table "
    "(Integer, nullable).</p>\n"
    "<h4>/enhance Step 7 Integration</h4>\n"
    "<p><code>.claude/commands/enhance.md</code> Step 7 now calls "
    "<code>write_run_to_db.py</code> immediately after writing the run log JSON. "
    "The call is non-blocking &mdash; if the script exits 1, the orchestrator logs a "
    "warning and continues. No new API endpoints were added.</p>\n"
)

if MARKER in body_updated:
    print("NOTE: Agent Builds DB Write note already present — skipping")
else:
    # Try to insert before the /enhance slash command row or before the slash commands section
    ANCHOR_CANDIDATES = [
        "<h2>Slash Commands</h2>",
        "<h3>Slash Commands</h3>",
        "<h2>Agent Build</h2>",
        "<h3>Agent Build</h3>",
        "<h3>RITA Dashboard &mdash; Nav/Section Swap",
        "<!-- rita-dashboard-nav-swap-2026-05-11 -->",
    ]

    anchor_found = None
    for candidate in ANCHOR_CANDIDATES:
        if candidate in body_updated:
            anchor_found = candidate
            break

    if anchor_found is None:
        # Append to end of body as a safe fallback
        body_updated = body_updated + "\n" + AGENT_BUILDS_NOTE
        print("NOTE: No anchor found — note appended to end of page body")
    else:
        body_updated = body_updated.replace(anchor_found, AGENT_BUILDS_NOTE + anchor_found, 1)
        print(f"OK: Agent Builds DB Write note inserted before: {anchor_found[:60]}")

# ── 3. Bump version date in header ───────────────────────────────────────────
for old_date in ("2026-05-15", "2026-05-14", "2026-05-11", "2026-05-08", "2026-04-30", "2026-04-29"):
    if f"<strong>Date:</strong> {old_date}" in body_updated:
        if old_date != "2026-05-16":
            body_updated = body_updated.replace(
                f"<strong>Date:</strong> {old_date}",
                "<strong>Date:</strong> 2026-05-16",
                1,
            )
            print(f"OK: version date bumped from {old_date} to 2026-05-16")
        else:
            print("NOTE: date already at 2026-05-16")
        break

# ── 4. Push update ───────────────────────────────────────────────────────────
if body_updated == body:
    print("No changes made — page not updated")
else:
    payload = {
        "version": {"number": version + 1},
        "title":   title,
        "type":    "page",
        "body":    {"storage": {"value": body_updated, "representation": "storage"}},
    }
    result  = put(f"content/{PAGE_ID}", payload)
    new_ver = result["version"]["number"]
    url     = f"https://ravionics.atlassian.net/wiki{result['_links']['webui']}"
    print(f"OK: Page updated to v{new_ver}")
    print(f"  URL: {url}")
