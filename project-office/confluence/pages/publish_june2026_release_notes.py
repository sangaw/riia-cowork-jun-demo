import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from confluence.publish import ConfluenceClient, SECTION

TITLE = "RITA June 2026 — Release Notes"
PAGE_ID = "92274695"

BODY = """
<h1>RITA June 2026 Release Notes</h1>
<p><strong>Release window:</strong> 2026-06-01 &ndash; 2026-06-10 &nbsp;|&nbsp;
<strong>Production:</strong> <a href="https://riia.ravionics.nl">riia.ravionics.nl</a></p>
<p>
  The June release turns the FnO dashboard into a <strong>portfolio-aligned equity hedging
  workspace</strong>: every analysis page (Overview, Positions, Manoeuvre, Stress, Scenarios)
  is now driven by the user's saved portfolio through a single analytics endpoint, and hedge
  selections persist server-side. The release also ships dedicated <strong>mobile PWAs</strong>
  for the Ops, DS Lab, and FnO apps, a <strong>CRISP-DM education page</strong> in the DS Lab,
  a risk-first <strong>Ops Risk page</strong>, and a realistic earnings-shock preset for the
  Invest Game.
</p>

<h2>Release Summary</h2>
<table>
  <thead><tr><th>Feature</th><th>Area</th><th>Status</th></tr></thead>
  <tbody>
    <tr><td>F28 &mdash; Portfolio Build &amp; Hedge Flow</td><td>RITA + FnO</td><td><strong style="color:#1a6b3c">&#10003; Complete</strong></td></tr>
    <tr><td>F29 &mdash; FnO Linked Data &amp; Overview Redesign</td><td>FnO</td><td><strong style="color:#1a6b3c">&#10003; Complete</strong></td></tr>
    <tr><td>F30 &mdash; FnO Portfolio-Aligned Analytics</td><td>FnO</td><td><strong style="color:#1a6b3c">&#10003; Complete</strong></td></tr>
    <tr><td>Equity Scenarios &mdash; native FnO section</td><td>FnO</td><td><strong style="color:#1a6b3c">&#10003; Complete</strong></td></tr>
    <tr><td>Ops Risk page (Daily Ops &rarr; Risk)</td><td>Ops</td><td><strong style="color:#1a6b3c">&#10003; Complete</strong></td></tr>
    <tr><td>DS Lab CRISP-DM Concepts page</td><td>DS Lab</td><td><strong style="color:#1a6b3c">&#10003; Complete</strong></td></tr>
    <tr><td>Mobile PWAs &mdash; Ops / DS Lab / FnO</td><td>Mobile</td><td><strong style="color:#1a6b3c">&#10003; Complete</strong></td></tr>
    <tr><td>Invest Game &mdash; ASML earnings-shock preset</td><td>Invest Game</td><td><strong style="color:#1a6b3c">&#10003; Complete</strong></td></tr>
  </tbody>
</table>

<h2>F28 &mdash; Portfolio Build &amp; Hedge Flow</h2>
<ul>
  <li><strong>Portfolio value in EUR:</strong> Portfolio Builder (RITA) gains a "Portfolio value (&euro;)" input; new <code>total_value_eur</code> column on <code>user_portfolio</code> flows through schemas, service, and API.</li>
  <li><strong>Hedge wizard simplified to 2 tabs:</strong> Discover (holdings table with 1Y return, risk, 1&sigma; downside, "could drop &euro;", put cost, "reduce loss by", hedge checkbox) &rarr; Hedge (coverage dial + payoff simulator). Duration locked to 1 year.</li>
  <li><strong>ATM put calculation:</strong> EUR put cost switched to at-the-money strike so "max loss hedged = premium paid" holds; 2&sigma; VaR in EUR added.</li>
  <li><strong>Fixes:</strong> NVIDIA hedge-type misclassification (ticker-length heuristic replaced with explicit US/intl ticker set); local-dev Google auth redirect loop.</li>
</ul>

<h2>F29 &mdash; FnO Linked Data &amp; Overview Redesign</h2>
<ul>
  <li><strong>Hedge plans persist server-side:</strong> new <code>user_hedge_plans</code> table (Alembic migration) with <code>GET</code>/<code>PUT /api/v1/experience/fno/hedge-plan</code>. Coverage, hedged instruments, and scenario tab are saved with a 500 ms debounce and restored on reload.</li>
  <li><strong>FnO Overview redesign:</strong> 5-card KPI strip (Portfolio Value, Holdings, Wtd 1Y Return, Avg Risk, Hedge Coverage), region allocation doughnut, hedge status card, and a 6-column holdings table with per-instrument Hedged? status. All computed figures labelled "(indicative)".</li>
  <li>Overview, Portfolio Hedge, and the saved portfolio are now linked &mdash; the hedge card and Hedged? column read the saved plan.</li>
</ul>

<h2>F30 &mdash; FnO Portfolio-Aligned Analytics</h2>
<ul>
  <li><strong>One endpoint drives the whole app:</strong> <code>GET /api/v1/experience/fno/portfolio-analytics?mode=real|mock</code> returns positions, net Greeks, &sigma;-move scenario levels, a 20-point payoff grid, 5 crisis stress events (hedged vs unhedged), and a 0&ndash;100 hedge quality score per instrument.</li>
  <li><strong>Single-fetch app init:</strong> <code>initApp()</code> refactored to one API call &mdash; no more position-count flicker or empty analysis pages.</li>
  <li><strong>Real/Mock toggle:</strong> sidebar pill switches between the user's saved portfolio and demo data; first-time users without a portfolio fall back to demo mode with a "Build yours" banner.</li>
  <li>Manoeuvre tab now shows portfolio alerts + suggested actions; Stress and Scenarios pages read hedged-vs-unhedged figures from the same payload.</li>
</ul>

<h2>Equity Scenarios &mdash; Native FnO Section</h2>
<ul>
  <li>The standalone Equity SL/Target scenario tracker is now a native FnO section (<code>#page-equity-scenarios</code>) with colour tokens aliased to the FnO palette.</li>
  <li>Redesigned from a card grid to an <strong>expandable table</strong>: one line per instrument with a 9-dot SL&rarr;Target position indicator; clicking a row reveals P&amp;L detail, trade chips, and a recommendation.</li>
  <li>Data files (<code>alerts/portfolio/tradebook.json</code>) are committed under <code>dashboard/data/scenarios/</code>.</li>
</ul>

<h2>Ops Risk Page</h2>
<ul>
  <li>"Daily Ops" renamed to <strong>Risk</strong> with a risk-first layout: portfolio risk KPI strip (net delta, theta, vega, unrealised P&amp;L), live positions, stress scenarios, and hedge quality chips rendered above the Manoeuvre section.</li>
</ul>

<h2>DS Lab &mdash; CRISP-DM Concepts Page</h2>
<ul>
  <li>New Concepts page walks the 6 CRISP-DM phases with 3 charts each (18 Chart.js charts), key-fact pills, and phase descriptions &mdash; from business understanding through deployment trends (backtest return % + Sharpe across training rounds).</li>
  <li>New system endpoint <code>GET /api/v1/training-metrics?instrument=</code> serves persisted per-episode TD loss + reward, fixing the empty TD Loss chart.</li>
</ul>

<h2>Mobile PWAs</h2>
<ul>
  <li>Three new single-file mobile apps under <code>/mobileapp/</code>, all using the same 5-screen carousel + tab-bar pattern:
    <ul>
      <li><strong>Ops</strong> (<code>ops.html</code>): Overview, Monitoring, Deploy, Agents, Activity.</li>
      <li><strong>DS Lab</strong> (<code>ds.html</code>): Overview, Perf, Trades, Model, Risk.</li>
      <li><strong>FnO</strong> (<code>fno.html</code>): Overview, Positions, Risk, Scenarios, Hedge &mdash; driven by the F30 portfolio-analytics endpoint with Real/Mock toggle.</li>
    </ul>
  </li>
  <li>The mobile gateway hub (<code>/mobile</code>) now links all five apps to mobile-ready experiences &mdash; no more "Desktop Only" cards.</li>
</ul>

<h2>Invest Game</h2>
<ul>
  <li><strong>Volatile preset is now a real event:</strong> the July 2025 ASML earnings shock (&minus;11.37% on game day 2); the AI flags compliance on the shock day.</li>
  <li>Price row shows a <strong>&#9650;/&#9660; % move indicator</strong> vs the previous close on every game day, in both regular and volatile modes.</li>
</ul>

<h2>New API Endpoints</h2>
<table>
  <thead><tr><th>Endpoint</th><th>Method</th><th>Auth</th><th>Feature</th></tr></thead>
  <tbody>
    <tr><td>/api/v1/experience/fno/hedge-plan</td><td>GET / PUT</td><td>JWT</td><td>F29 &mdash; saved hedge plan (404 if none; PUT upserts)</td></tr>
    <tr><td>/api/v1/experience/fno/portfolio-analytics</td><td>GET</td><td>JWT (real mode)</td><td>F30 &mdash; full portfolio analytics payload, <code>?mode=real|mock</code></td></tr>
    <tr><td>/api/v1/training-metrics</td><td>GET</td><td>None</td><td>DS Lab &mdash; per-episode TD loss + reward, <code>?instrument=</code></td></tr>
  </tbody>
</table>

<h2>Database Changes</h2>
<table>
  <thead><tr><th>Migration</th><th>Change</th></tr></thead>
  <tbody>
    <tr><td><code>20260602_add_total_value_eur</code></td><td><code>total_value_eur</code> column on <code>user_portfolio</code></td></tr>
    <tr><td><code>20260603_add_user_hedge_plans</code></td><td>New <code>user_hedge_plans</code> table (FK to <code>user_portfolio_keys</code>, unique per key)</td></tr>
  </tbody>
</table>

<h2>Notes &amp; Disclaimers</h2>
<ul>
  <li>All hedge costs, returns, and risk figures shown in the FnO app are <strong>indicative</strong> &mdash; RITA is a research platform, not financial advice.</li>
  <li>Feature-level documentation: spec files in <code>project-office/specs/</code> and per-feature PLAN_STATUS in <code>project-office/features/Jun/</code> were brought to final state on 2026-06-10.</li>
</ul>
"""


if __name__ == "__main__":
    client = ConfluenceClient()

    if PAGE_ID:
        page_id, url = client.update_page(PAGE_ID, TITLE, BODY)
        print(f"Release notes updated: {url}")
    else:
        page_id, url = client.create_page(TITLE, BODY, parent_id=SECTION["release_notes"])
        print(f"Release notes created: {url}")
        print(f"Page ID: {page_id}")
        print(f'\nPaste into PAGE_ID: "{page_id}"')
