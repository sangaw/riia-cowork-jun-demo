"""
Update the Engineering Confluence page (76611602) after Feature 09 Run A —
Instrument Onboarding Pipeline (task-brief-20260518-0545).

Changes:
  1. Add two rows to the API Endpoint Inventory table:
     - GET  /api/v1/instrument/search
     - POST /api/v1/instrument/onboard
  2. Bump version date in the page header to 2026-05-18.

Run from project root:
    python project-office/confluence/_update_engineering_instrument_onboard.py
"""
import urllib.request, json, base64
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

# ── 2. Add instrument endpoint rows to the API table ─────────────────────────
MARKER = "instrument-onboard-2026-05-18"

INSTRUMENT_ROWS = (
    f"<!-- {MARKER} -->\n"
    "  <tr><td><code>GET /api/v1/instrument/search</code></td><td>GET</td><td>"
    "Workflow tier; no auth; query param <code>q</code> (min 2 chars); "
    "returns list of <code>{ticker, name, exchange, currency, country, quote_type}</code> "
    "from yfinance — EQUITY type only (Feature 09).</td></tr>\n"
    "  <tr><td><code>POST /api/v1/instrument/onboard</code></td><td>POST</td><td>"
    "Workflow tier; no auth; body <code>{ticker, name, exchange, currency, country_code, lot_size?}</code>; "
    "fetches OHLCV data via yfinance, normalises columns, seeds <code>market_cache</code> DB table "
    "and writes CSV to <code>data/raw/{TICKER}/</code> and <code>data/input/{TICKER}/</code>; "
    "returns <code>{status, ticker, rows_fetched, rows_seeded, raw_path, input_path}</code> (Feature 09).</td></tr>\n"
)

if MARKER in body_updated:
    print("NOTE: Instrument onboard rows already present — skipping")
else:
    ANCHOR = "</tbody>"
    if ANCHOR in body_updated:
        body_updated = body_updated.replace(ANCHOR, INSTRUMENT_ROWS + ANCHOR, 1)
        print("OK: Instrument endpoint rows inserted before </tbody>")
    else:
        print("WARNING: </tbody> anchor not found — rows appended to end of body")
        body_updated = body_updated + "\n" + INSTRUMENT_ROWS

# ── 3. Bump version date in header ───────────────────────────────────────────
for old_date in ("2026-05-17", "2026-05-16", "2026-05-15", "2026-05-14",
                  "2026-05-11", "2026-05-08", "2026-04-30", "2026-04-29"):
    if f"<strong>Date:</strong> {old_date}" in body_updated:
        if old_date != "2026-05-18":
            body_updated = body_updated.replace(
                f"<strong>Date:</strong> {old_date}",
                "<strong>Date:</strong> 2026-05-18",
                1,
            )
            print(f"OK: version date bumped from {old_date} to 2026-05-18")
        else:
            print("NOTE: date already at 2026-05-18")
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
