"""
Update the Engineering Confluence page (76611602) after Feature 25 —
ASML Equity Hedge Scenarios (task-brief-20260527-1514).

Changes:
  - Append a "Feature 25" section documenting:
    - POST /api/v1/portfolio/equity-hedge-scenarios endpoint
    - equity_hedge.js frontend module
    - 14 unit tests in tests/unit/test_equity_hedge.py (all passing)
    - i18n fix: nav label + hedge return + net return KPIs (fix commit 488a42b)

Run from project root:
    python project-office/confluence/_update_engineering_feature25_equity_hedge.py
"""
import urllib.request, urllib.error, json, base64
from pathlib import Path

PAGE_ID = "76611602"
BASE    = "https://ravionics.atlassian.net/wiki/rest/api"

MARKER = "feature25-asml-equity-hedge-2026-05-27"

FEATURE25_SECTION = (
    f"\n<!-- {MARKER} -->\n"
    "<h2>Feature 25 &mdash; ASML Equity Hedge Scenarios <small>2026-05-27</small></h2>\n"
    "<p>FnO dashboard page for ASML equity portfolio performance and Black-Scholes "
    "option hedge scenarios. Covers covered call (mild bearish) and protective put "
    "(strong bearish) strategies with payoff curves. Engineer commits: "
    "<strong>7f678d7</strong> (Phase 1 backend + Phase 2 frontend) and "
    "<strong>488a42b</strong> (fix: i18n nav label, hedge return KPI, net return KPI). "
    "Merged to master via <strong>773853e</strong>.</p>\n"

    "<h3>New API Endpoint</h3>\n"
    "<table>\n"
    "  <thead><tr><th>Method</th><th>Path</th><th>Tier</th><th>Description</th><th>Auth</th></tr></thead>\n"
    "  <tbody>\n"
    "  <tr>\n"
    "    <td><code>POST</code></td>\n"
    "    <td><code>/api/v1/portfolio/equity-hedge-scenarios</code></td>\n"
    "    <td>Portfolio (Business Process)</td>\n"
    "    <td>Accepts <code>EquityHedgeRequest</code> (instrument, n_shares, start_date, end_date). "
    "Returns portfolio performance (start/end price, return %, 30-day vol, daily series) and two "
    "Black-Scholes hedge scenarios &mdash; mild bearish (covered call) and strong bearish "
    "(protective put) &mdash; each with strike, premium, max/floor value, breakeven, and "
    "description. Also returns 33-point payoff curves for all three strategies. "
    "ValueError &rarr; HTTP 422.</td>\n"
    "    <td>JWT (Bearer)</td>\n"
    "  </tr>\n"
    "  </tbody>\n"
    "</table>\n"

    "<h3>Backend Files</h3>\n"
    "<table>\n"
    "  <thead><tr><th>File</th><th>Change</th></tr></thead>\n"
    "  <tbody>\n"
    "  <tr>\n"
    "    <td><code>src/rita/core/portfolio_engine.py</code></td>\n"
    "    <td>NEW function <code>equity_hedge_scenarios()</code> &mdash; loads OHLCV price data "
    "via <code>_load_with_indicators</code>, computes portfolio return and 30-day realised "
    "volatility (fallback 0.25 if zero/NaN), prices covered call and protective put via "
    "Black-Scholes, returns full payoff curves over a 33-point price range.</td>\n"
    "  </tr>\n"
    "  <tr>\n"
    "    <td><code>src/rita/api/v1/workflow/portfolio.py</code></td>\n"
    "    <td>Added <code>POST /equity-hedge-scenarios</code> route; "
    "<code>EquityHedgeRequest</code> Pydantic schema; ValueError caught and raised as HTTP 422. "
    "Calls <code>equity_hedge_scenarios()</code> from <code>portfolio_engine</code>.</td>\n"
    "  </tr>\n"
    "  </tbody>\n"
    "</table>\n"

    "<h3>Frontend Files</h3>\n"
    "<table>\n"
    "  <thead><tr><th>File</th><th>Description</th></tr></thead>\n"
    "  <tbody>\n"
    "  <tr>\n"
    "    <td><code>dashboard/js/fno/equity_hedge.js</code></td>\n"
    "    <td>NEW module &mdash; <code>loadEquityHedge(forceRefresh)</code> posts to "
    "<code>/api/v1/portfolio/equity-hedge-scenarios</code>; "
    "<code>renderEquityHedge(data)</code> populates 6 KPI tiles (start price, end price, "
    "vol, return %, hedge return, net return), covered call and protective put scenario cards, "
    "and two Chart.js charts (portfolio value over time; payoff curves). "
    "Fix commit 488a42b added hedge return and net return KPI rendering.</td>\n"
    "  </tr>\n"
    "  <tr>\n"
    "    <td><code>dashboard/fno.html</code></td>\n"
    "    <td>Added Equity Hedge Scenarios section: form inputs (instrument, n_shares, "
    "start_date, end_date), 6 KPI tiles, covered call card, protective put card, "
    "portfolio chart, and payoff chart. Nav label fixed (i18n key <code>nav_equity_hedge</code>).</td>\n"
    "  </tr>\n"
    "  <tr>\n"
    "    <td><code>dashboard/js/fno/nav.js</code> / <code>main.js</code> / <code>state.js</code></td>\n"
    "    <td>Wired <code>equity_hedge</code> tab: nav dispatch, state initialisation, "
    "on-load trigger for <code>loadEquityHedge()</code>.</td>\n"
    "  </tr>\n"
    "  <tr>\n"
    "    <td><code>dashboard/js/i18n/en.js</code>, <code>nl.js</code>, <code>fr.js</code></td>\n"
    "    <td>Added 3 FnO equity-hedge i18n keys: "
    "<code>nav_equity_hedge</code>, <code>kpi_hedge_return</code>, <code>kpi_net_return</code> "
    "(English, Dutch, French).</td>\n"
    "  </tr>\n"
    "  </tbody>\n"
    "</table>\n"

    "<h3>QA Coverage</h3>\n"
    "<p>14 unit tests in <code>tests/unit/test_equity_hedge.py</code> &mdash; all 14 passed. "
    "Three scenario groups: 8 happy-path tests, 3 insufficient-data edge-case tests "
    "(2-row and 4-row raise ValueError; 5-row boundary succeeds), "
    "3 zero-variance edge-case tests (constant price triggers sigma fallback 0.25; "
    "vol_30d_pct == 25.0 asserted; 33-element payoff curves intact).</p>\n"

    "<h3>Spec Updates</h3>\n"
    "<ul>\n"
    "  <li><code>Spec_RITA_App.md</code> line 182 &mdash; "
    "<code>POST /api/v1/portfolio/equity-hedge-scenarios</code> row confirmed present.</li>\n"
    "  <li><code>Spec_JS_Code.md</code> line 71 &mdash; "
    "<code>equity_hedge.js</code> module row confirmed present.</li>\n"
    "</ul>\n"
)


def get_page(path, headers):
    req = urllib.request.Request(f"{BASE}/{path}", headers=headers)
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def put_page(path, payload, headers):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(f"{BASE}/{path}", data=data, headers=headers, method="PUT")
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read()), r.status
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        return (json.loads(raw) if raw.strip() else {}), e.code


def main():
    print(f"Fetching Engineering page {PAGE_ID}...")
    page    = get_page(f"content/{PAGE_ID}?expand=version,body.storage", HEADERS)
    title   = page["title"]
    version = page["version"]["number"]
    body    = page["body"]["storage"]["value"]
    print(f"  Title: {title}  (version {version}, {len(body)} chars)")

    if MARKER in body:
        print(f"NOTE: Feature 25 section already present (marker: {MARKER}) — skipping")
        url = f"https://ravionics.atlassian.net/wiki/spaces/RIIAProjec/pages/{PAGE_ID}"
        print(f"  URL: {url}")
        return url

    body_updated = body + FEATURE25_SECTION

    # Bump version date in page header if present
    for old_date in ("2026-05-26", "2026-05-25", "2026-05-24", "2026-05-23",
                     "2026-05-22", "2026-05-21", "2026-05-20", "2026-05-19"):
        if f"<strong>Date:</strong> {old_date}" in body_updated:
            body_updated = body_updated.replace(
                f"<strong>Date:</strong> {old_date}",
                "<strong>Date:</strong> 2026-05-27",
                1,
            )
            print(f"OK: version date bumped from {old_date} to 2026-05-27")
            break
    else:
        if "<strong>Date:</strong> 2026-05-27" in body_updated:
            print("NOTE: date already at 2026-05-27")

    payload = {
        "version": {"number": version + 1},
        "title":   title,
        "type":    "page",
        "body":    {"storage": {"value": body_updated, "representation": "storage"}},
    }

    result, status = put_page(f"content/{PAGE_ID}", payload, HEADERS)
    if status == 200:
        url = f"https://ravionics.atlassian.net/wiki{result['_links']['webui']}"
        print(f"OK: Page updated to v{version + 1}")
        print(f"  URL: {url}")
        return url
    else:
        raise RuntimeError(f"Update failed: HTTP {status} — {result.get('message', '')[:200]}")


if __name__ == "__main__":
    try:
        key_file = Path("confluence-api-key.txt")
        TOKEN = key_file.read_text().splitlines()[0].strip()
        EMAIL = key_file.read_text().splitlines()[1].strip()
    except FileNotFoundError:
        print("SKIP: confluence-api-key.txt not found — Confluence update skipped.")
        print("Spec edits are complete. Re-run this script after adding the key file.")
        raise SystemExit(0)

    creds   = base64.b64encode(f"{EMAIL}:{TOKEN}".encode()).decode()
    HEADERS = {
        "Authorization": f"Basic {creds}",
        "Content-Type":  "application/json",
        "Accept":        "application/json",
    }

    url = main()
    print(f"\nDone. Engineering page: {url}")
