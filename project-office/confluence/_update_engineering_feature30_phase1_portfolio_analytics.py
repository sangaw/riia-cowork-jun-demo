"""
Update the Engineering Confluence page (76611602) after Feature 30 Phase 1 —
portfolio-analytics unified FnO backend endpoint (2026-06-04).

Run from project root:
    python project-office/confluence/_update_engineering_feature30_phase1_portfolio_analytics.py
"""
import urllib.request, urllib.error, json, base64
from pathlib import Path

PAGE_ID = "76611602"
BASE    = "https://ravionics.atlassian.net/wiki/rest/api"

MARKER = "feature30-phase1-portfolio-analytics-2026-06-04"

FEATURE30_PHASE1_SECTION = (
    f"\n<!-- {MARKER} -->\n"
    "<h2>Feature 30 Phase 1 &mdash; FnO Portfolio Analytics Backend Endpoint <small>2026-06-04</small></h2>\n"
    "<p>Adds a unified read-only Experience-tier endpoint that delivers a single analytics payload "
    "covering positions, per-instrument greeks, net greeks, &sigma;-based scenario levels, a 21-point "
    "payoff grid, stress test results, and hedge quality scores &mdash; all derived from the user&rsquo;s "
    "saved equity portfolio and hedge plan. Replaces the broken multi-call chain in "
    "<code>app-init.js</code> as the single source of truth for all FnO dashboard sections. "
    "Commits: <strong>10b4f66</strong> (implementation), <strong>abdc7c6</strong> (tests).</p>\n"

    "<h3>New Endpoint</h3>\n"
    "<table>\n"
    "  <thead><tr><th>Method</th><th>Path</th><th>Tier</th><th>Auth</th><th>Purpose</th></tr></thead>\n"
    "  <tbody>\n"
    "    <tr>\n"
    "      <td>GET</td>\n"
    "      <td><code>/api/v1/experience/fno/portfolio-analytics?mode=real|mock</code></td>\n"
    "      <td>Experience</td>\n"
    "      <td>JWT (mode=real only; mode=mock: no auth)</td>\n"
    "      <td>Unified FnO dashboard analytics payload &mdash; positions, greeks, scenarios, "
    "      stress, payoff, HQS, market OHLCV. mode=mock returns demo data with zero DB calls; "
    "      mode=real requires JWT &rarr; 401 without token, 404 if no portfolio saved.</td>\n"
    "    </tr>\n"
    "  </tbody>\n"
    "</table>\n"

    "<h3>Response Payload &mdash; Top-level Fields</h3>\n"
    "<table>\n"
    "  <thead><tr><th>Field</th><th>Type</th><th>Description</th></tr></thead>\n"
    "  <tbody>\n"
    "    <tr><td><code>mode</code></td><td>string</td><td>&ldquo;real&rdquo; or &ldquo;mock&rdquo;</td></tr>\n"
    "    <tr><td><code>portfolio_meta</code></td><td>PortfolioMetaSchema</td><td>name, total_value_eur, updated_at</td></tr>\n"
    "    <tr><td><code>market</code></td><td>dict[str, MarketEntrySchema]</td><td>Per-instrument OHLCV + daily change from market_data_cache</td></tr>\n"
    "    <tr><td><code>positions</code></td><td>list[PositionItemSchema]</td><td>Per-holding: und, exp=EQUITY, type=EQ, side=Long, qty, allocation_pct, position_eur, avg, ltp, chg, pnl, currency, ann_vol_pct, region</td></tr>\n"
    "    <tr><td><code>greeks</code></td><td>list[GreekItemSchema]</td><td>Per-holding BS greeks: delta, gamma, theta, vega, sigma_eur, hedge_type, put_cost_eur, call_income_eur, net_theta_eur_day</td></tr>\n"
    "    <tr><td><code>net_greeks</code></td><td>NetGreeksSchema</td><td>Portfolio aggregate: delta, theta, vega</td></tr>\n"
    "    <tr><td><code>net_delta</code></td><td>dict[str, float]</td><td>Per-instrument net delta</td></tr>\n"
    "    <tr><td><code>scenario_levels</code></td><td>dict[str, ScenarioLevelSchema]</td><td>Per-instrument &sigma;-anchored target and stop-loss levels</td></tr>\n"
    "    <tr><td><code>payoff</code></td><td>PayoffSchema</td><td>21-point payoff grid: portfolio unhedged + hedged (labels + data arrays)</td></tr>\n"
    "    <tr><td><code>stress</code></td><td>list[StressEventSchema] (5 items)</td><td>5 stress events: label, move_pct, portfolio_pnl_eur, hedged_pnl_eur</td></tr>\n"
    "    <tr><td><code>hedge_quality</code></td><td>HedgeQualitySchema</td><td>Per-instrument HQS score, tier, hedged flag, strategy, coverage_pct, note</td></tr>\n"
    "    <tr><td><code>closed_positions</code></td><td>list</td><td>Always empty [] (Phase 1)</td></tr>\n"
    "    <tr><td><code>realized_pnl</code></td><td>float</td><td>Always 0.0 (Phase 1)</td></tr>\n"
    "    <tr><td><code>margin</code></td><td>dict</td><td>Always {} (Phase 1)</td></tr>\n"
    "  </tbody>\n"
    "</table>\n"

    "<h3>New Pydantic Schemas &mdash; <code>schemas/portfolio_analytics.py</code></h3>\n"
    "<ul>\n"
    "  <li><code>PortfolioMetaSchema</code></li>\n"
    "  <li><code>MarketEntrySchema</code></li>\n"
    "  <li><code>PositionItemSchema</code></li>\n"
    "  <li><code>GreekItemSchema</code></li>\n"
    "  <li><code>NetGreeksSchema</code></li>\n"
    "  <li><code>ScenarioLevelSchema</code></li>\n"
    "  <li><code>PayoffCurveSchema</code></li>\n"
    "  <li><code>PayoffSchema</code></li>\n"
    "  <li><code>StressEventSchema</code></li>\n"
    "  <li><code>HedgeQualityPositionSchema</code></li>\n"
    "  <li><code>HedgeQualitySchema</code></li>\n"
    "  <li><code>PortfolioAnalyticsResponse</code> (top-level envelope)</li>\n"
    "</ul>\n"

    "<h3>Files Changed</h3>\n"
    "<table>\n"
    "  <thead><tr><th>File</th><th>Change</th></tr></thead>\n"
    "  <tbody>\n"
    "    <tr><td><code>src/rita/api/experience/portfolio_analytics.py</code></td>"
    "    <td>CREATED: MOCK_PORTFOLIO constant, get_optional_user() usage, router, "
    "    _build_real_payload() with sub-helpers for greeks, scenarios, payoff, stress, HQS</td></tr>\n"
    "    <tr><td><code>src/rita/schemas/portfolio_analytics.py</code></td>"
    "    <td>CREATED: 12 Pydantic models (PortfolioAnalyticsResponse + 11 nested schemas)</td></tr>\n"
    "    <tr><td><code>src/rita/auth.py</code></td>"
    "    <td>MODIFIED: <code>get_optional_user()</code> async dependency added using "
    "    <code>HTTPBearer(auto_error=False)</code> for conditional JWT enforcement</td></tr>\n"
    "    <tr><td><code>src/rita/main.py</code></td>"
    "    <td>MODIFIED: <code>portfolio_analytics_router</code> imported and registered via "
    "    <code>app.include_router()</code> alongside other Experience-tier routers</td></tr>\n"
    "    <tr><td><code>project-office/specs/Spec_RITA_App.md</code></td>"
    "    <td>MODIFIED: FnO Experience endpoint table row added (line 135)</td></tr>\n"
    "    <tr><td><code>project-office/specs/Spec_Python_Code.md</code></td>"
    "    <td>MODIFIED: Tier 3 Experience Layer file inventory row added (line 77)</td></tr>\n"
    "    <tr><td><code>tests/unit/test_portfolio_analytics.py</code></td>"
    "    <td>CREATED: 15 unit tests covering mock path, real-mode auth, repo calls, "
    "    edge cases E1&ndash;E10, all 14 top-level response fields verified</td></tr>\n"
    "  </tbody>\n"
    "</table>\n"

    "<h3>Edge Cases Handled (10)</h3>\n"
    "<ol>\n"
    "  <li><strong>E1</strong>: mode=mock, no JWT &rarr; 200 with MOCK_PORTFOLIO, zero DB calls</li>\n"
    "  <li><strong>E2</strong>: mode=real, no JWT &rarr; 401</li>\n"
    "  <li><strong>E3</strong>: mode=real, valid JWT, no portfolio key &rarr; 404</li>\n"
    "  <li><strong>E4</strong>: mode=real, valid JWT, key exists but no active portfolio &rarr; 404</li>\n"
    "  <li><strong>E5</strong>: mode=real, portfolio exists, no hedge plan &rarr; safe defaults (delta=1.0, theta/vega/gamma=0)</li>\n"
    "  <li><strong>E6</strong>: instrument absent from market_data_cache &rarr; graceful degradation (fallback vol 25%, ltp=0)</li>\n"
    "  <li><strong>E7</strong>: portfolio with empty holdings list &rarr; 200 with empty arrays/dicts</li>\n"
    "  <li><strong>E8</strong>: total_value_eur is None &rarr; default to 0, position_eur=0, sigma_eur=0</li>\n"
    "  <li><strong>E9</strong>: invalid mode value &rarr; 422 (FastAPI Literal validation)</li>\n"
    "  <li><strong>E10</strong>: sigma&asymp;0 or S/K math.log domain error &rarr; try/except guard, returns 0.0</li>\n"
    "</ol>\n"

    "<h3>Test Coverage</h3>\n"
    "<p>15 unit tests in <code>tests/unit/test_portfolio_analytics.py</code>, 15/15 passed. "
    "All 14 top-level PortfolioAnalyticsResponse fields verified present in both mock and real-mode responses. "
    "Ruff check: zero errors.</p>\n"
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
        print("NOTE: Feature 30 Phase 1 section already present — skipping.")
        sys.exit(0)

    new_body = body + FEATURE30_PHASE1_SECTION
    result   = _update_page(auth, page, new_body)
    new_ver  = result["version"]["number"]
    url      = result["_links"]["base"] + result["_links"]["webui"]
    print(f"OK: Page updated to v{new_ver}")
    print(f"  URL: {url}")
    print(f"\nDone. Engineering page: {url}")
