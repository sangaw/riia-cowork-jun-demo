"""
Update the Engineering Confluence page (76611602) after the Improve Observability
feature was merged (2026-05-08, commit af148b6).

Changes:
  1. Add POST /api/v1/client-error row to the System CRUD table
  2. Add observability note (structured logging) below the System CRUD table
  3. Bump version date in the page header to 2026-05-11
"""
import urllib.request, urllib.error, json, base64
from pathlib import Path

PAGE_ID = "76611602"
EMAIL   = "contact@ravionics.nl"
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

# ── 2. Add /api/v1/client-error row to System CRUD table ────────────────────
# Insert after the last row of the System CRUD table, before </tbody> of that table.
# Anchor: the /api/v1/metrics/summary row (last row currently in the System section).
METRICS_ROW = "    <tr><td>/api/v1/metrics/summary</td><td>GET</td><td>Structured Prometheus metrics summary</td></tr>"
CLIENT_ERROR_ROW = (
    "\n    <tr><td>/api/v1/client-error</td><td>POST</td>"
    "<td>System tier; no auth; accepts JS error payload "
    "(<code>type</code>, <code>message</code>, <code>stack</code>, "
    "<code>url</code>, <code>trace_id</code>); returns 204; "
    "writes to <code>logs/client-errors.jsonl</code></td></tr>"
)

if "/api/v1/client-error" in body_updated:
    print("NOTE: /api/v1/client-error row already present — skipping")
elif METRICS_ROW not in body_updated:
    print("WARNING: anchor row (/api/v1/metrics/summary) not found — skipping client-error row")
else:
    body_updated = body_updated.replace(METRICS_ROW, METRICS_ROW + CLIENT_ERROR_ROW, 1)
    print("OK: /api/v1/client-error row added to System CRUD table")

# ── 3. Add observability note below the System CRUD table ────────────────────
# Insert a paragraph after the closing </table> that follows the System CRUD section,
# which is immediately before the <h3>Workflow &mdash; heading.
WORKFLOW_H3 = "<h3>Workflow &mdash; <code>api/v1/workflow/</code></h3>"
OBS_NOTE = (
    "<p><strong>Structured observability (added 2026-05-08):</strong> "
    "All backend components now use a unified <code>log_event()</code> wrapper "
    "from <code>src/rita/logging_config.py</code>. Four rotating JSONL log files "
    "are written (<code>logs/app.jsonl</code>, <code>experience.jsonl</code>, "
    "<code>jobs.jsonl</code>, <code>client-errors.jsonl</code>). "
    "The experience layer emits an <code>experience.compose</code> provenance event "
    "per handler (per-source ok/empty/error). "
    "All three dashboards and the Mobile PWA use an <code>apiFetch()</code> wrapper "
    "with <code>X-Request-ID</code> header.</p>\n"
)

if "log_event()" in body_updated:
    print("NOTE: observability note already present — skipping")
elif WORKFLOW_H3 not in body_updated:
    print("WARNING: Workflow h3 heading not found — cannot place observability note")
else:
    body_updated = body_updated.replace(WORKFLOW_H3, OBS_NOTE + WORKFLOW_H3, 1)
    print("OK: structured observability note added")

# ── 4. Bump version date in header ───────────────────────────────────────────
for old_date in ("2026-05-11", "2026-04-30", "2026-04-29"):
    if f"<strong>Date:</strong> {old_date}" in body_updated:
        if old_date != "2026-05-11":
            body_updated = body_updated.replace(
                f"<strong>Date:</strong> {old_date}",
                "<strong>Date:</strong> 2026-05-11",
                1,
            )
            print(f"OK: version date bumped from {old_date} to 2026-05-11")
        else:
            print("NOTE: date already at 2026-05-11")
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
