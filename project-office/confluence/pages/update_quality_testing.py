"""
Update the Quality and Testing Confluence page (65404959) with
current test strategy, tier descriptions, and coverage details.

Run from any directory:
  CONFLUENCE_EMAIL=contact@ravionics.nl python project-office/confluence/pages/update_quality_testing.py
"""

import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from confluence.publish import ConfluenceClient, SECTION

PAGE_ID = SECTION["quality_testing"]  # 65404959

QUALITY_HTML = """
<h1>Quality and Testing</h1>
<p><strong>Version:</strong> v1.0 &nbsp;|&nbsp; <strong>Date:</strong> 2026-04-29</p>
<p>Test strategy, tier descriptions, and coverage for the RITA application.
Tests live in <code>riia-jun-release/tests/</code> and are split into three tiers:
unit, integration, and end-to-end (e2e).</p>

<hr/>

<h2>Test Pyramid Overview</h2>
<table>
  <thead>
    <tr><th>Tier</th><th>Location</th><th>Runner</th><th>Isolation</th><th>When to run</th></tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>Unit</strong></td>
      <td><code>tests/unit/</code></td>
      <td><code>pytest tests/unit</code></td>
      <td>In-memory SQLite or FastAPI dependency overrides — no server, no CSV files</td>
      <td>Every commit; fastest feedback</td>
    </tr>
    <tr>
      <td><strong>Integration</strong></td>
      <td><code>tests/integration/</code></td>
      <td><code>pytest tests/integration</code></td>
      <td>Real SQLAlchemy stack on in-memory SQLite; full middleware chain</td>
      <td>Every commit; after unit passes</td>
    </tr>
    <tr>
      <td><strong>End-to-End</strong></td>
      <td><code>tests/e2e/</code></td>
      <td><code>pytest tests/e2e</code></td>
      <td>Real uvicorn subprocess on port 8765; pure HTTP via <code>requests</code> — no browser</td>
      <td>Pre-merge and before marking a day done</td>
    </tr>
  </tbody>
</table>

<p><strong>Definition of Done:</strong> The app must start end-to-end and all e2e scenario tests must pass before any day is marked complete. Unit tests alone are not sufficient.</p>

<hr/>

<h2>Unit Tests — <code>tests/unit/</code></h2>
<p>Unit tests verify individual components in isolation. All tests use either FastAPI
<code>dependency_overrides</code> (for router tests) or a function-scoped in-memory SQLite session
(for repository and service tests). No real CSV files or running server are required.</p>

<table>
  <thead>
    <tr><th>File</th><th>What it tests</th><th>Key assertions</th></tr>
  </thead>
  <tbody>
    <tr>
      <td><code>test_api_system.py</code></td>
      <td>System CRUD router contracts — positions, orders, snapshots, trades, alerts, audit, market_data, config_overrides</td>
      <td>Correct HTTP status codes, response schema shapes, repository calls are wired correctly</td>
    </tr>
    <tr>
      <td><code>test_api_workflow.py</code></td>
      <td>Workflow router contracts — <code>POST /api/v1/train</code>, <code>/backtest</code>, <code>/evaluate</code></td>
      <td>All workflow POSTs return <code>202</code> with <code>status=pending</code>; services are mocked via dependency_overrides</td>
    </tr>
    <tr>
      <td><code>test_api_experience.py</code></td>
      <td>Experience Layer router contracts — <code>/api/experience/rita</code>, <code>/fno</code>, <code>/ops</code></td>
      <td>Composite payload shapes returned by read-only Experience endpoints</td>
    </tr>
    <tr>
      <td><code>test_repository.py</code></td>
      <td>SqlRepository base class via PositionsRepository</td>
      <td>read_all, get, upsert, delete operations on in-memory SQLite; isolation per test function</td>
    </tr>
    <tr>
      <td><code>test_services.py</code></td>
      <td>ManoeuvreService and PortfolioService business logic</td>
      <td>Service methods produce correct outputs for known inputs; in-memory SQLite session</td>
    </tr>
    <tr>
      <td><code>test_greeks.py</code></td>
      <td>Black-Scholes Greeks reference values</td>
      <td>Inline pricer (no <code>core/</code> import) validates Delta, Gamma, Theta, Vega to <code>abs=1e-4</code> — regression guard before any Greeks code is added to <code>core/</code></td>
    </tr>
    <tr>
      <td><code>test_auth.py</code></td>
      <td>JWT utilities — <code>create_access_token</code>, <code>get_current_user</code></td>
      <td>Valid tokens pass, expired tokens raise 401, malformed tokens raise 403</td>
    </tr>
    <tr>
      <td><code>test_middleware.py</code></td>
      <td>TraceIDMiddleware and global exception handlers</td>
      <td>Every response carries <code>X-Request-ID</code>; client-supplied IDs are echoed back; 404/422/500 all return <code>{detail, trace_id}</code> JSON</td>
    </tr>
    <tr>
      <td><code>test_config.py</code></td>
      <td>Configuration loading (Pydantic Settings + YAML hierarchy)</td>
      <td>Settings resolve correctly across base/development/production YAML files</td>
    </tr>
    <tr>
      <td><code>test_workflow_integration.py</code></td>
      <td>Cross-service workflow flows (training tracker, background dispatch)</td>
      <td>WorkflowService and BacktestService coordinate correctly; training state transitions</td>
    </tr>
  </tbody>
</table>

<h3>Running Unit Tests</h3>
<pre>
# From riia-jun-release/
pytest tests/unit -v

# Single file
pytest tests/unit/test_greeks.py -v
</pre>

<hr/>

<h2>Integration Tests — <code>tests/integration/</code></h2>
<p>Integration tests exercise the full middleware and authentication stack against a real SQLAlchemy
session backed by an in-memory SQLite database. No server process is started — FastAPI's
<code>TestClient</code> is used, so the full ASGI stack (middleware chain, dependency injection,
error handlers) runs in-process.</p>

<table>
  <thead>
    <tr><th>File</th><th>What it tests</th><th>Key assertions</th></tr>
  </thead>
  <tbody>
    <tr>
      <td><code>test_security.py</code></td>
      <td>CORS, JWT authentication, and rate limiting</td>
      <td>
        <ul>
          <li>CORS preflight returns correct <code>Access-Control-Allow-Origin</code> headers</li>
          <li>Protected workflow routes return <code>401</code> without a token and <code>200</code> with a valid JWT</li>
          <li>Rate limiter returns <code>429</code> after the configured threshold on <code>/auth/token</code></li>
          <li>Full DB schema created via <code>Base.metadata.create_all()</code> on in-memory SQLite</li>
        </ul>
      </td>
    </tr>
  </tbody>
</table>

<h3>Running Integration Tests</h3>
<pre>
pytest tests/integration -v
</pre>

<hr/>

<h2>End-to-End Tests — <code>tests/e2e/</code></h2>
<p>E2E tests run against a real uvicorn subprocess on port 8765 (started by the <code>server</code>
conftest fixture). Tests use <code>requests</code> for pure HTTP — no browser, no Playwright.
Each test represents one UI section or one user scenario. A failing test means that dashboard
section will be empty or error on load.</p>

<h3>test_smoke.py — Server Startup &amp; Critical Endpoints</h3>
<p>Fast smoke check that the server started correctly and all critical endpoints are reachable.</p>
<table>
  <thead><tr><th>Test</th><th>Endpoint</th><th>What it checks</th></tr></thead>
  <tbody>
    <tr><td>test_health_ok</td><td>GET /health</td><td>200 + <code>status: ok</code></td></tr>
    <tr><td>test_readyz_ok</td><td>GET /readyz</td><td>200 + <code>status: ready</code> (DB connectivity)</td></tr>
    <tr><td>test_openapi_docs</td><td>GET /docs</td><td>OpenAPI UI reachable</td></tr>
  </tbody>
</table>

<h3>test_rita_scenarios.py — RITA Dashboard</h3>
<p>One test per RITA dashboard section. Tests call the exact API endpoints that populate each section.</p>
<table>
  <thead><tr><th>Use Case</th><th>Dashboard Section</th><th>Endpoints exercised</th></tr></thead>
  <tbody>
    <tr><td>UC-01</td><td>Overview (Home)</td><td>GET /health, GET /readyz, GET /api/v1/metrics/summary</td></tr>
    <tr><td>UC-02</td><td>Financial Goal</td><td>GET /api/v1/performance-summary</td></tr>
    <tr><td>UC-03</td><td>Market Signals</td><td>GET /api/v1/market-signals?timeframe=daily&amp;periods=100</td></tr>
    <tr><td>UC-04</td><td>Scenarios</td><td>GET /api/v1/backtest-daily, POST /api/v1/backtest</td></tr>
    <tr><td>UC-05</td><td>Performance</td><td>GET /api/v1/performance-summary, GET /api/v1/backtest-daily</td></tr>
    <tr><td>UC-06</td><td>Trade Journal</td><td>GET /api/v1/risk-timeline?phase=all</td></tr>
    <tr><td>UC-07</td><td>Trade Diagnostics</td><td>GET /api/v1/backtest-daily</td></tr>
  </tbody>
</table>

<h3>test_fno_scenarios.py — FnO Dashboard</h3>
<p>One test per FnO menu section. A failing test maps directly to a broken FnO panel.</p>
<table>
  <thead><tr><th>Use Case</th><th>FnO Section</th><th>Endpoints exercised</th></tr></thead>
  <tbody>
    <tr><td>UC-F01</td><td>Dashboard (Overview)</td><td>GET /health, Experience Layer composite</td></tr>
    <tr><td>UC-F02+</td><td>Positions, Greeks, Margin, Payoff, Stress, Risk-Reward, Hedge</td><td>System CRUD + Experience Layer FnO endpoints</td></tr>
  </tbody>
</table>

<h3>test_ops_scenarios.py — Ops Dashboard</h3>
<p>One test per Ops menu section.</p>
<table>
  <thead><tr><th>Use Case</th><th>Ops Section</th><th>Endpoints exercised</th></tr></thead>
  <tbody>
    <tr><td>UC-O01</td><td>Overview</td><td>GET /health, GET /metrics, GET /api/v1/step-log</td></tr>
    <tr><td>UC-O02+</td><td>CI/CD, Monitoring, Observability, Test Results, Users</td><td>Ops Experience Layer + System CRUD endpoints</td></tr>
  </tbody>
</table>

<h3>Manual Scenario Plans</h3>
<p>Markdown scenario plans live alongside the Python tests as a human-readable cross-check:</p>
<ul>
  <li><code>tests/e2e/test_rita_scenarios.md</code></li>
  <li><code>tests/e2e/test_fno_scenarios.md</code></li>
  <li><code>tests/e2e/test_ops_scenarios.md</code></li>
</ul>

<h3>Running E2E Tests</h3>
<pre>
# Server must be running on port 8765 (conftest starts it automatically)
pytest tests/e2e -v

# Run only RITA scenarios
pytest tests/e2e/test_rita_scenarios.py -v
</pre>

<hr/>

<h2>CI Pipeline</h2>
<p>Tests run in this order in <code>.github/workflows/ci.yml</code>:</p>
<ol>
  <li>Lint — <code>ruff check src/</code></li>
  <li>Alembic — <code>alembic upgrade head</code></li>
  <li>Unit tests — <code>pytest tests/unit</code></li>
  <li>Integration tests — <code>pytest tests/integration</code></li>
  <li>E2E tests — <code>pytest tests/e2e</code></li>
  <li>Docker build — confirm image builds clean</li>
</ol>
<p>The CI gate blocks merge if any tier fails. Test results (JUnit XML) are written to
<code>test-results/</code> and displayed in the Ops dashboard at <code>GET /api/v1/test-results</code>.</p>

<hr/>

<h2>Test Results</h2>
<table>
  <thead><tr><th>Tier</th><th>Result file</th><th>Tests passing (v1.0)</th></tr></thead>
  <tbody>
    <tr><td>Unit</td><td><code>test-results/unit/latest.xml</code></td><td>~78 tests</td></tr>
    <tr><td>Integration</td><td><code>test-results/integration/latest.xml</code></td><td>Security suite</td></tr>
    <tr><td>E2E</td><td><code>test-results/e2e/rita/</code>, <code>fno/</code>, <code>ops/</code></td><td>47 scenario tests</td></tr>
  </tbody>
</table>

<hr/>

<h2>Rules</h2>
<ul>
  <li>Do not modify <code>core/</code> without running <code>test_greeks.py</code> first — it is the regression guard for the Black-Scholes pricer.</li>
  <li>Unit and integration tests must not start a server or read from <code>data/raw/</code> CSV files.</li>
  <li>E2E tests must not use a browser or Playwright — pure HTTP via <code>requests</code> only.</li>
  <li>All new API endpoints need at least one unit contract test and one e2e scenario test.</li>
  <li>JUnit XML output is required for Ops dashboard test result display — always pass <code>--junitxml</code> in CI.</li>
</ul>
"""


if __name__ == "__main__":
    client = ConfluenceClient()
    print(f"Updating Quality and Testing page [{PAGE_ID}]...")
    page_id, url = client.update_page(PAGE_ID, "Quality and Testing", QUALITY_HTML)
    print(f"  UPDATED [{page_id}]")
    print(f"  {url}")
