"""
Update the Engineering Confluence page (76611602) after the /enhance orchestrator
and ms-last-updated market signals feature were added (2026-04-30).

Changes:
  1. Add /enhance to the slash commands table
  2. Update /api/v1/market-signals description to note ms-last-updated DOM element
  3. Bump version date in the page header
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

# ── 2. Update market-signals row ─────────────────────────────────────────────
OLD_MS = "<tr><td>/api/v1/market-signals</td><td>GET</td><td>Technical indicators (RSI, MACD, BB, ATR, EMA, trend)</td></tr>"
NEW_MS = "<tr><td>/api/v1/market-signals</td><td>GET</td><td>Technical indicators (RSI, MACD, BB, ATR, EMA, trend). <code>ms-last-updated</code> label in market signals panel now shows date &amp; time (2026-04-30).</td></tr>"

if OLD_MS not in body:
    print("WARNING: market-signals row not found at expected text — skipping that change")
    body_updated = body
else:
    body_updated = body.replace(OLD_MS, NEW_MS, 1)
    print("OK: market-signals row updated")

# ── 3. Add /enhance to slash commands table ──────────────────────────────────
# Insert before /fix-bug row (first entry in the commands table)
ENHANCE_ROW = "    <tr><td><code>/enhance</code></td><td>Orchestrate a full agent chain (PM &rarr; Architect &rarr; Engineer &rarr; QA &rarr; TechWriter) to plan, build, test, and document a feature</td></tr>\n"
FIX_BUG_ROW = "    <tr><td><code>/fix-bug</code></td>"

if ENHANCE_ROW.strip() in body_updated:
    print("NOTE: /enhance row already present — skipping")
elif FIX_BUG_ROW not in body_updated:
    print("WARNING: /fix-bug row not found — cannot locate insertion point for /enhance")
else:
    body_updated = body_updated.replace(FIX_BUG_ROW, ENHANCE_ROW + FIX_BUG_ROW, 1)
    print("OK: /enhance row added to slash commands table")

# ── 4. Bump version date in header ───────────────────────────────────────────
OLD_DATE = "<strong>Date:</strong> 2026-04-29"
NEW_DATE = "<strong>Date:</strong> 2026-04-30"
if OLD_DATE in body_updated:
    body_updated = body_updated.replace(OLD_DATE, NEW_DATE, 1)
    print("OK: version date bumped to 2026-04-30")

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
    result = put(f"content/{PAGE_ID}", payload)
    new_ver = result["version"]["number"]
    url     = f"https://ravionics.atlassian.net/wiki{result['_links']['webui']}"
    print(f"OK: Page updated to v{new_ver}")
    print(f"  URL: {url}")
