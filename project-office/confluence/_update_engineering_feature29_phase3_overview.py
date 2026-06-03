"""
Update the Engineering Confluence page (76611602) after Feature 29 Phase 3 —
FnO Overview redesign: KPI strip, allocation chart, hedge status card,
enriched holdings table, 3-source parallel fetch in my-portfolio.js (2026-06-03).

Run from project root:
    python project-office/confluence/_update_engineering_feature29_phase3_overview.py
"""
import urllib.request, urllib.error, json, base64
from pathlib import Path

PAGE_ID = "76611602"
BASE    = "https://ravionics.atlassian.net/wiki/rest/api"

MARKER = "feature29-phase3-overview-2026-06-03"

FEATURE29_PHASE3_SECTION = (
    f"\n<!-- {MARKER} -->\n"
    "<h2>Feature 29 Phase 3 &mdash; FnO Overview Redesign <small>2026-06-03</small></h2>\n"
    "<p>Redesigns the My Portfolio block inside the FnO Overview section (<code>#page-overview</code>) "
    "into a data-rich snapshot assembling information from three Experience-tier API endpoints "
    "in parallel via <code>Promise.allSettled</code>. Commit: <strong>3cc9d04</strong>.</p>\n"

    "<h3>API Endpoints Consumed (3 existing Experience-tier endpoints, no new backend code)</h3>\n"
    "<table>\n"
    "  <thead><tr><th>Method</th><th>Path</th><th>Tier</th><th>Auth</th><th>Purpose</th></tr></thead>\n"
    "  <tbody>\n"
    "    <tr><td>GET</td><td>/api/v1/experience/user-portfolio</td><td>Experience</td><td>JWT</td>"
    "    <td>Holdings, allocation_pct, total_value_eur, name, updated_at</td></tr>\n"
    "    <tr><td>GET</td><td>/api/experience/rita/geography-overview</td><td>Experience</td><td>No</td>"
    "    <td>Regions with instruments &mdash; return_1y_pct, risk_score, region label</td></tr>\n"
    "    <tr><td>GET</td><td>/api/v1/experience/fno/hedge-plan</td><td>Experience</td><td>JWT</td>"
    "    <td>hedged_ids, coverage, scenario_tab, updated_at (404 = no plan)</td></tr>\n"
    "  </tbody>\n"
    "</table>\n"

    "<h3>Frontend Changes</h3>\n"
    "<p><strong>my-portfolio.js</strong> (full replacement) &mdash; <code>dashboard/js/fno/my-portfolio.js</code>:</p>\n"
    "<ul>\n"
    "  <li><strong>3-source parallel fetch</strong>: <code>Promise.allSettled([portfolio, geo, hedgePlan])</code> "
    "  with per-source graceful fallback: portfolio 404 &rarr; empty state; geo fail &rarr; "
    "  <code>instMap={}</code> and geo-derived fields degrade to &ldquo;&mdash;&rdquo;; "
    "  hedge-plan 404 &rarr; <code>hedgePlan=null</code>.</li>\n"
    "  <li><strong>instMap build step</strong>: explicit nested loop over <code>regions[]</code> then "
    "  <code>reg.instruments[]</code> propagating <code>reg.region</code> from the parent GeoRegion object "
    "  into each instrument entry. Required because <code>region</code> lives on the parent, not the "
    "  instrument.</li>\n"
    "  <li><strong>5-card KPI strip</strong>: Portfolio Value, Holdings count, Wtd 1Y Return "
    "  (weighted avg &mdash; indicative), Avg Risk (weighted avg &mdash; indicative), "
    "  Hedge Coverage (from saved plan &mdash; indicative).</li>\n"
    "  <li><strong>Region-allocation doughnut chart</strong>: Chart.js canvas "
    "  (<code>fno-mp-alloc-chart</code>) grouped by India / US / EU / Other; "
    "  falls back to &ldquo;Other: 100%&rdquo; when geo is unavailable.</li>\n"
    "  <li><strong>Hedge Status card</strong>: Displays plan coverage %, scenario, updated date, "
    "  and unconditional &ldquo;Values are indicative &mdash; not financial advice&rdquo; note. "
    "  Shows &ldquo;No hedge configured&rdquo; when hedgePlan is null.</li>\n"
    "  <li><strong>6-column holdings table</strong>: Instrument &middot; Alloc% &middot; Position &euro; "
    "  &middot; 1Y Return (ind.) &middot; Risk (ind.) &middot; Hedged? "
    "  (reads hedged_ids from saved plan; stale IDs silently skipped).</li>\n"
    "  <li><strong>CTA button</strong>: <code>window.fnoMpGoHedge</code> (registered in main.js) "
    "  navigates to the Portfolio Hedge section via <code>_sectionLoaders</code>.</li>\n"
    "</ul>\n"
    "<p><strong>fno.html</strong>: Old 2-column My Portfolio table block replaced with the new "
    "5-component structure (KPI strip, chart+hedge-card row, holdings table, CTA). "
    "13 DOM element IDs added: <code>fno-mp-name</code>, <code>fno-mp-updated</code>, "
    "<code>fno-mp-empty</code>, <code>fno-mp-error</code>, <code>fno-mp-kpi-value</code>, "
    "<code>fno-mp-kpi-holdings</code>, <code>fno-mp-kpi-return</code>, <code>fno-mp-kpi-risk</code>, "
    "<code>fno-mp-kpi-hedged</code>, <code>fno-mp-alloc-chart</code>, <code>fno-mp-hedge-card</code>, "
    "<code>fno-mp-holdings-body</code>, <code>fno-mp-total</code>.</p>\n"
    "<p><strong>main.js</strong>: <code>window.fnoMpGoHedge</code> binding added.</p>\n"

    "<h3>Edge Cases Handled (7)</h3>\n"
    "<ol>\n"
    "  <li>Hedge-plan 404 &rarr; hedge card shows &ldquo;No hedge configured&rdquo;; Hedged? column shows &ldquo;&mdash;&rdquo; for all rows.</li>\n"
    "  <li><code>total_value_eur</code> null/0 &rarr; KPI shows &ldquo;&mdash;&rdquo; with subtitle &ldquo;Not set &mdash; add in Portfolio Builder&rdquo;; chart and table still render.</li>\n"
    "  <li>Stale <code>hedged_ids</code> (IDs not in current portfolio) &rarr; silently skipped; table iterates holdings, not hedged_ids.</li>\n"
    "  <li>Portfolio 404 &rarr; <code>fno-mp-empty</code> shown; all other components hidden.</li>\n"
    "  <li>Geo API fail or empty &rarr; <code>instMap={}</code>; all geo-derived fields degrade to &ldquo;&mdash;&rdquo;; chart shows &ldquo;Other: 100%&rdquo; single slice.</li>\n"
    "  <li>instMap instruments not in portfolio &rarr; no error (table loop iterates holdings only).</li>\n"
    "  <li>All <code>allocation_pct = 0</code> &rarr; division-by-zero guard (<code>|| 1</code>) prevents NaN.</li>\n"
    "</ol>\n"

    "<h3>Spec Updates</h3>\n"
    "<ul>\n"
    "  <li><code>Spec_JS_Code.md</code>: FnO <code>my-portfolio.js</code> row updated with Phase 3 description, "
    "  all 13 DOM IDs, and <code>window.fnoMpGoHedge</code> binding.</li>\n"
    "  <li><code>Spec_HTML_Code.md</code>: My Portfolio block updated with Phase 3 component list, "
    "  all 13 DOM IDs, indicative label placements, and CTA button reference.</li>\n"
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
        print("NOTE: Feature 29 Phase 3 section already present — skipping.")
        sys.exit(0)

    new_body = body + FEATURE29_PHASE3_SECTION
    result   = _update_page(auth, page, new_body)
    new_ver  = result["version"]["number"]
    url      = result["_links"]["base"] + result["_links"]["webui"]
    print(f"OK: Page updated to v{new_ver}")
    print(f"  URL: {url}")
    print(f"\nDone. Engineering page: {url}")
