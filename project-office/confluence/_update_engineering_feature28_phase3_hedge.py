"""
Update the Engineering Confluence page (76611602) after Feature 28 Phase 3 —
Portfolio Hedge 4-tab wizard completion + bug fix + UX polish (2026-06-02).

Run from project root:
    python project-office/confluence/_update_engineering_feature28_phase3_hedge.py
"""
import urllib.request, urllib.error, json, base64
from pathlib import Path

PAGE_ID = "76611602"
BASE    = "https://ravionics.atlassian.net/wiki/rest/api"

MARKER = "feature28-phase3-hedge-2026-06-02"

FEATURE28_PHASE3_SECTION = (
    f"\n<!-- {MARKER} -->\n"
    "<h2>Feature 28 Phase 3 &mdash; Portfolio Hedge 4-tab Wizard <small>2026-06-02</small></h2>\n"
    "<p>Completes the Hedging Wizard in the FnO Portfolio Hedge section: a 4-tab flow "
    "(Discover &rarr; Selection &rarr; Allocation &rarr; Hedge) that takes the user's saved "
    "portfolio and computes per-instrument Black-Scholes hedge parameters at a chosen duration "
    "and coverage level. Commit: <strong>13dc6bb</strong>.</p>\n"

    "<h3>Bug Fix</h3>\n"
    "<p><code>portfolio_hedge.py</code>: <code>sa.JSON</code> column deserialises holdings as "
    "plain dicts; code was using attribute access (<code>h.instrument_id</code>) causing "
    "<code>AttributeError</code>. Fixed by parsing each dict through "
    "<code>HoldingItem(**h) if isinstance(h, dict)</code> before the holding loop.</p>\n"

    "<h3>API Endpoint</h3>\n"
    "<table>\n"
    "  <thead><tr><th>Method</th><th>Path</th><th>Tier</th><th>Auth</th><th>Notes</th></tr></thead>\n"
    "  <tbody>\n"
    "    <tr><td>GET</td><td>/api/v1/experience/fno/portfolio-hedge</td><td>Experience</td><td>JWT</td>"
    "    <td>Params: <code>coverage</code> 0&ndash;100 (default 50), <code>duration</code> 1m|3m|1y (default 1y). "
    "    Returns <code>PortfolioHedgeResponse</code>: holdings with <code>ann_vol_pct</code>, "
    "    <code>cost_pct</code>, <code>call_sell_cost_pct</code>, <code>strike_pct</code>, "
    "    <code>strike_label</code>, <code>protected_pct</code>, <code>risk_score</code>, "
    "    <code>duration</code>; plus <code>aggregate</code> and <code>coverage</code>.</td></tr>\n"
    "  </tbody>\n"
    "</table>\n"

    "<h3>Frontend (portfolio-hedge.js)</h3>\n"
    "<ul>\n"
    "  <li><strong>Discover tab</strong>: Duration pills (1M / 3M / 1Y); holdings rendered as "
    "  proper <code>&lt;table&gt;</code> inside <code>.tbl-wrap</code> (max-height 230px, sticky thead, "
    "  scrolls after 5 rows). Concept block explains hedging + horizon choice.</li>\n"
    "  <li><strong>Selection tab</strong>: Per-instrument Put Buy vs Sell Call with BS-priced buttons; "
    "  auto-recommend badge (risk &ge; 3 &rarr; Put Buy). Same .tbl-wrap scroll pattern. "
    "  Concept block explains the two strategies.</li>\n"
    "  <li><strong>Allocation tab</strong>: &sigma;-anchored scenario matrix (&minus;2&sigma; / "
    "&minus;1&sigma; / Flat / +1&sigma;); aggregate portfolio row in <code>&lt;tfoot&gt;</code>; "
    "  summary strip (monthly premium + max drawdown floor). .tbl-wrap max-height 240px. "
    "  Concept block explains &sigma; and how to read the matrix.</li>\n"
    "  <li><strong>Hedge tab</strong>: Confirmed strategy table + coverage dial + payoff chart "
    "  (pp / put spread / collar) + scenario P&amp;L table. Place hedge orders CTA.</li>\n"
    "</ul>\n"

    "<h3>Spec Updates (3G)</h3>\n"
    "<ul>\n"
    "  <li><code>Spec_HTML_Code.md</code>: full Portfolio Hedge wizard section added to fno.html entry "
    "  (all 4 panel IDs, tbody IDs, tbl-wrap heights, state banners).</li>\n"
    "  <li><code>Spec_Python_Code.md</code>: <code>portfolio_hedge.py</code> row added to Experience Layer table "
    "  with endpoint contract, schema fields, and HoldingItem dict-parse note.</li>\n"
    "  <li><code>Spec_JS_Code.md</code> + <code>Spec_RITA_App.md</code>: updated in commit 435f648.</li>\n"
    "</ul>\n"
)


def _auth(email: str) -> str:
    import os
    token = os.environ.get("CONFLUENCE_API_TOKEN")
    if not token:
        key_file = Path("confluence-api-key.txt")
        token = key_file.read_text().splitlines()[0].strip()
        email = key_file.read_text().splitlines()[1].strip()
    return base64.b64encode(f"{email}:{token}".encode()).decode(), email


def _get_page(auth: str):
    req = urllib.request.Request(
        f"{BASE}/content/{PAGE_ID}?expand=body.storage,version",
        headers={"Authorization": f"Basic {auth}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def _update_page(auth: str, page: dict, new_body: str):
    ver = page["version"]["number"] + 1
    payload = json.dumps({
        "version": {"number": ver},
        "title": page["title"],
        "type": "page",
        "body": {"storage": {"value": new_body, "representation": "storage"}},
    }).encode()
    req = urllib.request.Request(
        f"{BASE}/content/{PAGE_ID}",
        data=payload,
        method="PUT",
        headers={"Authorization": f"Basic {auth}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


if __name__ == "__main__":
    import os, sys
    email = os.environ.get("CONFLUENCE_EMAIL", "contact@ravionics.nl")
    auth, email = _auth(email)

    print(f"Fetching Engineering page {PAGE_ID}...")
    page  = _get_page(auth)
    body  = page["body"]["storage"]["value"]
    ver   = page["version"]["number"]
    print(f"  Title: {page['title']}  (version {ver}, {len(body)} chars)")

    if MARKER in body:
        print("NOTE: Feature 28 Phase 3 section already present — skipping.")
        sys.exit(0)

    new_body = body + FEATURE28_PHASE3_SECTION
    result   = _update_page(auth, page, new_body)
    new_ver  = result["version"]["number"]
    url      = result["_links"]["base"] + result["_links"]["webui"]
    print(f"OK: Page updated to v{new_ver}")
    print(f"  URL: {url}")
    print(f"\nDone. Engineering page: {url}")
