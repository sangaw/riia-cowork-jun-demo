"""
Update the Engineering Confluence page (76611602) after Feature 30 Phase 2 —
portfolio-analytics frontend wiring: single unified initApp() call + Real/Mock toggle (2026-06-04).

Run from project root:
    python project-office/confluence/_update_engineering_feature30_phase2_portfolio_analytics.py
"""
import urllib.request, urllib.error, json, base64
from pathlib import Path

PAGE_ID = "76611602"
BASE    = "https://ravionics.atlassian.net/wiki/rest/api"

MARKER = "feature30-phase2-portfolio-analytics-2026-06-04"

FEATURE30_PHASE2_SECTION = (
    f"\n<!-- {MARKER} -->\n"
    "<h2>Feature 30 Phase 2 &mdash; FnO Dashboard: Unified initApp() + Real/Mock Toggle <small>2026-06-04</small></h2>\n"
    "<p>Wires the Phase 1 backend endpoint (<code>/api/v1/experience/fno/portfolio-analytics</code>) "
    "to the FnO dashboard frontend. Replaces the fragmented multi-fetch <code>initApp()</code> chain "
    "with a single unified call to the portfolio-analytics endpoint, maps all 13 response fields to "
    "state, and adds a Real/Mock sidebar toggle. "
    "Commits: <strong>3c19040</strong> (implementation), <strong>cb5eeba</strong> (tests).</p>\n"

    "<h3>Key Change: initApp() Refactor</h3>\n"
    "<p>The <code>initApp()</code> function in <code>dashboard/js/fno/app-init.js</code> now uses a "
    "<strong>single unified call</strong> to <code>/api/v1/experience/fno/portfolio-analytics?mode=real|mock</code> "
    "instead of the previous fragmented multi-fetch chain. All 13 response fields from "
    "<code>PortfolioAnalyticsResponse</code> are mapped directly to dashboard state. "
    "A <strong>Real/Mock toggle</strong> has been added to the FnO sidebar, allowing users to switch "
    "between live portfolio data (requires JWT) and demo mock data (no auth required).</p>\n"

    "<h3>API Contract &mdash; Frontend Consumer</h3>\n"
    "<table>\n"
    "  <thead><tr><th>Endpoint</th><th>JS File</th><th>Signature</th><th>Auth</th></tr></thead>\n"
    "  <tbody>\n"
    "    <tr>\n"
    "      <td><code>GET /api/v1/experience/fno/portfolio-analytics?mode=real|mock</code></td>\n"
    "      <td><code>dashboard/js/fno/app-init.js</code></td>\n"
    "      <td><code>initApp(mode='mock')</code></td>\n"
    "      <td>JWT bearer token in sessionStorage (<code>auth_token</code>) — sent only when mode=real; "
    "      mode=mock requires no auth</td>\n"
    "    </tr>\n"
    "  </tbody>\n"
    "</table>\n"

    "<h3>State Fields Mapped (13)</h3>\n"
    "<table>\n"
    "  <thead><tr><th>Response Field</th><th>JS Read (<code>data.*</code>)</th><th>State Field</th></tr></thead>\n"
    "  <tbody>\n"
    "    <tr><td><code>portfolio_meta</code></td><td><code>data.portfolio_meta</code></td><td><code>state.portfolioMeta</code></td></tr>\n"
    "    <tr><td><code>market</code></td><td><code>data.market</code></td><td><code>state.marketData</code></td></tr>\n"
    "    <tr><td><code>positions</code></td><td><code>data.positions</code></td><td><code>state.positions</code></td></tr>\n"
    "    <tr><td><code>greeks</code></td><td><code>data.greeks</code></td><td><code>state.greeksData</code></td></tr>\n"
    "    <tr><td><code>net_greeks</code></td><td><code>data.net_greeks</code></td><td><code>state.netGreeks</code></td></tr>\n"
    "    <tr><td><code>net_delta</code></td><td><code>data.net_delta</code></td><td><code>state.portDelta</code></td></tr>\n"
    "    <tr><td><code>scenario_levels</code></td><td><code>data.scenario_levels</code></td><td><code>state.scenarioLevels</code></td></tr>\n"
    "    <tr><td><code>payoff</code></td><td><code>data.payoff</code></td><td><code>state.payoffData</code></td></tr>\n"
    "    <tr><td><code>stress</code></td><td><code>data.stress</code></td><td><code>state.stressData</code></td></tr>\n"
    "    <tr><td><code>hedge_quality</code></td><td><code>data.hedge_quality</code></td><td><code>state.hedgeQuality</code></td></tr>\n"
    "    <tr><td><code>closed_positions</code></td><td><code>data.closed_positions</code></td><td><code>state.closedPositions</code></td></tr>\n"
    "    <tr><td><code>realized_pnl</code></td><td><code>data.realized_pnl</code></td><td><code>state.realizedPnl</code></td></tr>\n"
    "    <tr><td><code>margin</code></td><td><code>data.margin</code></td><td><code>state.marginData</code></td></tr>\n"
    "  </tbody>\n"
    "</table>\n"

    "<h3>Files Changed</h3>\n"
    "<table>\n"
    "  <thead><tr><th>File</th><th>Change</th></tr></thead>\n"
    "  <tbody>\n"
    "    <tr><td><code>dashboard/js/fno/state.js</code></td>"
    "    <td>Added <code>portfolioMeta: null</code> and <code>analyticsMode: &lsquo;mock&rsquo;</code> fields</td></tr>\n"
    "    <tr><td><code>dashboard/js/fno/app-init.js</code></td>"
    "    <td>Full refactor: single fetch to portfolio-analytics, <code>initApp(mode=&lsquo;mock&rsquo;)</code> "
    "    signature, removed loadEquityHedge/injectAsmlToState/multi-fetch chain, added _renderAll() helper, "
    "    fetchPositions shim, disable/re-enable chk toggle; 401&rarr;login error, 404&rarr;no portfolio</td></tr>\n"
    "    <tr><td><code>dashboard/js/fno/main.js</code></td>"
    "    <td>Added <code>window.toggleAnalyticsMode</code> binding wired to <code>initApp(state.analyticsMode)</code></td></tr>\n"
    "    <tr><td><code>dashboard/fno.html</code></td>"
    "    <td>Added Real/Mock toggle div after <code>#sidebar-as-of</code>: checkbox (<code>#analytics-mode-chk</code>), "
    "    label (<code>#analytics-mode-label</code>), error div (<code>#analytics-mode-error</code>)</td></tr>\n"
    "    <tr><td><code>project-office/specs/Spec_JS_Code.md</code></td>"
    "    <td>Updated app-init.js row with new <code>initApp(mode=&lsquo;mock&rsquo;)</code> signature and fetchPositions shim description</td></tr>\n"
    "    <tr><td><code>project-office/specs/Spec_RITA_App.md</code></td>"
    "    <td>Annotated portfolio-analytics row with Phase 2 JS consumer note and sidebar toggle wiring</td></tr>\n"
    "  </tbody>\n"
    "</table>\n"

    "<h3>Test Coverage</h3>\n"
    "<p>33 unit tests in <code>tests/unit/test_portfolio_analytics_p2.py</code>, 33/33 passed. "
    "Full API-frontend contract verified: all 13 Pydantic fields confirmed present and mapped. "
    "Toggle auth edge cases (401/404 fallback, mock no-auth, real+JWT=200), state.js contract, "
    "app-init.js signature and auth key (FC-AUTH-KEY), and main.js window binding all covered.</p>\n"
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
        print("NOTE: Feature 30 Phase 2 section already present — skipping.")
        sys.exit(0)

    new_body = body + FEATURE30_PHASE2_SECTION
    result   = _update_page(auth, page, new_body)
    new_ver  = result["version"]["number"]
    url      = result["_links"]["base"] + result["_links"]["webui"]
    print(f"OK: Page updated to v{new_ver}")
    print(f"  URL: {url}")
    print(f"\nDone. Engineering page: {url}")
