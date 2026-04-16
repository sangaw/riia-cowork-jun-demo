import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from confluence.publish import ConfluenceClient, SECTION

TITLE = "RITA v1.0 — Release Notes"
PAGE_ID = None  # Set after first run

BODY = """
<h1>RITA v1.0 Release Notes</h1>
<p><strong>Release Date:</strong> 2026-04-16 &nbsp;|&nbsp; <strong>Tag:</strong> <code>v1.0</code></p>
<p>
  RITA (Risk Informed Investment Approach) v1.0 is the first production-grade release of
  the Nifty 50 Double DQN reinforcement-learning trading system and FnO portfolio manager.
  This release represents a full refactor of the POC codebase over 42 days across 7 sprints.
</p>

<h2>What Is RITA?</h2>
<ul>
  <li>A <strong>Double DQN reinforcement-learning agent</strong> trained on Nifty 50 OHLCV data to make daily allocation decisions (0%, 50%, or 100% invested).</li>
  <li>A <strong>FnO portfolio manager</strong> tracking option positions, manoeuvres, Greeks, and daily P&amp;L.</li>
  <li>A <strong>three-dashboard web application</strong>: RITA (model training &amp; signals), FnO (portfolio), and Ops (observability &amp; CI/CD).</li>
  <li>A <strong>production-grade FastAPI backend</strong>: SQLite/SQLAlchemy ORM, JWT auth, rate limiting, structured logging, Prometheus metrics.</li>
</ul>

<h2>Release Summary</h2>
<table>
  <thead><tr><th>Sprint</th><th>Theme</th><th>Days</th><th>Status</th></tr></thead>
  <tbody>
    <tr><td>Sprint 0</td><td>Architecture &amp; Schema Design</td><td>1–3</td><td><strong style="color:#1a6b3c">&#10003; Complete</strong></td></tr>
    <tr><td>Sprint 1</td><td>Foundation: Config, Repositories, CI</td><td>4–8</td><td><strong style="color:#1a6b3c">&#10003; Complete</strong></td></tr>
    <tr><td>Sprint 2</td><td>API Layer (System + Workflow + Experience)</td><td>9–14</td><td><strong style="color:#1a6b3c">&#10003; Complete</strong></td></tr>
    <tr><td>Sprint 2.5</td><td>Database Migration (SQLite + SQLAlchemy)</td><td>15–18</td><td><strong style="color:#1a6b3c">&#10003; Complete</strong></td></tr>
    <tr><td>Sprint 3</td><td>Service Layer &amp; Observability</td><td>19–24</td><td><strong style="color:#1a6b3c">&#10003; Complete</strong></td></tr>
    <tr><td>Sprint 4</td><td>Frontend &amp; Responsive Design</td><td>25–30</td><td><strong style="color:#1a6b3c">&#10003; Complete</strong></td></tr>
    <tr><td>Sprint 5</td><td>Security, k8s, Integration</td><td>31–33</td><td><strong style="color:#1a6b3c">&#10003; Complete</strong></td></tr>
    <tr><td>Sprint 6</td><td>Model Building, Performance Analytics, Drift</td><td>35–40</td><td><strong style="color:#1a6b3c">&#10003; Complete</strong></td></tr>
  </tbody>
</table>

<h2>Key Features</h2>

<h3>AI / ML Engine</h3>
<ul>
  <li>Double DQN agent (stable-baselines3) with three allocation actions: 0%, 50%, 100%.</li>
  <li>Multi-seed training (<code>train_best_of_n</code>) selects the best model by validation Sharpe.</li>
  <li>Real backtest dispatch: deterministic episode replay with daily P&amp;L, benchmark comparison, and Sharpe/MDD/CAGR computation.</li>
  <li>TrainingTracker: JSON audit log of every training round including val metrics, constraints met, and seed used.</li>
  <li>DriftDetector: 5 DB-backed health checks — Sharpe drift, return degradation, data freshness, pipeline health, constraint breach.</li>
  <li>Performance analytics: portfolio comparison vs fixed profiles, qualitative feedback, stress testing.</li>
</ul>

<h3>API</h3>
<ul>
  <li>Three-tier architecture (ADR-001): System CRUD, Workflow (train/backtest/evaluate), Experience Layer (dashboard payloads).</li>
  <li>JWT authentication on workflow endpoints; rate limiting via slowapi (60 req/min default, 10 req/min on /auth/token).</li>
  <li>Full observability: <code>/health</code>, <code>/readyz</code>, <code>/metrics</code> (Prometheus), <code>/api/v1/drift</code>, <code>/api/v1/metrics/summary</code>.</li>
  <li>Chat pipeline: local intent classifier (all-MiniLM-L6-v2) + deterministic OHLCV dispatch — no external API dependency.</li>
  <li>48 functional scenario tests across RITA, FnO, and Ops dashboards (all passing).</li>
</ul>

<h3>Database</h3>
<ul>
  <li>SQLite via SQLAlchemy 2.x ORM (ADR-003). PostgreSQL upgrade: change one <code>database_url</code> config value.</li>
  <li>17 ORM models, Alembic migrations, DB seeded on startup (instruments + Nifty 50 market data).</li>
  <li>Repository pattern throughout (ADR-002): no direct DB access in routes or services.</li>
</ul>

<h3>Frontend</h3>
<ul>
  <li>Three dashboards (RITA, FnO, Ops) decomposed into ES modules — 21 + 14 + 12 modules respectively.</li>
  <li>Fully responsive at 480px / 768px / 1100px breakpoints.</li>
  <li>Zero hardcoded localhost URLs — all API calls use <code>window.RITA_API_BASE</code>.</li>
  <li>TEST menu in Ops dashboard shows live JUnit XML results for all three e2e suites.</li>
</ul>

<h3>Infrastructure</h3>
<ul>
  <li>Multi-stage Dockerfile (builder lints + tests; runtime non-root user).</li>
  <li>GitHub Actions CI: lint → unit tests → Alembic migration → e2e tests → Docker build.</li>
  <li>Kubernetes manifests: <code>k8s/deployment.yaml</code>, <code>k8s/service.yaml</code>, <code>k8s/ingress.yaml</code>.</li>
  <li>Docker Compose for local development.</li>
  <li>Terraform scaffolding for cloud provider deployment.</li>
</ul>

<h2>API Reference — New in v1.0</h2>
<table>
  <thead><tr><th>Endpoint</th><th>Method</th><th>Auth</th><th>Description</th></tr></thead>
  <tbody>
    <tr><td>/api/v1/pipeline</td><td>POST</td><td>None</td><td>Full train &rarr; backtest pipeline (async)</td></tr>
    <tr><td>/api/v1/training-history</td><td>GET</td><td>None</td><td>All training rounds, newest first</td></tr>
    <tr><td>/api/v1/training-progress</td><td>GET</td><td>None</td><td>Live progress for in-flight training run</td></tr>
    <tr><td>/api/v1/drift</td><td>GET</td><td>None</td><td>5-check drift &amp; health report</td></tr>
    <tr><td>/api/v1/performance-feedback</td><td>GET</td><td>None</td><td>Qualitative backtest feedback</td></tr>
    <tr><td>/api/v1/portfolio-comparison</td><td>GET</td><td>None</td><td>RITA vs fixed allocation profiles</td></tr>
    <tr><td>/api/v1/stress-scenarios</td><td>GET</td><td>None</td><td>Stress test across market moves</td></tr>
    <tr><td>/api/v1/market-signals</td><td>GET</td><td>None</td><td>OHLCV + 10 technical indicators time series</td></tr>
    <tr><td>/api/v1/risk-timeline</td><td>GET</td><td>None</td><td>Backtest daily risk metrics with regime labels</td></tr>
    <tr><td>/api/v1/trade-events</td><td>GET</td><td>None</td><td>Entry/exit events from allocation changes</td></tr>
    <tr><td>/api/v1/shap</td><td>GET</td><td>None</td><td>SHAP feature importance for explainability</td></tr>
    <tr><td>/api/v1/chat</td><td>POST</td><td>None</td><td>Intent classification + OHLCV response</td></tr>
    <tr><td>/api/v1/chat/monitor</td><td>GET</td><td>None</td><td>Chat KPIs and recent query log</td></tr>
    <tr><td>/api/v1/portfolio/summary</td><td>GET</td><td>None</td><td>FnO overview KPI cards</td></tr>
    <tr><td>/api/v1/portfolio/price-history</td><td>GET</td><td>None</td><td>NIFTY price history for charts</td></tr>
    <tr><td>/api/v1/data-prep/status</td><td>GET</td><td>None</td><td>Data preparation pipeline status</td></tr>
    <tr><td>/auth/token</td><td>POST</td><td>None</td><td>Issue JWT bearer token</td></tr>
    <tr><td>/api/v1/workflow/train</td><td>POST</td><td>JWT</td><td>Submit training run</td></tr>
    <tr><td>/api/v1/workflow/backtest</td><td>POST</td><td>JWT</td><td>Submit backtest run</td></tr>
    <tr><td>/api/v1/instruments</td><td>GET / POST</td><td>None / None</td><td>List or register instruments</td></tr>
  </tbody>
</table>

<h2>Test Coverage</h2>
<table>
  <thead><tr><th>Suite</th><th>Tests</th><th>Pass</th><th>Fail</th></tr></thead>
  <tbody>
    <tr><td>Unit + Integration</td><td>122</td><td>121</td><td>1 (pre-existing JWT env-var)</td></tr>
    <tr><td>RITA e2e scenarios</td><td>20</td><td>20</td><td>0</td></tr>
    <tr><td>FnO e2e scenarios</td><td>11</td><td>11</td><td>0</td></tr>
    <tr><td>Ops e2e scenarios</td><td>16</td><td>16</td><td>0</td></tr>
    <tr><td><strong>Total</strong></td><td><strong>169</strong></td><td><strong>168</strong></td><td><strong>1</strong></td></tr>
  </tbody>
</table>

<h2>Known Limitations (v2 Scope)</h2>
<ul>
  <li>SQLite — upgrade to PostgreSQL by changing <code>database_url</code> in config.</li>
  <li>SHAP values are representative (static) — live SHAP inference requires a loaded model at request time.</li>
  <li>JWT secret is config-driven (not HSM-backed) — suitable for development and staging.</li>
  <li>Model training is synchronous in the background thread — large timestep runs block the thread pool.</li>
  <li>Nifty 50 only — multi-instrument support is scaffolded (instruments table, data loader) but models are per-instrument.</li>
</ul>

<h2>Upgrade / Deploy</h2>
<pre>
# Pull latest
git checkout master
git pull

# Install dependencies
pip install -e ".[dev]"

# Run migrations
alembic upgrade head

# Start server
uvicorn rita.main:app --host 0.0.0.0 --port 8000

# Or with Docker Compose
docker-compose up --build
</pre>
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
