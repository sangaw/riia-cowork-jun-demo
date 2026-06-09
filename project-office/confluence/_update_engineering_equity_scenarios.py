"""
Update the Engineering Confluence page (76611602) — equity-scenarios.html
standalone page added as FnO-adjacent page navigated from the FnO sidebar.

This page was built outside /enhance and aligned to architecture conventions
(null guards + spec entries) in task-brief-20260609-1038.

Run from project root:
    python project-office/confluence/_update_engineering_equity_scenarios.py
"""
import urllib.request, urllib.error, json, base64
from pathlib import Path

PAGE_ID = "76611602"
BASE    = "https://ravionics.atlassian.net/wiki/rest/api"

MARKER = "equity-scenarios-standalone-2026-06-09"

EQUITY_SCENARIOS_SECTION = (
    f"\n<!-- {MARKER} -->\n"
    "<h2>Equity Scenarios Standalone Page &mdash; FnO Sidebar Navigation <small>2026-06-09</small></h2>\n"
    "<p><strong>equity-scenarios.html</strong> is a standalone page navigated from the FnO sidebar "
    "(<code>fno.html</code> nav link at line 430: "
    "<code>&lt;a class=\"nav-item p01\" href=\"/dashboard/equity-scenarios.html\"&gt;</code>). "
    "It is an equity stop-loss and target tracker with urgency-sorted instrument cards, "
    "price range bars, P&amp;L metrics, trade analysis chips, and action recommendations. "
    "Built outside <code>/enhance</code> and aligned to architecture conventions in this task.</p>\n"

    "<h3>Page Inventory</h3>\n"
    "<table>\n"
    "  <thead><tr><th>File</th><th>Description</th></tr></thead>\n"
    "  <tbody>\n"
    "    <tr>\n"
    "      <td><code>dashboard/equity-scenarios.html</code></td>\n"
    "      <td>Standalone page. Not a section in <code>fno.html</code>. "
    "      Served at <code>/dashboard/equity-scenarios.html</code>. "
    "      Script tag: <code>&lt;script type=\"module\" src=\"js/scenarios/equity-scenarios.js\"&gt;</code></td>\n"
    "    </tr>\n"
    "    <tr>\n"
    "      <td><code>dashboard/js/scenarios/equity-scenarios.js</code></td>\n"
    "      <td>Self-contained ES module. No imports from <code>fno/</code> or <code>shared/</code>. "
    "      Fetches 3 JSON data files, renders urgency-sorted instrument cards. "
    "      <code>init()</code> called at module bottom &mdash; no export. "
    "      Local helpers: <code>setEl()</code>, <code>INR()</code>, <code>PCT()</code>, "
    "      <code>KPCT()</code>, <code>daysAgo()</code>, <code>computeStatus()</code>, "
    "      <code>buildRecommendation()</code>, <code>renderBar()</code>, "
    "      <code>analyseTrades()</code>, <code>urgencyScore()</code>, <code>renderCard()</code>.</td>\n"
    "    </tr>\n"
    "  </tbody>\n"
    "</table>\n"

    "<h3>Data Layer (Static JSON &mdash; no REST endpoint)</h3>\n"
    "<table>\n"
    "  <thead><tr><th>File</th><th>Key fields read</th></tr></thead>\n"
    "  <tbody>\n"
    "    <tr>\n"
    "      <td><code>dashboard/data/scenarios/alerts.json</code></td>\n"
    "      <td><code>instruments[].{symbol, name, sl, target, status}</code>; "
    "      <code>triggered[].{symbol, alert_name, sl, target, created_on}</code></td>\n"
    "    </tr>\n"
    "    <tr>\n"
    "      <td><code>dashboard/data/scenarios/portfolio.json</code></td>\n"
    "      <td><code>last_updated</code>; "
    "      <code>holdings[].{symbol, qty, avg_cost, ltp, invested, cur_val, pnl, net_chg_pct, day_chg_pct}</code></td>\n"
    "    </tr>\n"
    "    <tr>\n"
    "      <td><code>dashboard/data/scenarios/tradebook.json</code></td>\n"
    "      <td><code>trades[].{symbol, trade_time, price}</code></td>\n"
    "    </tr>\n"
    "  </tbody>\n"
    "</table>\n"
    "<p><em>Future migration path</em>: a Portfolio-tier endpoint will merge the 3 JSON shapes "
    "into a single <code>GET /api/v1/experience/fno/equity-scenarios</code> response. "
    "The JS module is structured for this migration: a single <code>_fetchData()</code> "
    "function at the top of <code>init()</code> handles all 3 fetches.</p>\n"

    "<h3>Architecture Alignment Fixes Applied</h3>\n"
    "<table>\n"
    "  <thead><tr><th>#</th><th>Fix</th><th>Location</th></tr></thead>\n"
    "  <tbody>\n"
    "    <tr>\n"
    "      <td>1</td>\n"
    "      <td>Null guard: <code>(dayChg ?? 0).toFixed(2)</code> &mdash; guards against null "
    "      <code>day_chg_pct</code> field in portfolio.json</td>\n"
    "      <td><code>equity-scenarios.js</code> line 55 (<code>buildRecommendation()</code>)</td>\n"
    "    </tr>\n"
    "    <tr>\n"
    "      <td>2</td>\n"
    "      <td>Zero-division guard: <code>totalInvested &gt; 0 ? (totalPnl / totalInvested * 100) : 0</code> "
    "      &mdash; guards against NaN when holdings array is empty</td>\n"
    "      <td><code>equity-scenarios.js</code> line 309 (<code>init()</code>)</td>\n"
    "    </tr>\n"
    "  </tbody>\n"
    "</table>\n"

    "<h3>DOM IDs (10 elements)</h3>\n"
    "<p><code>kpi-invested</code>, <code>kpi-value</code>, <code>kpi-pnl</code>, "
    "<code>kpi-pnl-pct</code>, <code>kpi-status</code>, <code>kpi-status-sub</code>, "
    "<code>alert-strip</code>, <code>scenarios-grid</code>, <code>triggered-grid</code>, "
    "<code>last-updated</code></p>\n"

    "<h3>Spec Updates</h3>\n"
    "<ul>\n"
    "  <li><code>project-office/specs/Spec_RITA_App.md</code> &mdash; "
    "  Section 6: <code>equity-scenarios.html</code> standalone page entry added</li>\n"
    "  <li><code>project-office/specs/Spec_JS_Code.md</code> &mdash; "
    "  Section 3a: new &ldquo;Standalone FnO-Adjacent&rdquo; module subsection added "
    "  documenting <code>scenarios/equity-scenarios.js</code></li>\n"
    "</ul>\n"
)


def _auth():
    import os
    token = os.environ.get("CONFLUENCE_API_TOKEN")
    key_file = Path("confluence-api-key.txt")
    if not token:
        token = key_file.read_text().splitlines()[0].strip()
    email = os.environ.get("CONFLUENCE_EMAIL") or key_file.read_text().splitlines()[1].strip()
    return base64.b64encode(f"{email}:{token}".encode()).decode()


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
    import sys
    auth = _auth()

    print(f"Fetching Engineering page {PAGE_ID}...")
    page  = _get_page(auth)
    body  = page["body"]["storage"]["value"]
    ver   = page["version"]["number"]
    print(f"  Title: {page['title']}  (version {ver}, {len(body)} chars)")

    if MARKER in body:
        print("NOTE: equity-scenarios section already present — skipping.")
        sys.exit(0)

    new_body = body + EQUITY_SCENARIOS_SECTION
    result   = _update_page(auth, page, new_body)
    new_ver  = result["version"]["number"]
    url      = result["_links"]["base"] + result["_links"]["webui"]
    print(f"OK: Page updated to v{new_ver}")
    print(f"  URL: {url}")
    print(f"\nDone. Engineering page: {url}")
