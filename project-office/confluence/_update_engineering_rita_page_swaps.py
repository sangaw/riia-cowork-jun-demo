"""
Update the Engineering Confluence page (76611602) after the RITA Dashboard
page-swap feature (task-brief-20260511-1046).

Changes:
  1. Add a RITA Dashboard — Nav/Section Swap note to the Frontend Architecture section
     describing the Market Signals → Overview landing page reorganisation.
  2. Bump version date in the page header to 2026-05-11.

Run from project root:
    python project-office/confluence/_update_engineering_rita_page_swaps.py
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

# ── 2. Add RITA Dashboard nav/section note ───────────────────────────────────
# Anchor: insert the note before the first <h3>Workflow section heading so the
# note appears in the frontend / dashboard area of the page.
# If a dedicated Frontend Architecture h2/h3 is present, use that instead.

ANCHOR_CANDIDATES = [
    "<h2>Frontend Architecture</h2>",
    "<h3>Frontend Architecture</h3>",
    "<h2>RITA Dashboard</h2>",
    "<h3>RITA Dashboard</h3>",
    "<h3>Workflow &mdash; <code>api/v1/workflow/</code></h3>",
    "<h3>Workflow &mdash; <code>api/v1/workflow/</code></h3>",  # fallback duplicate
]

NAV_SWAP_NOTE = (
    "<h3>RITA Dashboard &mdash; Nav/Section Swap (2026-05-11)</h3>\n"
    "<p>The RITA dashboard (<code>rita.html</code>) nav order and landing section were "
    "reorganised as follows:</p>\n"
    "<ul>\n"
    "  <li><strong>Market Signals is now the Overview landing page</strong> "
    "(Phase 01, first nav item). Users arrive directly at instrument-aware market signals "
    "(RSI, MACD, Bollinger Bands, EMAs, ATR, Trend Score, charts, alert strip).</li>\n"
    "  <li><strong>Previous Overview content moved to &ldquo;Model Overview&rdquo;</strong> "
    "(Phase 03). Health KPIs, model status, and performance summary are accessible under "
    "the renamed &ldquo;Model Overview&rdquo; nav item (<code>sec-home</code>).</li>\n"
    "  <li><strong>Instrument selector tabs</strong> (<code>.inst-tab</code> / "
    "<code>itab-NIFTY</code>, <code>itab-BANKNIFTY</code>, <code>itab-ASML</code>, "
    "<code>itab-NVIDIA</code>) moved into <code>sec-market-signals</code> so instrument "
    "selection is available on the landing page without any prior navigation.</li>\n"
    "  <li><strong><code>nav.js _currentSection</code></strong> default changed from "
    "<code>'home'</code> to <code>'market-signals'</code>, and "
    "<code>loadMarketSignals()</code> is now called from the <code>window.load</code> "
    "handler so data populates on first paint.</li>\n"
    "</ul>\n"
    "<p>No backend API changes. All existing endpoints unchanged. "
    "Spec files updated: <code>Spec_RITA_App.md</code> (Sections/Phases table, "
    "Flow 1 description) and <code>Spec_JS_Code.md</code> (nav.js row, "
    "Section 6 loader pattern).</p>\n"
)

MARKER = "rita-dashboard-nav-swap-2026-05-11"

if MARKER in body_updated:
    print("NOTE: RITA Dashboard nav/section swap note already present — skipping")
else:
    anchor_found = None
    for candidate in ANCHOR_CANDIDATES:
        if candidate in body_updated:
            anchor_found = candidate
            break

    if anchor_found is None:
        # Append to end of body as a safe fallback
        body_updated = body_updated + f"\n<!-- {MARKER} -->\n" + NAV_SWAP_NOTE
        print("NOTE: No anchor found — note appended to end of page body")
    else:
        tagged_note = f"<!-- {MARKER} -->\n" + NAV_SWAP_NOTE
        body_updated = body_updated.replace(anchor_found, tagged_note + anchor_found, 1)
        print(f"OK: RITA Dashboard nav/section swap note inserted before: {anchor_found[:60]}")

# ── 3. Bump version date in header ───────────────────────────────────────────
for old_date in ("2026-05-08", "2026-05-11", "2026-04-30", "2026-04-29"):
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
