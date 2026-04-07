import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from confluence.publish import ConfluenceClient, SECTION

TITLE = "Frontend Architecture — Sprint 4 (Day 30)"
PAGE_ID = "68616193"

BODY = """
<h2>1. Overview</h2>
<p>
  Sprint 4 (Days 25–30) refactored the RITA frontend from three monolithic HTML files into
  a production-grade, modular dashboard suite. Each dashboard is a single-page application
  built with vanilla ES modules — no build step required. The three dashboards are served
  directly by FastAPI's <code>StaticFiles</code> mount.
</p>
<table>
  <thead>
    <tr>
      <th>File</th>
      <th>Purpose</th>
      <th>ES Modules</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>dashboard/rita.html</code></td>
      <td>RL training monitor — live training control, P&amp;L charts, observability, explainability</td>
      <td>21</td>
    </tr>
    <tr>
      <td><code>dashboard/fno.html</code></td>
      <td>F&amp;O portfolio manager — positions, Greeks, payoff diagrams, hedging, stress tests</td>
      <td>14</td>
    </tr>
    <tr>
      <td><code>dashboard/ops.html</code></td>
      <td>Operations console — system health, CI/CD pipeline, deployment, monitoring</td>
      <td>12</td>
    </tr>
  </tbody>
</table>
<p>Total: <strong>47 ES modules</strong> across three dashboards.</p>

<h2>2. ES Module Decomposition</h2>

<h3>2.1 rita.html — 21 modules (<code>dashboard/js/rita/</code>)</h3>
<table>
  <thead>
    <tr><th>Module</th><th>Responsibility</th></tr>
  </thead>
  <tbody>
    <tr><td><code>main.js</code></td><td>Entry point — initialises all modules, registers event listeners</td></tr>
    <tr><td><code>api.js</code></td><td>All fetch calls to the RITA backend; reads <code>window.RITA_API_BASE</code></td></tr>
    <tr><td><code>nav.js</code></td><td>Top navigation bar and hamburger toggle (mobile)</td></tr>
    <tr><td><code>utils.js</code></td><td>Shared helpers — date formatting, number rounding, debounce</td></tr>
    <tr><td><code>charts.js</code></td><td>Chart.js wrappers for reward/loss curves and equity curves</td></tr>
    <tr><td><code>chart-modal.js</code></td><td>Full-screen chart modal overlay</td></tr>
    <tr><td><code>training.js</code></td><td>Training run start/stop controls and progress display</td></tr>
    <tr><td><code>pipeline.js</code></td><td>Step-by-step pipeline status panel</td></tr>
    <tr><td><code>performance.js</code></td><td>Sharpe, max-drawdown, win-rate KPI cards</td></tr>
    <tr><td><code>trades.js</code></td><td>Recent trades table with sorting</td></tr>
    <tr><td><code>risk.js</code></td><td>VaR, position-limit alerts, risk gauge</td></tr>
    <tr><td><code>health.js</code></td><td>API liveness/readiness status badge</td></tr>
    <tr><td><code>observability.js</code></td><td>Prometheus metrics summary panel</td></tr>
    <tr><td><code>diagnostics.js</code></td><td>Drift check results (data freshness, Sharpe drift, pipeline health)</td></tr>
    <tr><td><code>market-signals.js</code></td><td>Live Nifty 50 signal cards</td></tr>
    <tr><td><code>scenarios.js</code></td><td>What-if scenario runner UI</td></tr>
    <tr><td><code>explainability.js</code></td><td>SHAP-style feature importance visualisation</td></tr>
    <tr><td><code>export.js</code></td><td>CSV/JSON export of training run results</td></tr>
    <tr><td><code>audit.js</code></td><td>Audit log viewer (last N events)</td></tr>
    <tr><td><code>chat.js</code></td><td>MCP-connected chat panel for natural-language queries</td></tr>
    <tr><td><code>mcp.js</code></td><td>MCP tool-call log viewer</td></tr>
  </tbody>
</table>

<h3>2.2 fno.html — 14 modules (<code>dashboard/js/fno/</code>)</h3>
<table>
  <thead>
    <tr><th>Module</th><th>Responsibility</th></tr>
  </thead>
  <tbody>
    <tr><td><code>main.js</code></td><td>Entry point — initialises all panels</td></tr>
    <tr><td><code>api.js</code></td><td>All fetch calls; reads <code>window.RITA_API_BASE</code></td></tr>
    <tr><td><code>nav.js</code></td><td>Navigation bar and hamburger toggle</td></tr>
    <tr><td><code>utils.js</code></td><td>Shared formatting helpers</td></tr>
    <tr><td><code>state.js</code></td><td>Centralised reactive state store for portfolio data</td></tr>
    <tr><td><code>positions.js</code></td><td>Open positions table (long/short, lot size, P&amp;L)</td></tr>
    <tr><td><code>greeks.js</code></td><td>Delta, Gamma, Theta, Vega display cards</td></tr>
    <tr><td><code>payoff.js</code></td><td>Option payoff diagram (Chart.js)</td></tr>
    <tr><td><code>hedge.js</code></td><td>Delta-hedge recommendation panel</td></tr>
    <tr><td><code>manoeuvre.js</code></td><td>Manoeuvre (roll/close/add leg) action panel</td></tr>
    <tr><td><code>margin.js</code></td><td>Margin utilisation and available capital display</td></tr>
    <tr><td><code>stress.js</code></td><td>Stress-test scenarios (spot ±5%, vol ±20%)</td></tr>
    <tr><td><code>rr.js</code></td><td>Risk/reward ratio and breakeven calculator</td></tr>
    <tr><td><code>dashboard.js</code></td><td>Top-level layout coordinator</td></tr>
  </tbody>
</table>

<h3>2.3 ops.html — 12 modules (<code>dashboard/js/ops/</code>)</h3>
<table>
  <thead>
    <tr><th>Module</th><th>Responsibility</th></tr>
  </thead>
  <tbody>
    <tr><td><code>main.js</code></td><td>Entry point — initialises all panels</td></tr>
    <tr><td><code>api.js</code></td><td>All fetch calls; reads <code>window.RITA_API_BASE</code></td></tr>
    <tr><td><code>nav.js</code></td><td>Navigation bar and hamburger toggle</td></tr>
    <tr><td><code>utils.js</code></td><td>Shared helpers (time formatting, badge colours)</td></tr>
    <tr><td><code>sidebar.js</code></td><td>Left sidebar navigation state</td></tr>
    <tr><td><code>overview.js</code></td><td>System-status summary tile (API up/down, DB health)</td></tr>
    <tr><td><code>monitoring.js</code></td><td>Real-time metrics panel — reads <code>/api/v1/metrics/summary</code></td></tr>
    <tr><td><code>observability.js</code></td><td>Step-log and drift-check panels — reads <code>/api/v1/step-log</code> and <code>/api/v1/drift</code></td></tr>
    <tr><td><code>cicd.js</code></td><td>CI/CD pipeline status (last run, duration, pass/fail)</td></tr>
    <tr><td><code>deploy.js</code></td><td>Deployment control panel (environment selector, rollout button)</td></tr>
    <tr><td><code>daily-ops.js</code></td><td>Daily operations checklist (end-of-day tasks)</td></tr>
    <tr><td><code>chat.js</code></td><td>MCP call log viewer — reads <code>/api/v1/mcp-calls</code></td></tr>
  </tbody>
</table>

<h2>3. Responsive Design</h2>
<p>
  <code>dashboard/css/responsive.css</code> provides a single shared stylesheet imported by
  all three HTML files. It implements a mobile-first responsive layout with three breakpoints.
</p>
<table>
  <thead>
    <tr><th>Breakpoint</th><th>Layout change</th></tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>&le; 1100 px</strong> (tablet landscape)</td>
      <td>Two-column grid collapses to single column; sidebar folds into hamburger drawer</td>
    </tr>
    <tr>
      <td><strong>&le; 768 px</strong> (tablet portrait)</td>
      <td>Navigation items collapse fully; hamburger button becomes visible; table columns reduce</td>
    </tr>
    <tr>
      <td><strong>&le; 480 px</strong> (mobile)</td>
      <td>Full single-column stack; cards go full-width; font sizes reduce for readability</td>
    </tr>
  </tbody>
</table>

<h3>Hamburger Toggle</h3>
<p>
  Each dashboard's <code>nav.js</code> module registers a click handler on a
  <code>.hamburger</code> button element. On click it toggles the <code>.nav-open</code>
  CSS class on the <code>&lt;body&gt;</code>, which triggers the CSS drawer slide-in
  transition defined in <code>responsive.css</code>. The same pattern is used identically
  in all three dashboards for consistency.
</p>

<h2>4. API Base Configuration (<code>window.RITA_API_BASE</code>)</h2>
<p>
  Prior to Day 28, all three <code>api.js</code> modules hardcoded
  <code>http://localhost:8000</code> as the API origin. Day 28 replaced every hardcoded
  URL with the <code>window.RITA_API_BASE</code> pattern.
</p>

<h3>How it works</h3>
<p>Each <code>api.js</code> reads the base URL from a global window variable with a safe fallback:</p>
<pre><code>const BASE = window.RITA_API_BASE ?? "";</code></pre>
<p>
  When <code>RITA_API_BASE</code> is an empty string (the default), all fetch calls use
  relative paths (e.g. <code>/api/v1/positions</code>), which resolve against whatever
  origin served the HTML — correct for same-origin deployments.
</p>

<h3>Deployment configuration</h3>
<p>
  To point the dashboards at a different API host (e.g. staging or production), inject
  <code>window.RITA_API_BASE</code> into each HTML file before the module scripts load:
</p>
<pre><code>&lt;script&gt;
  window.RITA_API_BASE = "https://rita-api.example.com";
&lt;/script&gt;
&lt;script type="module" src="/dashboard/js/rita/main.js"&gt;&lt;/script&gt;</code></pre>
<p>
  This allows a single static build to target any backend — no rebuild or environment-specific
  bundle required. In Kubernetes, the value is injected via a ConfigMap-rendered HTML fragment.
</p>

<h2>5. Observability API Endpoints (ops.html)</h2>
<p>
  Four new endpoints were added to the RITA API (post-Day-29) to make the ops.html
  monitoring panels functional. All return JSON and are authenticated via the standard
  JWT bearer token.
</p>
<table>
  <thead>
    <tr>
      <th>Endpoint</th>
      <th>Consumer module</th>
      <th>Response</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>GET /api/v1/metrics/summary</code></td>
      <td><code>ops/monitoring.js</code></td>
      <td>Structured JSON summary of Prometheus metrics — request counts, p50/p95 latency, error rate</td>
    </tr>
    <tr>
      <td><code>GET /api/v1/step-log</code></td>
      <td><code>ops/observability.js</code></td>
      <td>Training pipeline step log — ordered list of step name, status, duration, and timestamp</td>
    </tr>
    <tr>
      <td><code>GET /api/v1/drift</code></td>
      <td><code>ops/observability.js</code></td>
      <td>System health and drift checks — data freshness, Sharpe drift flag, pipeline health verdict</td>
    </tr>
    <tr>
      <td><code>GET /api/v1/mcp-calls</code></td>
      <td><code>ops/chat.js</code></td>
      <td>MCP tool-call log — list of recent MCP invocations (empty list in this deployment)</td>
    </tr>
  </tbody>
</table>

<h2>6. End-to-End Testing (Playwright)</h2>
<p>
  Day 29 added a full Playwright e2e test suite covering all three dashboards across
  three viewport sizes. The suite is integrated into the CI pipeline and gates the
  Docker build.
</p>

<h3>Test structure</h3>
<table>
  <thead>
    <tr><th>File</th><th>Purpose</th><th>Test count</th></tr>
  </thead>
  <tbody>
    <tr>
      <td><code>tests/e2e/conftest.py</code></td>
      <td>Shared fixtures — starts a real uvicorn server on port 8765 for the test session</td>
      <td>—</td>
    </tr>
    <tr>
      <td><code>tests/e2e/test_smoke.py</code></td>
      <td>7 HTTP-level smoke checks — API liveness, dashboard HTML serving, static asset delivery</td>
      <td>7</td>
    </tr>
    <tr>
      <td><code>tests/e2e/test_responsive.py</code></td>
      <td>
        30 Playwright browser tests: 3 dashboards &times; 3 viewports &times; ~3 assertions each.
        Asserts page load, nav visibility, hamburger toggle at each breakpoint.
      </td>
      <td>30</td>
    </tr>
  </tbody>
</table>
<p><strong>Total: 37 e2e tests</strong> (7 smoke + 30 responsive).</p>

<h3>Viewports tested</h3>
<ul>
  <li><strong>Desktop</strong> — 1280 &times; 800 px</li>
  <li><strong>Tablet</strong> — 768 &times; 1024 px</li>
  <li><strong>Mobile</strong> — 375 &times; 667 px (iPhone SE)</li>
</ul>

<h3>CI integration</h3>
<p>
  The GitHub Actions workflow runs e2e tests in a dedicated <code>e2e</code> job after the
  unit test job passes. The Docker build job is gated on <strong>both</strong> the unit test
  job and the e2e job — a failing responsive or smoke test blocks image publication.
</p>
<pre><code>jobs:
  test:        # unit + integration tests
  e2e:         # Playwright tests (depends on: test)
  docker-build: # (depends on: test, e2e)</code></pre>

<h2>7. File Structure</h2>
<pre><code>riia-jun-release/
└── dashboard/
    ├── rita.html                   # RL training monitor SPA
    ├── fno.html                    # F&amp;O portfolio manager SPA
    ├── ops.html                    # Operations console SPA
    ├── css/
    │   └── responsive.css          # Shared responsive stylesheet (3 breakpoints)
    └── js/
        ├── rita/                   # 21 ES modules
        │   ├── main.js
        │   ├── api.js              # window.RITA_API_BASE pattern
        │   ├── nav.js              # hamburger toggle
        │   ├── charts.js
        │   ├── training.js
        │   ├── pipeline.js
        │   ├── performance.js
        │   ├── trades.js
        │   ├── risk.js
        │   ├── health.js
        │   ├── observability.js
        │   ├── diagnostics.js
        │   ├── market-signals.js
        │   ├── scenarios.js
        │   ├── explainability.js
        │   ├── export.js
        │   ├── audit.js
        │   ├── chat.js
        │   ├── mcp.js
        │   ├── chart-modal.js
        │   └── utils.js
        ├── fno/                    # 14 ES modules
        │   ├── main.js
        │   ├── api.js
        │   ├── nav.js
        │   ├── utils.js
        │   ├── state.js
        │   ├── positions.js
        │   ├── greeks.js
        │   ├── payoff.js
        │   ├── hedge.js
        │   ├── manoeuvre.js
        │   ├── margin.js
        │   ├── stress.js
        │   ├── rr.js
        │   └── dashboard.js
        └── ops/                    # 12 ES modules
            ├── main.js
            ├── api.js
            ├── nav.js
            ├── utils.js
            ├── sidebar.js
            ├── overview.js
            ├── monitoring.js
            ├── observability.js
            ├── cicd.js
            ├── deploy.js
            ├── daily-ops.js
            └── chat.js</code></pre>

<h2>8. Design Decisions</h2>
<ul>
  <li>
    <strong>No build step.</strong> ES modules are served as-is by FastAPI's
    <code>StaticFiles</code>. This eliminates webpack/vite configuration overhead and makes
    the frontend trivially portable — any static file server works.
  </li>
  <li>
    <strong>Single shared CSS file.</strong> <code>responsive.css</code> is imported by all
    three HTML files, keeping breakpoint logic in one place and preventing drift between dashboards.
  </li>
  <li>
    <strong>Relative-path default.</strong> <code>window.RITA_API_BASE ?? ""</code> means the
    dashboards work correctly with zero configuration in same-origin deployments (the common
    case), while still supporting cross-origin deployments without a rebuild.
  </li>
  <li>
    <strong>Real server in e2e tests.</strong> <code>conftest.py</code> starts a real uvicorn
    process (not a mock) so e2e tests exercise the actual FastAPI app, static file serving,
    and CORS configuration, not a test double.
  </li>
</ul>
"""

if __name__ == "__main__":
    client = ConfluenceClient()
    if PAGE_ID:
        pid, url = client.update_page(PAGE_ID, TITLE, BODY)
        print(f"Updated: {url}")
        print(f"Page ID: {pid}")
    else:
        pid, url = client.create_page(TITLE, BODY, parent_id=SECTION["engineering"])
        print(f"Created: {url}")
        print(f'PAGE_ID = "{pid}"')
