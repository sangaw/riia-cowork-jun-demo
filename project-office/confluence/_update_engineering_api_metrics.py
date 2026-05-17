"""
Update the Engineering Confluence page (76611602) after Feature 08 R4+R5 —
API Layer Rationalization: session cache + API monitoring + api-metrics endpoint
+ Ops API Metrics panel (task-brief-20260517-1430).

Changes:
  1. Add a row to the Experience Tier endpoint table for GET /api/experience/ops/api-metrics
  2. Add a description of the new "API Metrics" panel in the Ops dashboard section
  3. Bump version date in the page header to 2026-05-17.

Run from project root:
    python project-office/confluence/_update_engineering_api_metrics.py
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

# ── 2. Add api-metrics endpoint row to Experience Tier table ─────────────────
MARKER_ENDPOINT = "api-metrics-endpoint-2026-05-17"

API_METRICS_ROW = (
    f"<!-- {MARKER_ENDPOINT} -->\n"
    "<tr>\n"
    "  <td><code>GET</code></td>\n"
    "  <td><code>/api/experience/ops/api-metrics</code></td>\n"
    "  <td>Aggregates <code>api_call_log</code> rows per path+method. Returns "
    "<code>ApiMetricsResponse(items: list[ApiMetricsRow])</code>. Each row contains: "
    "<code>path</code>, <code>method</code>, <code>call_count</code>, "
    "<code>p50_ms</code>, <code>p95_ms</code>, <code>error_count</code>, "
    "<code>error_rate_pct</code>, <code>last_called_at</code>. "
    "Query params: <code>limit</code> (default 200), <code>method</code>, "
    "<code>path_prefix</code>. No auth required.</td>\n"
    "  <td>No</td>\n"
    "</tr>\n"
)

if MARKER_ENDPOINT in body_updated:
    print("NOTE: api-metrics endpoint row already present — skipping")
else:
    # Look for the token-forecast row (last row in the Ops Experience Endpoints table added
    # in the previous session), then append our new row after it.
    ENDPOINT_ANCHOR_CANDIDATES = [
        "/api/experience/ops/token-forecast",
        "token-forecast",
        "/api/experience/ops/agent-builds",
        "/api/experience/ops/",
    ]
    anchor_found = None
    for candidate in ENDPOINT_ANCHOR_CANDIDATES:
        if candidate in body_updated:
            anchor_found = candidate
            break

    if anchor_found == "/api/experience/ops/token-forecast" or anchor_found == "token-forecast":
        # Find the closing </tr> after the token-forecast row and insert after it
        idx = body_updated.find(anchor_found)
        # Walk forward to find the closing </tr>
        tr_close = body_updated.find("</tr>", idx)
        if tr_close != -1:
            insert_pos = tr_close + len("</tr>")
            body_updated = body_updated[:insert_pos] + "\n" + API_METRICS_ROW + body_updated[insert_pos:]
            print("OK: api-metrics endpoint row inserted after token-forecast row")
        else:
            body_updated = body_updated + "\n" + API_METRICS_ROW
            print("NOTE: Could not find </tr> after token-forecast — appended to end")
    elif anchor_found is not None:
        # Insert before the anchor as a safe fallback
        body_updated = body_updated.replace(anchor_found, API_METRICS_ROW + anchor_found, 1)
        print(f"OK: api-metrics endpoint row inserted before: {anchor_found[:60]}")
    else:
        body_updated = body_updated + "\n" + API_METRICS_ROW
        print("NOTE: No anchor found — endpoint row appended to end of page body")

# ── 3. Add API Metrics panel description to Ops dashboard section ─────────────
MARKER_PANEL = "api-metrics-panel-2026-05-17"

API_METRICS_PANEL = (
    f"\n<!-- {MARKER_PANEL} -->\n"
    "<h3>Ops Dashboard &mdash; API Metrics Panel (2026-05-17)</h3>\n"
    "<p>A new <strong>API Metrics</strong> panel (<code>sec-api-metrics</code>) has been "
    "added to the Ops dashboard. It reads from <code>GET /api/experience/ops/api-metrics</code> "
    "and displays per-endpoint call statistics aggregated from the <code>api_call_log</code> "
    "database table populated by <code>ApiCallLogMiddleware</code>.</p>\n"
    "<h4>KPI Row</h4>\n"
    "<ul>\n"
    "  <li><strong>Total Calls</strong> — sum of <code>call_count</code> across all endpoints</li>\n"
    "  <li><strong>Unique Endpoints</strong> — number of distinct path+method combinations</li>\n"
    "  <li><strong>Overall Error Rate</strong> — weighted average <code>error_rate_pct</code></li>\n"
    "</ul>\n"
    "<h4>Filter Controls</h4>\n"
    "<ul>\n"
    "  <li><strong>Method</strong> filter (<code>ops-api-metrics-filter-method</code>) — "
    "filters rows by HTTP method (GET, POST, etc.)</li>\n"
    "  <li><strong>Path prefix</strong> filter (<code>ops-api-metrics-filter-prefix</code>) — "
    "filters rows by path prefix substring match</li>\n"
    "</ul>\n"
    "<h4>Data Table</h4>\n"
    "<p>Table columns: <strong>Path</strong>, <strong>Method</strong>, "
    "<strong>Calls</strong>, <strong>p50 (ms)</strong>, <strong>p95 (ms)</strong>, "
    "<strong>Errors</strong>, <strong>Error Rate %</strong>. "
    "Null latencies render as <code>&mdash;</code>. "
    "Empty state shows when no data or filter returns zero results.</p>\n"
    "<h4>Supporting Infrastructure</h4>\n"
    "<ul>\n"
    "  <li><code>ApiCallLogMiddleware</code> in <code>src/rita/middleware.py</code> — "
    "fires after each request, logs path/method/status_code/duration_ms to "
    "<code>api_call_log</code> table; skips health/docs/dashboard routes; "
    "swallows DB write errors without affecting the response.</li>\n"
    "  <li><code>api_call_log</code> table created by Alembic migration "
    "<code>e9f3b2c41a07</code>.</li>\n"
    "  <li><code>dashboard/js/ops/api-metrics.js</code> — JS module: "
    "<code>loadApiMetrics()</code>, <code>filterApiMetrics()</code>, "
    "<code>renderMetrics()</code>. Registered in <code>ops/main.js</code> "
    "section loader and window bindings.</li>\n"
    "  <li><code>dashboard/js/shared/api-cache.js</code> — shared session-scoped TTL "
    "cache factory. Applied to 5 redundant endpoints across 8 RITA dashboard JS modules "
    "to eliminate duplicate API calls.</li>\n"
    "  <li><code>riia-ai-org/agent-ops/aggregate_metrics.py</code> — new "
    "<code>compute_api_metrics()</code> function writes <code>api_metrics</code> block "
    "to <code>metrics.json</code>; alerts if <code>overall_error_rate_pct &gt; 5.0</code>.</li>\n"
    "</ul>\n"
)

if MARKER_PANEL in body_updated:
    print("NOTE: API Metrics panel description already present — skipping")
else:
    # Insert before the Agent Builds DB Write section (added in previous session)
    # or before the Slash Commands section as fallback
    PANEL_ANCHOR_CANDIDATES = [
        "<!-- agent-builds-db-write-2026-05-16 -->",
        "<h3>Agent Build Runs &mdash; DB Write Feature",
        "<h2>Slash Commands</h2>",
        "<h3>Slash Commands</h3>",
    ]

    panel_anchor_found = None
    for candidate in PANEL_ANCHOR_CANDIDATES:
        if candidate in body_updated:
            panel_anchor_found = candidate
            break

    if panel_anchor_found is not None:
        body_updated = body_updated.replace(
            panel_anchor_found, API_METRICS_PANEL + panel_anchor_found, 1
        )
        print(f"OK: API Metrics panel description inserted before: {panel_anchor_found[:70]}")
    else:
        body_updated = body_updated + "\n" + API_METRICS_PANEL
        print("NOTE: No anchor found — panel description appended to end of page body")

# ── 4. Bump version date in header ───────────────────────────────────────────
for old_date in ("2026-05-16", "2026-05-15", "2026-05-14", "2026-05-11", "2026-05-08",
                 "2026-04-30", "2026-04-29"):
    if f"<strong>Date:</strong> {old_date}" in body_updated:
        if old_date != "2026-05-17":
            body_updated = body_updated.replace(
                f"<strong>Date:</strong> {old_date}",
                "<strong>Date:</strong> 2026-05-17",
                1,
            )
            print(f"OK: version date bumped from {old_date} to 2026-05-17")
        else:
            print("NOTE: date already at 2026-05-17")
        break

# ── 5. Push update ───────────────────────────────────────────────────────────
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
