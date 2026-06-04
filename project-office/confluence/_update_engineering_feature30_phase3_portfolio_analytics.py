"""
Update the Engineering Confluence page (76611602) after Feature 30 Phase 3 —
FnO dashboard section renderers wired to portfolio-analytics state: Overview
instrument selector, positions grid, Risk/Scenarios/Hedge Radar/Manoeuvre pages
all consuming state fields (2026-06-04).

Run from project root:
    python project-office/confluence/_update_engineering_feature30_phase3_portfolio_analytics.py
"""
import urllib.request, urllib.error, json, base64
from pathlib import Path

PAGE_ID = "76611602"
BASE    = "https://ravionics.atlassian.net/wiki/rest/api"

MARKER = "feature30-phase3-portfolio-analytics-2026-06-04"

FEATURE30_PHASE3_SECTION = (
    f"\n<!-- {MARKER} -->\n"
    "<h2>Feature 30 Phase 3 &mdash; FnO Dashboard: Section Renderers + Overview Instrument Selector <small>2026-06-04</small></h2>\n"
    "<p>Completes the F30 consumer chain by wiring the Risk, Scenarios, Hedge Radar, and Manoeuvre pages "
    "to the <code>state.portfolioMeta</code>, <code>state.scenarioLevels</code>, <code>state.payoffData</code>, "
    "and <code>state.hedgeQuality</code> fields that were mapped in Phase 2 but never consumed by section renderers. "
    "Also improves the Overview page with an ASML-default instrument selector card, a live positions grid, "
    "and removes redundant widgets (paper toggle, closed positions, equity hedge grid, region/strategy/total allocation). "
    "No new backend endpoint &mdash; reuses <code>GET /api/v1/experience/fno/portfolio-analytics?mode=real|mock</code> "
    "from Phase 1. Commit: <strong>f7c60e8</strong> (implementation). Tests: 25/25 passed.</p>\n"

    "<h3>Overview Page Changes</h3>\n"
    "<p>The FnO Overview page (<code>page-overview</code>) now shows an instrument selector card with ASML as default "
    "(<code>_selectedInstrument = &lsquo;ASML&rsquo;</code> module constant). Selecting an instrument reloads the positions "
    "grid and KPI strip for that instrument via <code>window.fnoSelectInstrument(symbol)</code>. "
    "The new <code>renderOverviewFromState()</code> function in <code>my-portfolio.js</code> renders "
    "a 3-card KPI strip (Portfolio Value, P&amp;L, Positions count) and a live positions grid from "
    "<code>state.positions</code>. Removed: paper-mode-chk toggle block, closed-positions panel, "
    "equity hedge positions grid, region/strategy/total allocation widgets.</p>\n"

    "<h3>Section Renderer Changes</h3>\n"
    "<table>\n"
    "  <thead><tr><th>Page</th><th>Module</th><th>Change</th></tr></thead>\n"
    "  <tbody>\n"
    "    <tr>\n"
    "      <td>Risk &mdash; Payoff</td>\n"
    "      <td><code>payoff.js</code></td>\n"
    "      <td><code>renderPayoffChart()</code> updated to detect portfolio-shape "
    "      (<code>data.portfolio</code> / <code>data.hedged</code>) vs legacy NIFTY/BANKNIFTY shape</td>\n"
    "    </tr>\n"
    "    <tr>\n"
    "      <td>Risk &mdash; Stress</td>\n"
    "      <td><code>stress.js</code></td>\n"
    "      <td>Added <code>renderAnalyticsStress()</code> for historical stress events from "
    "      <code>state.stressData</code>; called from <code>renderStressScenarios()</code></td>\n"
    "    </tr>\n"
    "    <tr>\n"
    "      <td>Risk &mdash; Greeks</td>\n"
    "      <td><code>greeks.js</code></td>\n"
    "      <td><code>renderGreeksTable()</code> fixed to use <code>g.und + g.hedge_type</code> "
    "      (not <code>g.full</code>) and <code>g.ann_vol_pct</code> (not <code>g.iv</code>)</td>\n"
    "    </tr>\n"
    "    <tr>\n"
    "      <td>Scenarios</td>\n"
    "      <td><code>rr.js</code> + <code>app-init.js</code></td>\n"
    "      <td><code>_normScenarioLevels()</code> helper added in <code>app-init.js</code> — normalises "
    "      scenario shape mismatch (raw <code>{target, sl}</code> &rarr; <code>{bull: {target}, bear: {target}}</code>) "
    "      before passing to <code>rr.js</code>; called immediately after <code>state.scenarioLevels</code> assignment</td>\n"
    "    </tr>\n"
    "    <tr>\n"
    "      <td>Hedge Radar</td>\n"
    "      <td><code>hedge.js</code></td>\n"
    "      <td>Added <code>renderPortfolioHedgeRadar()</code> — renders instrument-level HQS table "
    "      from <code>state.hedgeQuality.positions</code>; replaces <code>renderHedgeRadar()</code> "
    "      in <code>app-init.js _renderAll()</code></td>\n"
    "    </tr>\n"
    "    <tr>\n"
    "      <td>Manoeuvre</td>\n"
    "      <td><code>manoeuvre.js</code></td>\n"
    "      <td>Fixed instrument field lookup at line 140: <code>p.instrument</code> &rarr; "
    "      <code>p.full ?? p.instrument ?? p.und</code> (handles PositionItemSchema field names)</td>\n"
    "    </tr>\n"
    "  </tbody>\n"
    "</table>\n"

    "<h3>app-init.js _renderAll() Registration</h3>\n"
    "<p><code>_renderAll()</code> in <code>app-init.js</code> now calls both "
    "<code>renderOverviewFromState()</code> (imported from <code>my-portfolio.js</code>) and "
    "<code>renderPortfolioHedgeRadar()</code> (imported from <code>hedge.js</code>). "
    "<code>_normScenarioLevels()</code> is called inline after state assignment, before "
    "any scenario renderer fires.</p>\n"

    "<h3>Files Changed</h3>\n"
    "<table>\n"
    "  <thead><tr><th>File</th><th>Change</th></tr></thead>\n"
    "  <tbody>\n"
    "    <tr><td><code>dashboard/js/fno/my-portfolio.js</code></td>"
    "    <td>Added <code>renderOverviewFromState()</code>, <code>fnoSelectInstrument()</code>, "
    "    <code>_selectedInstrument = &lsquo;ASML&rsquo;</code> constant; removed paper toggle, "
    "    closed positions panel, equity hedge grid, region/strategy/total allocation widgets; "
    "    exported <code>renderOverviewFromState</code></td></tr>\n"
    "    <tr><td><code>dashboard/js/fno/app-init.js</code></td>"
    "    <td>Added <code>_normScenarioLevels()</code> helper and normalisation call; "
    "    updated <code>_renderAll()</code> to call <code>renderOverviewFromState</code> "
    "    and <code>renderPortfolioHedgeRadar</code>; updated imports</td></tr>\n"
    "    <tr><td><code>dashboard/js/fno/payoff.js</code></td>"
    "    <td>Updated <code>renderPayoffChart()</code> to handle portfolio-shape vs legacy "
    "    NIFTY/BANKNIFTY shape</td></tr>\n"
    "    <tr><td><code>dashboard/js/fno/stress.js</code></td>"
    "    <td>Added <code>renderAnalyticsStress()</code> for <code>state.stressData</code> "
    "    historical stress events</td></tr>\n"
    "    <tr><td><code>dashboard/js/fno/hedge.js</code></td>"
    "    <td>Added <code>renderPortfolioHedgeRadar()</code> for "
    "    <code>state.hedgeQuality.positions</code>; exported it</td></tr>\n"
    "    <tr><td><code>dashboard/js/fno/manoeuvre.js</code></td>"
    "    <td>Fixed line 140: <code>p.instrument</code> &rarr; "
    "    <code>p.full ?? p.instrument ?? p.und</code></td></tr>\n"
    "    <tr><td><code>dashboard/js/fno/greeks.js</code></td>"
    "    <td>Fixed <code>renderGreeksTable()</code>: <code>g.full</code> &rarr; "
    "    <code>g.und + g.hedge_type</code>; <code>g.iv</code> &rarr; <code>g.ann_vol_pct</code></td></tr>\n"
    "    <tr><td><code>dashboard/js/fno/main.js</code></td>"
    "    <td>Added <code>window.fnoSelectInstrument = fnoSelectInstrument</code> binding; "
    "    imported <code>renderOverviewFromState</code></td></tr>\n"
    "    <tr><td><code>dashboard/fno.html</code></td>"
    "    <td>Removed paper-mode-chk toggle block; added <code>fno-overview-inst-selector</code> "
    "    and <code>fno-overview-positions-grid</code> divs; added <code>stress-events-row</code> "
    "    below <code>stress-row</code>; added HQS portfolio section in <code>page-hedge</code>; "
    "    removed closed-positions, equity hedge grid, allocation widgets</td></tr>\n"
    "    <tr><td><code>project-office/specs/Spec_RITA_App.md</code></td>"
    "    <td>Updated portfolio-analytics endpoint row: F30 Phase 3 consumer chain detail; "
    "    scenario normalisation note</td></tr>\n"
    "    <tr><td><code>project-office/specs/Spec_JS_Code.md</code></td>"
    "    <td>Updated FnO module table: <code>my-portfolio.js</code> exports "
    "    <code>renderOverviewFromState</code>; <code>hedge.js</code> exports "
    "    <code>renderPortfolioHedgeRadar</code>; <code>app-init.js</code> documents "
    "    <code>_normScenarioLevels</code></td></tr>\n"
    "  </tbody>\n"
    "</table>\n"

    "<h3>Test Coverage</h3>\n"
    "<p>25 unit tests in <code>tests/unit/test_f30_phase3_contract.py</code>, 25/25 passed. "
    "Schema-contract tests only (no new Python code in Phase 3). All Phase 3 JS consumer "
    "state fields verified against <code>PortfolioAnalyticsResponse</code>: "
    "<code>portfolio_meta</code>, <code>positions</code>, <code>market</code>, "
    "<code>scenario_levels</code>, <code>payoff</code>, <code>stress</code>, "
    "<code>hedge_quality</code>, <code>net_greeks</code>, <code>greeks</code> "
    "(<code>und + hedge_type + ann_vol_pct</code>; absence of <code>full</code> verified). "
    "_normScenarioLevels edge cases: empty input, bull/bear passthrough, multi-instrument. "
    "All 21 schema fields matched with no mismatches.</p>\n"
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
        print("NOTE: Feature 30 Phase 3 section already present — skipping.")
        sys.exit(0)

    new_body = body + FEATURE30_PHASE3_SECTION
    result   = _update_page(auth, page, new_body)
    new_ver  = result["version"]["number"]
    url      = result["_links"]["base"] + result["_links"]["webui"]
    print(f"OK: Page updated to v{new_ver}")
    print(f"  URL: {url}")
    print(f"\nDone. Engineering page: {url}")
