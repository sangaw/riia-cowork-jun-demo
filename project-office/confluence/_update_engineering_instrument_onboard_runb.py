"""
Update the Engineering Confluence page (76611602) after Feature 09 Run B —
Instrument Onboard UI panel (task-brief-20260518-0635).

Changes:
  1. Add a new "Feature 09 Run B — Instrument Onboard UI (Ops Dashboard)" section
     describing the JS functions, DOM elements, and window bindings.

Run from project root:
    python project-office/confluence/_update_engineering_instrument_onboard_runb.py
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

# ── 2. Add Feature 09 Run B UI section ───────────────────────────────────────
MARKER = "instrument-onboard-runb-2026-05-18"

RUNB_SECTION = (
    f"\n<!-- {MARKER} -->\n"
    "<h2>Feature 09 Run B &mdash; Instrument Onboard UI (Ops Dashboard) <small>2026-05-18</small></h2>\n"
    "<p>Adds an Instrument Onboarding sub-panel to the Daily Ops section of the Ops dashboard "
    "(<code>sec-dailyops</code> in <code>ops.html</code>). Ops users can search Yahoo Finance "
    "by keyword, select a result, and trigger the full onboarding pipeline without leaving the dashboard.</p>\n"

    "<h3>JS Module: <code>dashboard/js/ops/daily-ops.js</code></h3>\n"
    "<p>Two new async functions added to the existing module:</p>\n"
    "<table>\n"
    "  <thead><tr><th>Function</th><th>Description</th></tr></thead>\n"
    "  <tbody>\n"
    "  <tr>\n"
    "    <td><code>searchInstrument()</code></td>\n"
    "    <td>Reads query from <code>#dops-search-input</code>; client-side guard rejects queries &lt; 2 chars; "
    "calls <code>GET /api/v1/instrument/search?q=...</code> via <code>api()</code>; renders clickable result rows "
    "into <code>#dops-search-results</code>; handles empty-results and API error states.</td>\n"
    "  </tr>\n"
    "  <tr>\n"
    "    <td><code>onboardInstrument(ticker, name, exchange, currency, country)</code></td>\n"
    "    <td>Posts to <code>POST /api/v1/instrument/onboard</code>; shows progress in <code>#dops-onboard-status</code>; "
    "handles 409 Duplicate, 502 yfinance unreachable, and generic non-2xx errors with distinct messages.</td>\n"
    "  </tr>\n"
    "  </tbody>\n"
    "</table>\n"

    "<h3>DOM Elements (inserted into <code>sec-dailyops</code>)</h3>\n"
    "<table>\n"
    "  <thead><tr><th>Element ID</th><th>Purpose</th></tr></thead>\n"
    "  <tbody>\n"
    "  <tr><td><code>dops-search-input</code></td><td>Text input for instrument keyword search</td></tr>\n"
    "  <tr><td><code>dops-search-btn</code></td><td>Button that calls <code>window.searchInstrument()</code></td></tr>\n"
    "  <tr><td><code>dops-search-results</code></td><td>Div rendered with clickable search result rows</td></tr>\n"
    "  <tr><td><code>dops-onboard-status</code></td><td>Div showing onboard progress and success/error messages</td></tr>\n"
    "  </tbody>\n"
    "</table>\n"

    "<h3>Window Bindings (<code>dashboard/js/ops/main.js</code>)</h3>\n"
    "<ul>\n"
    "  <li><code>window.searchInstrument</code> &mdash; bound from <code>daily-ops.js</code> export; "
    "called by the search button <code>onclick</code> handler in <code>ops.html</code>.</li>\n"
    "  <li><code>window.onboardInstrument</code> &mdash; bound from <code>daily-ops.js</code> export; "
    "called from each search result row's onclick handler.</li>\n"
    "</ul>\n"

    "<h3>Error Handling</h3>\n"
    "<ul>\n"
    "  <li><strong>Query &lt; 2 chars:</strong> client-side guard; search button disabled with inline validation.</li>\n"
    "  <li><strong>Empty results:</strong> shows &ldquo;No results found for &lsquo;&hellip;&rsquo;&rdquo;.</li>\n"
    "  <li><strong>409 Duplicate:</strong> shows &ldquo;Already onboarded&rdquo; message.</li>\n"
    "  <li><strong>502 yfinance unreachable:</strong> shows &ldquo;Yahoo Finance is unavailable &mdash; try again shortly&rdquo;.</li>\n"
    "  <li><strong>Other non-2xx:</strong> shows <code>detail</code> field from HTTPException response.</li>\n"
    "</ul>\n"

    "<h3>RITA Dashboard — Dynamic Instrument Tabs</h3>\n"
    "<p>The RITA dashboard instrument tab bar (<code>rita.html</code>) was converted from hardcoded buttons "
    "to a dynamic list. On page load, <code>loadInstrumentTabs()</code> in <code>dashboard/js/rita/main.js</code> "
    "calls <code>GET /api/v1/experience/rita/geography-overview</code>, extracts all available instruments "
    "across regions, and renders them as tab buttons. Any instrument enabled in Ops Daily Ops "
    "(<code>is_available=True</code>) automatically appears as a selectable tab in RITA on next load. "
    "Falls back to the four static tabs (NIFTY/BANKNIFTY/ASML/NVIDIA) if the API is unavailable.</p>\n"

    "<h3>QA</h3>\n"
    "<p>21 unit tests in <code>tests/unit/test_instrument_onboard.py</code>; all pass (21/21). "
    "Covers: search results, equity-only filtering (service layer), 400/409/502 error paths, "
    "onboard success + all response fields, duplicate ticker, yfinance failure on both endpoints. "
    "FC-IMP gate passed &mdash; all named imports verified against source module exports.</p>\n"

    "<p><strong>Commit:</strong> a86669b &mdash; Branch: worktree-agent-a19ee4b2d4c56552a</p>\n"
)

if MARKER in body_updated:
    print("NOTE: Run B section already present — skipping")
else:
    body_updated = body_updated + RUNB_SECTION
    print("OK: Feature 09 Run B UI section appended")

# ── 3. Bump version date in header ───────────────────────────────────────────
for old_date in ("2026-05-17", "2026-05-16", "2026-05-15", "2026-05-14",
                  "2026-05-11", "2026-05-08", "2026-04-30", "2026-04-29"):
    if f"<strong>Date:</strong> {old_date}" in body_updated:
        body_updated = body_updated.replace(
            f"<strong>Date:</strong> {old_date}",
            "<strong>Date:</strong> 2026-05-18",
            1,
        )
        print(f"OK: version date bumped from {old_date} to 2026-05-18")
        break
else:
    if "<strong>Date:</strong> 2026-05-18" in body_updated:
        print("NOTE: date already at 2026-05-18")

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
