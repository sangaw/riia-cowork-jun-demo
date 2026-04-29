"""
Create the RIIA App product section + Project Summary page on Confluence.

Pages created:
  1. Project Summary          (parent: homepage)
  2. RIIA App                 (parent: homepage)  ← product section root
     2a. Requirements         (parent: RIIA App)
     2b. Architecture         (parent: RIIA App)
     2c. Engineering          (parent: RIIA App)
     2d. Operations           (parent: RIIA App)

Run from any directory:
  CONFLUENCE_EMAIL=contact@ravionics.nl python project-office/confluence/pages/publish_product_section.py
"""

import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from confluence.publish import ConfluenceClient, HOMEPAGE_ID

client = ConfluenceClient()

# ── helpers ──────────────────────────────────────────────────────────────────

def publish(title, html, parent_id):
    page_id, url = client.create_page(title, html, parent_id=parent_id)
    print(f"  CREATED [{page_id}] '{title}'\n  {url}\n")
    return page_id


# ─────────────────────────────────────────────────────────────────────────────
# 1. PROJECT SUMMARY
# ─────────────────────────────────────────────────────────────────────────────

PROJECT_SUMMARY_HTML = """
<h1>Project Summary</h1>
<p><strong>Project:</strong> RITA Production Refactor &nbsp;|&nbsp;
   <strong>Status:</strong> <span style="color:#1A6B3C;font-weight:bold;">v1.0 Released</span> &nbsp;|&nbsp;
   <strong>Release date:</strong> 2026-04-16 &nbsp;|&nbsp;
   <strong>Total days:</strong> 42</p>

<hr/>

<h2>What We Built</h2>
<p>RITA (Risk Informed Approach) is a Nifty 50 Double DQN reinforcement learning trading system and
FnO portfolio manager, refactored from a working POC into a production-ready application over 42 days
using a Claude AI cowork team.</p>

<table>
  <thead>
    <tr><th>Component</th><th>Description</th></tr>
  </thead>
  <tbody>
    <tr><td><strong>Trading Engine</strong></td><td>Double DQN RL model trained on NIFTY 50, BANKNIFTY, ASML, NVIDIA — 25 years of OHLCV data</td></tr>
    <tr><td><strong>FnO Portfolio Manager</strong></td><td>Options positions tracker with Greeks, margin, payoff diagrams, stress tests, risk-reward analysis</td></tr>
    <tr><td><strong>RITA Dashboard</strong></td><td>21-section web app: market signals, trade journal, performance analytics, training, scenarios, chat, agent panel</td></tr>
    <tr><td><strong>FnO Dashboard</strong></td><td>14-module FnO portfolio view with live Greeks calculator and hedge radar</td></tr>
    <tr><td><strong>Ops Dashboard</strong></td><td>System monitoring, CI/CD status, test results, user management, observability</td></tr>
    <tr><td><strong>Chat Assistant</strong></td><td>Local NLP classifier (sentence-transformers), 20 intents, deterministic handlers — no LLM at runtime</td></tr>
    <tr><td><strong>Agent Panel</strong></td><td>LangGraph 6-agent simulation with Human-in-the-Loop approval for BUY signals</td></tr>
    <tr><td><strong>Mobile PWA</strong></td><td>10-screen installable Android app with live data, sparklines, and offline support</td></tr>
  </tbody>
</table>

<hr/>

<h2>Sprint Summary</h2>

<table>
  <thead>
    <tr><th>Sprint</th><th>Days</th><th>Theme</th><th>Key Deliverables</th><th>Status</th></tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>Sprint 0</strong></td>
      <td>1–3</td>
      <td>Architecture &amp; Planning</td>
      <td>Folder structure, ADR-001 (three-tier API), ADR-002 (repository pattern), 16 Pydantic schemas, Confluence bootstrap</td>
      <td><span style="color:#1A6B3C;">&#10003; Done</span></td>
    </tr>
    <tr>
      <td><strong>Sprint 1</strong></td>
      <td>4–8</td>
      <td>Foundation</td>
      <td>Pydantic Settings + config YAML hierarchy, CSV repository layer (15 tables), multi-stage Dockerfile, CI pipeline, JWT secret handling</td>
      <td><span style="color:#1A6B3C;">&#10003; Done</span></td>
    </tr>
    <tr>
      <td><strong>Sprint 2</strong></td>
      <td>9–14</td>
      <td>API Decomposition</td>
      <td>8 System CRUD routers, 3 Workflow routers (train/backtest/evaluate), 3 Experience Layer routers (dashboard/fno/ops), trace ID middleware, 78 API contract tests</td>
      <td><span style="color:#1A6B3C;">&#10003; Done</span></td>
    </tr>
    <tr>
      <td><strong>Sprint 2.5</strong></td>
      <td>15–18</td>
      <td>Database Layer</td>
      <td>ADR-003 (SQLite via SQLAlchemy 2.x), 15 ORM models, SqlRepository base, Alembic migrations, full test suite migration to in-memory SQLite</td>
      <td><span style="color:#1A6B3C;">&#10003; Done</span></td>
    </tr>
    <tr>
      <td><strong>Sprint 3</strong></td>
      <td>19–24</td>
      <td>Service Layer &amp; Observability</td>
      <td>WorkflowService + BacktestService (real ML dispatch), ManoeuvreService, PortfolioService, structlog JSON logging, Prometheus metrics, /health + /readyz probes</td>
      <td><span style="color:#1A6B3C;">&#10003; Done</span></td>
    </tr>
    <tr>
      <td><strong>Sprint 4</strong></td>
      <td>25–30</td>
      <td>Frontend &amp; Responsive Design</td>
      <td>rita.html → 21 ES modules, fno.html → 14 ES modules, ops.html → 12 ES modules, 3-breakpoint responsive CSS, removed localhost hardcoding, Playwright e2e tests</td>
      <td><span style="color:#1A6B3C;">&#10003; Done</span></td>
    </tr>
    <tr>
      <td><strong>Sprint 5</strong></td>
      <td>31–34</td>
      <td>Integration, Security &amp; Release</td>
      <td>CORS, JWT auth on workflow routes, rate limiting (slowapi), input validation, Terraform + k8s manifests, scenario test suites (48 tests)</td>
      <td><span style="color:#1A6B3C;">&#10003; Done</span></td>
    </tr>
    <tr>
      <td><strong>Sprint 6</strong></td>
      <td>35–42</td>
      <td>Model Building, ML &amp; Release</td>
      <td>Real backtest dispatch engine, train_best_of_n, TrainingTracker, performance analytics (portfolio comparison, stress simulation), DriftDetector, 47 e2e scenario tests passing, v1.0 tag</td>
      <td><span style="color:#1A6B3C;">&#10003; Done</span></td>
    </tr>
  </tbody>
</table>

<hr/>

<h2>Key Milestones</h2>

<table>
  <thead>
    <tr><th>Date</th><th>Milestone</th></tr>
  </thead>
  <tbody>
    <tr><td>2026-03-30</td><td>Project kicked off. Folder structure and ADRs written on Day 1.</td></tr>
    <tr><td>2026-04-02</td><td>Sprint 2.5 added — SQLite/SQLAlchemy replaces CSV backend. Zero impact on API contracts.</td></tr>
    <tr><td>2026-04-12</td><td>Sprint 6 added — real RL training + backtest engine ported from POC.</td></tr>
    <tr><td>2026-04-16</td><td><strong>v1.0 released.</strong> All 42 days complete. 47/47 e2e scenario tests passing.</td></tr>
    <tr><td>2026-04-25</td><td>Agent Panel + AI Compliance dashboard added. Mobile PWA integrated with live data.</td></tr>
    <tr><td>2026-04-29</td><td>Skill system complete — 12 self-contained slash commands covering all feature work types.</td></tr>
  </tbody>
</table>

<hr/>

<h2>Technology Stack</h2>

<table>
  <thead>
    <tr><th>Layer</th><th>Technology</th></tr>
  </thead>
  <tbody>
    <tr><td><strong>Language</strong></td><td>Python 3.12, Vanilla JavaScript (ES Modules)</td></tr>
    <tr><td><strong>API Framework</strong></td><td>FastAPI + Uvicorn</td></tr>
    <tr><td><strong>Database</strong></td><td>SQLite via SQLAlchemy 2.x ORM + Alembic migrations (PostgreSQL in v2)</td></tr>
    <tr><td><strong>ML / RL</strong></td><td>Stable Baselines3 — DoubleDQN; NumPy, pandas, scikit-learn</td></tr>
    <tr><td><strong>NLP</strong></td><td>sentence-transformers/all-MiniLM-L6-v2 (local, no API calls)</td></tr>
    <tr><td><strong>Frontend</strong></td><td>Chart.js, Vanilla JS ES Modules — no bundler, no framework</td></tr>
    <tr><td><strong>Auth</strong></td><td>JWT (python-jose), slowapi rate limiting, CORS</td></tr>
    <tr><td><strong>Logging</strong></td><td>structlog (JSON), Prometheus (prometheus-fastapi-instrumentator)</td></tr>
    <tr><td><strong>Testing</strong></td><td>pytest, Playwright (e2e), JUnit XML test result integration</td></tr>
    <tr><td><strong>Infra</strong></td><td>Docker (multi-stage), k8s manifests, Terraform scaffolding</td></tr>
    <tr><td><strong>Mobile</strong></td><td>PWA — single-file, installable on Android, service worker offline cache</td></tr>
  </tbody>
</table>

<hr/>

<h2>Related Pages</h2>
<ul>
  <li><a href="https://ravionics.atlassian.net/wiki/spaces/RIIAProjec/pages/65110386">RITA Production Refactor — Master Plan</a></li>
  <li><a href="https://ravionics.atlassian.net/wiki/spaces/RIIAProjec/pages/71794689">v1.0 Release Notes</a></li>
  <li><a href="https://ravionics.atlassian.net/wiki/spaces/RIIAProjec/pages/65077274">Sprint Boards</a></li>
  <li><a href="https://ravionics.atlassian.net/wiki/spaces/RIIAProjec/pages/65339419">Architecture and Design</a></li>
  <li><a href="https://ravionics.atlassian.net/wiki/spaces/RIIAProjec/pages/65404944">Engineering Documentation</a></li>
</ul>
"""

# ─────────────────────────────────────────────────────────────────────────────
# 2. RIIA APP — product section root
# ─────────────────────────────────────────────────────────────────────────────

RIIA_APP_HTML = """
<h1>RIIA App</h1>
<p>Current state of the RITA application — requirements, architecture, engineering, and operations.
This section covers the <strong>live product</strong> as of v1.0. For historical sprint artefacts,
see the <a href="https://ravionics.atlassian.net/wiki/spaces/RIIAProjec/pages/65273887">Project Management</a> section.</p>

<h2>Quick Navigation</h2>
<table>
  <thead>
    <tr><th>Page</th><th>Contents</th></tr>
  </thead>
  <tbody>
    <tr><td><strong>Requirements</strong></td><td>Product features, user stories, non-functional requirements, instrument coverage</td></tr>
    <tr><td><strong>Architecture</strong></td><td>Three-tier API design, repository pattern, data flow, component map, technology stack</td></tr>
    <tr><td><strong>Engineering</strong></td><td>API inventory, key source files, development workflow, slash commands, spec files</td></tr>
    <tr><td><strong>Operations</strong></td><td>Running the app, configuration, data management, health probes, monitoring, troubleshooting</td></tr>
  </tbody>
</table>

<h2>Product in One Line</h2>
<p>RITA is a <strong>Nifty 50 Double DQN RL trading system</strong> and <strong>FnO portfolio manager</strong>
with three web dashboards, a local chat assistant, an agentic AI panel with Human-in-the-Loop approvals,
and an installable mobile PWA — all backed by a production FastAPI + SQLite service.</p>

<h2>Instrument Coverage</h2>
<table>
  <thead>
    <tr><th>Instrument</th><th>Exchange</th><th>History</th><th>Use</th></tr>
  </thead>
  <tbody>
    <tr><td>NIFTY 50</td><td>NSE India</td><td>1999–present</td><td>Primary RL trading instrument</td></tr>
    <tr><td>BANKNIFTY</td><td>NSE India</td><td>2007–present</td><td>Secondary RL instrument + FnO positions</td></tr>
    <tr><td>ASML</td><td>Euronext Amsterdam</td><td>2001–present</td><td>FnO positions, Agent Panel demo</td></tr>
    <tr><td>NVIDIA</td><td>NASDAQ</td><td>2001–present</td><td>FnO positions, portfolio benchmarking</td></tr>
  </tbody>
</table>
"""

# ─────────────────────────────────────────────────────────────────────────────
# 2a. REQUIREMENTS
# ─────────────────────────────────────────────────────────────────────────────

REQUIREMENTS_HTML = """
<h1>Requirements</h1>
<p><strong>Version:</strong> v1.0 &nbsp;|&nbsp; <strong>Date:</strong> 2026-04-29</p>
<p>Product requirements for the RITA application as delivered in v1.0.
This is a live document — update when features are added or changed.</p>

<hr/>

<h2>Product Overview</h2>
<p>RITA is a personal trading intelligence platform built around a reinforcement learning model trained
on 25 years of Nifty 50 data. It provides three interconnected capabilities:</p>
<ol>
  <li><strong>Trading system</strong> — RL agent (Double DQN) that makes allocation decisions based on market signals</li>
  <li><strong>FnO portfolio manager</strong> — tracks real and paper options positions with Greeks, margin, and risk analytics</li>
  <li><strong>Intelligence layer</strong> — chat assistant, agentic AI panel, AI compliance dashboard, and mobile PWA</li>
</ol>

<hr/>

<h2>Feature Inventory</h2>

<h3>Trading System</h3>
<table>
  <thead><tr><th>Feature</th><th>Detail</th><th>Status</th></tr></thead>
  <tbody>
    <tr><td>RL Training</td><td>DoubleDQN agent on NIFTY/BANKNIFTY/ASML/NVIDIA — train_best_of_n with n_seeds</td><td>v1.0</td></tr>
    <tr><td>Backtesting</td><td>Walk-forward backtest engine (real run_episode), performance_summary.json output</td><td>v1.0</td></tr>
    <tr><td>Market Signals</td><td>RSI-14, MACD, Bollinger Bands, ATR-14, EMA-5/13/26/50, trend score — daily/weekly/monthly</td><td>v1.0</td></tr>
    <tr><td>Performance Analytics</td><td>Portfolio comparison, performance feedback, stress simulation (crash/rally/flat)</td><td>v1.0</td></tr>
    <tr><td>Drift Detection</td><td>5 DB-backed drift checks: allocation, vol, drawdown, feature, regime</td><td>v1.0</td></tr>
    <tr><td>Goal Analysis</td><td>Target return feasibility scoring (conservative/realistic/ambitious/unrealistic)</td><td>v1.0</td></tr>
  </tbody>
</table>

<h3>FnO Portfolio Manager</h3>
<table>
  <thead><tr><th>Feature</th><th>Detail</th><th>Status</th></tr></thead>
  <tbody>
    <tr><td>Positions</td><td>Real and paper positions; lot size, avg, LTP, PnL, expiry per row</td><td>v1.0</td></tr>
    <tr><td>Greeks</td><td>Delta, Gamma, Theta, Vega via Black-Scholes (Experience Layer)</td><td>v1.0</td></tr>
    <tr><td>Margin Tracker</td><td>Used vs available margin per position group</td><td>v1.0</td></tr>
    <tr><td>Payoff Diagram</td><td>P&amp;L curve at expiry across price range</td><td>v1.0</td></tr>
    <tr><td>Stress Tests</td><td>Scenario levels from CSV — portfolio P&amp;L at each price level</td><td>v1.0</td></tr>
    <tr><td>Risk-Reward</td><td>Rolling R/R ratio chart with price history overlay</td><td>v1.0</td></tr>
    <tr><td>Hedge Radar</td><td>Multi-axis hedge coverage visualisation</td><td>v1.0</td></tr>
  </tbody>
</table>

<h3>Dashboards</h3>
<table>
  <thead><tr><th>Dashboard</th><th>Sections</th><th>Status</th></tr></thead>
  <tbody>
    <tr><td>RITA (rita.html)</td><td>Home KPIs, Market Signals, Trades, Performance, Risk, Training, Scenarios, Export, Observability, Chat, Agent Panel, AI Compliance, Audit, Diagnostics, Explainability</td><td>v1.0</td></tr>
    <tr><td>FnO (fno.html)</td><td>Overview, Positions, Greeks, Margin, Payoff, Stress, Risk-Reward, Hedge, Manoeuvre</td><td>v1.0</td></tr>
    <tr><td>Ops (ops.html)</td><td>Overview, CI/CD, Monitoring, Observability, Test Results, Daily Ops, Deploy, Users, Chat</td><td>v1.0</td></tr>
  </tbody>
</table>

<h3>Intelligence Features</h3>
<table>
  <thead><tr><th>Feature</th><th>Detail</th><th>Status</th></tr></thead>
  <tbody>
    <tr><td>Chat Assistant</td><td>Local NLP classifier, 20 intents, sentence-transformers — no LLM at runtime</td><td>v1.0</td></tr>
    <tr><td>Agent Panel</td><td>LangGraph 6-agent simulation (Analyst, Risk, Compliance, Portfolio, Narrator, Coordinator) with HITL approval for BUY signals</td><td>v1.0+</td></tr>
    <tr><td>AI Compliance</td><td>Governance tab, guardrails tab, trace inspector — reads agent history from localStorage</td><td>v1.0+</td></tr>
    <tr><td>Mobile PWA</td><td>10-screen installable app (Android), live data toggle, sparklines, offline cache</td><td>v1.0+</td></tr>
  </tbody>
</table>

<hr/>

<h2>Non-Functional Requirements</h2>
<table>
  <thead><tr><th>Requirement</th><th>Target</th><th>How Met</th></tr></thead>
  <tbody>
    <tr><td>API response time</td><td>&lt; 200ms for read endpoints</td><td>SQLite + connection pooling; Experience Layer pre-aggregates</td></tr>
    <tr><td>DB startup seeding</td><td>&lt; 10 seconds</td><td>Bulk db.add_all() — 260 rows per instrument, not row-by-row</td></tr>
    <tr><td>Auth</td><td>JWT on all write/workflow routes</td><td>python-jose, /auth/token endpoint, get_current_user dependency</td></tr>
    <tr><td>Rate limiting</td><td>60 req/min default, 10/min on /auth/token</td><td>slowapi</td></tr>
    <tr><td>Observability</td><td>Structured logs, Prometheus metrics, health probes</td><td>structlog JSON, prometheus-fastapi-instrumentator, /health + /readyz</td></tr>
    <tr><td>Database portability</td><td>SQLite → PostgreSQL with zero code changes</td><td>ADR-003: one config value change (database_url)</td></tr>
    <tr><td>Data integrity</td><td>All source data read-only</td><td>data/raw/ never written from code; API writes only to data/output/</td></tr>
    <tr><td>Mobile</td><td>Installable on Android Chrome</td><td>manifest.json + service worker offline cache</td></tr>
    <tr><td>Test coverage</td><td>≥ 80% unit, 47 e2e scenario tests</td><td>pytest + Playwright; CI gates on both</td></tr>
  </tbody>
</table>

<hr/>

<h2>Out of Scope (v1.0)</h2>
<ul>
  <li>Live broker integration (Zerodha/IBKR API) — positions are paper/manual CSV import</li>
  <li>Real-time data feeds — all data is local CSV, updated manually</li>
  <li>PostgreSQL migration — v2 work</li>
  <li>Multi-user access control beyond basic JWT</li>
  <li>iOS PWA (service worker limitations on iOS Safari)</li>
</ul>
"""

# ─────────────────────────────────────────────────────────────────────────────
# 2b. ARCHITECTURE
# ─────────────────────────────────────────────────────────────────────────────

ARCHITECTURE_HTML = """
<h1>Architecture</h1>
<p><strong>Version:</strong> v1.0 &nbsp;|&nbsp; <strong>Date:</strong> 2026-04-29</p>
<p>Current system architecture. For the decision trail, see
<a href="https://ravionics.atlassian.net/wiki/spaces/RIIAProjec/pages/65339419">Architecture and Design</a>
(ADR-001, ADR-002, ADR-003).</p>

<hr/>

<h2>Three-Tier API Design (ADR-001)</h2>
<p>All API routes are assigned to exactly one of three tiers. No exceptions.</p>

<table>
  <thead>
    <tr><th>Tier</th><th>Path prefix</th><th>Rule</th><th>Examples</th></tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>System (CRUD)</strong></td>
      <td><code>api/v1/system/</code></td>
      <td>One table, zero logic. Call one repository only.</td>
      <td>positions, orders, alerts, audit, market_data</td>
    </tr>
    <tr>
      <td><strong>Workflow</strong></td>
      <td><code>api/v1/workflow/</code></td>
      <td>Multi-step or ML process. Services only — no direct repo calls.</td>
      <td>train, backtest, evaluate, chat, pipeline</td>
    </tr>
    <tr>
      <td><strong>Experience</strong></td>
      <td><code>api/experience/</code></td>
      <td>Read-only UI payload. Composes from multiple sources.</td>
      <td>rita, fno, ops, ds, greeks</td>
    </tr>
  </tbody>
</table>

<hr/>

<h2>Repository Pattern (ADR-002)</h2>
<p>No direct DB or file access in routes or services. All data through repository classes.</p>
<pre>
Route → Service → Repository → SQLAlchemy Session → SQLite
</pre>
<ul>
  <li><code>SqlRepository[Model, Schema]</code> — generic base with read_all, get, upsert, delete</li>
  <li>One repository class per table (15 tables, 15 repo classes)</li>
  <li>Every repo constructor requires <code>db: Session</code> — injected via FastAPI <code>Depends(get_db)</code></li>
  <li>Background threads open their own <code>SessionLocal()</code> — never pass a request-scoped session across threads</li>
</ul>

<hr/>

<h2>Data Layer (ADR-003)</h2>
<table>
  <thead><tr><th>Layer</th><th>Technology</th><th>Notes</th></tr></thead>
  <tbody>
    <tr><td>ORM</td><td>SQLAlchemy 2.x</td><td>15 model files, 17 ORM classes, all inherit <code>rita.database.Base</code></td></tr>
    <tr><td>Database</td><td>SQLite (<code>data/output/rita.db</code>)</td><td>v2 upgrade path: change <code>database_url</code> config — zero code changes</td></tr>
    <tr><td>Migrations</td><td>Alembic</td><td>Run <code>alembic upgrade head</code> before starting; CI does this automatically</td></tr>
    <tr><td>Seeding</td><td>lifespan() in main.py</td><td>Market data cached for 2025+2026 window (bulk insert, &lt;2s each instrument)</td></tr>
    <tr><td>Source data</td><td>CSV files in <code>data/raw/</code></td><td>Read-only. Never written by code.</td></tr>
  </tbody>
</table>

<hr/>

<h2>Component Map</h2>
<pre>
Browser / Mobile PWA
        |
        | HTTP (RITA_API_BASE)
        v
FastAPI Application  (src/rita/main.py)
  ├── Middleware: TraceIDMiddleware, CORSMiddleware, PrometheusMiddleware, SlowAPI
  ├── Auth:       POST /auth/token  →  JWT
  │
  ├── System Routers  (api/v1/system/)
  │   └── positions, orders, alerts, audit, market_data, instruments, drift, training_runs, data_prep
  │
  ├── Workflow Routers  (api/v1/workflow/)
  │   └── train, backtest, evaluate, chat (classifier), pipeline
  │
  └── Experience Routers  (api/experience/)
      └── rita, fno, ops, ds, pipeline_wizard
        |
        v
Services  (src/rita/services/)
  WorkflowService, BacktestService, ManoeuvreService, PortfolioService
        |
        v
Repositories  (src/rita/repositories/)
  SqlRepository base + 15 concrete classes
        |
        v
SQLite  (data/output/rita.db)  ←→  CSV source files  (data/raw/)
        |
        v
Core  (src/rita/core/)
  data_loader, trading_env, ml_dispatch, backtest_dispatch,
  classifier, performance, drift_detector, training_tracker
</pre>

<hr/>

<h2>Frontend Architecture</h2>
<table>
  <thead><tr><th>Dashboard</th><th>File</th><th>JS modules</th><th>Key pattern</th></tr></thead>
  <tbody>
    <tr><td>RITA</td><td>dashboard/rita.html</td><td>21 ES modules in dashboard/js/rita/</td><td>Section loader pattern — _sectionLoaders map in nav.js/main.js</td></tr>
    <tr><td>FnO</td><td>dashboard/fno.html</td><td>14 ES modules in dashboard/js/fno/</td><td>Shared state.js for active instrument/expiry; same loader pattern</td></tr>
    <tr><td>Ops</td><td>dashboard/ops.html</td><td>14 ES modules in dashboard/js/ops/</td><td>sidebar.js navigation; admin-gated routes</td></tr>
    <tr><td>Mobile</td><td>android-mobile-app/index.html</td><td>Inline JS (single file)</td><td>goTo(n) carousel; fetch pattern with null-fallback; LIVE_MODE toggle</td></tr>
  </tbody>
</table>

<hr/>

<h2>Security</h2>
<ul>
  <li><strong>JWT:</strong> <code>POST /auth/token</code> issues HS256 tokens. Workflow routes require <code>get_current_user</code> dependency.</li>
  <li><strong>CORS:</strong> Origins set in <code>config/base.yaml → security.cors_origins</code></li>
  <li><strong>Rate limiting:</strong> 60 req/min global, 10 req/min on <code>/auth/token</code> (slowapi)</li>
  <li><strong>Input validation:</strong> Field constraints on 9 schemas (max_length, ge=0, pattern)</li>
  <li><strong>Secrets:</strong> JWT secret from env var <code>RITA_JWT_SECRET</code> — never in YAML</li>
</ul>

<hr/>

<h2>Observability</h2>
<ul>
  <li><code>GET /health</code> — liveness: model exists, CSV loaded, data freshness, Sharpe trend</li>
  <li><code>GET /readyz</code> — readiness: DB SELECT 1 (503 on failure)</li>
  <li><code>GET /metrics</code> — Prometheus endpoint (prometheus-fastapi-instrumentator)</li>
  <li><code>GET /api/v1/metrics/summary</code> — structured JSON summary for Ops dashboard</li>
  <li><code>GET /api/v1/drift</code> — 5 drift checks (allocation, vol, drawdown, feature, regime)</li>
  <li>structlog JSON logs with <code>trace_id</code> bound per request via TraceIDMiddleware</li>
</ul>
"""

# ─────────────────────────────────────────────────────────────────────────────
# 2c. ENGINEERING
# ─────────────────────────────────────────────────────────────────────────────

ENGINEERING_HTML = """
<h1>Engineering</h1>
<p><strong>Version:</strong> v1.0 &nbsp;|&nbsp; <strong>Date:</strong> 2026-04-29</p>
<p>Source structure, API inventory, development workflow, and slash command reference.</p>

<hr/>

<h2>Source Layout</h2>
<pre>
riia-jun-release/
  src/rita/
    api/
      v1/system/       ← CRUD routers (one file per resource)
      v1/workflow/     ← Business process routers
      experience/      ← Read-only UI payload routers
    services/          ← Business logic (WorkflowService, BacktestService, …)
    repositories/      ← Data access (one class per table)
    schemas/           ← Pydantic request/response models
    models/            ← SQLAlchemy ORM models
    core/              ← ML, indicators, data loading, analytics
    auth.py            ← JWT utilities
    config.py          ← Pydantic Settings
    database.py        ← SQLAlchemy engine, SessionLocal, Base, get_db
    main.py            ← FastAPI app, lifespan, router registration, seeding
  dashboard/
    js/rita/           ← 21 ES modules for RITA dashboard
    js/fno/            ← 14 ES modules for FnO dashboard
    js/ops/            ← 14 ES modules for Ops dashboard
    css/               ← responsive.css + component styles
  data/
    raw/               ← Immutable source CSVs (never written by code)
    input/DAILY-DATA/  ← Manually updated daily OHLCV
    output/            ← Model artefacts + backtest results (API writes here)
  config/
    base.yaml / development.yaml / production.yaml
  alembic/             ← Migration scripts
  tests/unit/ integration/ e2e/
</pre>

<hr/>

<h2>API Inventory</h2>

<h3>System CRUD — <code>api/v1/system/</code></h3>
<table>
  <thead><tr><th>Endpoint</th><th>Method</th><th>Description</th></tr></thead>
  <tbody>
    <tr><td>/api/v1/positions</td><td>GET, POST, DELETE</td><td>Live positions table</td></tr>
    <tr><td>/api/v1/portfolio/positions</td><td>GET</td><td>Positions by mode (paper/live)</td></tr>
    <tr><td>/api/v1/portfolio/summary</td><td>GET</td><td>Portfolio KPIs + instrument prices</td></tr>
    <tr><td>/api/v1/portfolio/price-history</td><td>GET</td><td>OHLCV price history</td></tr>
    <tr><td>/api/v1/alerts</td><td>GET, POST, DELETE</td><td>Alerts table</td></tr>
    <tr><td>/api/v1/audit-log</td><td>GET</td><td>Audit trail</td></tr>
    <tr><td>/api/v1/market-signals</td><td>GET</td><td>Technical indicators (RSI, MACD, BB, ATR, EMA, trend)</td></tr>
    <tr><td>/api/v1/drift</td><td>GET</td><td>5-check drift detector status</td></tr>
    <tr><td>/api/v1/training-history</td><td>GET</td><td>Training run history (newest-first)</td></tr>
    <tr><td>/api/v1/trade-events</td><td>GET</td><td>Trade event log</td></tr>
    <tr><td>/api/v1/risk-timeline</td><td>GET</td><td>Daily portfolio + benchmark values</td></tr>
    <tr><td>/api/v1/performance-summary</td><td>GET</td><td>Aggregated KPIs (Sharpe, MDD, CAGR, win rate)</td></tr>
    <tr><td>/api/v1/metrics/summary</td><td>GET</td><td>Structured Prometheus metrics summary</td></tr>
    <tr><td>/api/v1/test-results</td><td>GET</td><td>JUnit XML test result summary</td></tr>
    <tr><td>/api/v1/users</td><td>GET, POST, DELETE</td><td>User management (admin-gated)</td></tr>
  </tbody>
</table>

<h3>Workflow — <code>api/v1/workflow/</code></h3>
<table>
  <thead><tr><th>Endpoint</th><th>Method</th><th>Description</th></tr></thead>
  <tbody>
    <tr><td>/api/v1/train</td><td>POST</td><td>Launch RL training run (JWT required)</td></tr>
    <tr><td>/api/v1/backtest</td><td>POST</td><td>Launch backtest (JWT required)</td></tr>
    <tr><td>/api/v1/evaluate</td><td>POST</td><td>Evaluate latest model (JWT required)</td></tr>
    <tr><td>/api/v1/chat</td><td>POST</td><td>Chat query → classify → dispatch → response</td></tr>
    <tr><td>/api/v1/chat/warmup</td><td>POST</td><td>Pre-load sentence-transformer model</td></tr>
    <tr><td>/api/v1/goal</td><td>POST</td><td>Goal feasibility analysis</td></tr>
    <tr><td>/api/v1/market</td><td>POST</td><td>Run market analysis step</td></tr>
    <tr><td>/api/v1/strategy</td><td>POST</td><td>Run strategy step</td></tr>
    <tr><td>/api/v1/agent-panel/run-day</td><td>POST</td><td>Run one day of the LangGraph agent simulation</td></tr>
  </tbody>
</table>

<h3>Experience Layer — <code>api/experience/</code></h3>
<table>
  <thead><tr><th>Endpoint</th><th>Method</th><th>Description</th></tr></thead>
  <tbody>
    <tr><td>/api/experience/rita</td><td>GET</td><td>RITA dashboard composite payload</td></tr>
    <tr><td>/api/experience/fno</td><td>GET</td><td>FnO dashboard composite payload</td></tr>
    <tr><td>/api/experience/ops</td><td>GET</td><td>Ops dashboard composite payload</td></tr>
    <tr><td>/api/experience/ds</td><td>GET</td><td>Data science panel payload</td></tr>
    <tr><td>/api/experience/greeks</td><td>GET</td><td>Aggregated Greeks across open positions</td></tr>
  </tbody>
</table>

<hr/>

<h2>Slash Command Reference</h2>
<p>All commands live in <code>.claude/commands/</code>. Invoke with <code>/command-name task description</code>.</p>
<table>
  <thead><tr><th>Command</th><th>Use for</th></tr></thead>
  <tbody>
    <tr><td><code>/start-day</code></td><td>Read PLAN_STATUS.md and get today's tasks</td></tr>
    <tr><td><code>/end-day</code></td><td>Update PLAN_STATUS + roadmap + Confluence + git commit</td></tr>
    <tr><td><code>/fix-bug</code></td><td>Diagnose and fix a JS frontend bug (no server start)</td></tr>
    <tr><td><code>/add-endpoint</code></td><td>Add or modify a FastAPI route (tier placement, repo/service scaffolding)</td></tr>
    <tr><td><code>/add-db-model</code></td><td>Add ORM model + repository + schema + Alembic migration</td></tr>
    <tr><td><code>/add-chat-intent</code></td><td>Add a new classifier intent (seed phrases + handler)</td></tr>
    <tr><td><code>/add-rita-feature</code></td><td>Add section/card/chart to RITA dashboard</td></tr>
    <tr><td><code>/add-fno-feature</code></td><td>Add section/card to FnO dashboard</td></tr>
    <tr><td><code>/add-ops-feature</code></td><td>Add section/card to Ops dashboard</td></tr>
    <tr><td><code>/add-data-feature</code></td><td>Add data field, analysis function, or ML model</td></tr>
    <tr><td><code>/add-mobile-feature</code></td><td>Add screen or feature to the Mobile PWA</td></tr>
    <tr><td><code>/engineer-task</code></td><td>General engineer task (routes to the right specialist command)</td></tr>
  </tbody>
</table>
<p>See <code>.claude/commands/EXAMPLES.md</code> for copy-paste invocation examples for each command.</p>

<hr/>

<h2>Key Spec Files</h2>
<table>
  <thead><tr><th>Spec</th><th>Read when…</th></tr></thead>
  <tbody>
    <tr><td>Spec_Python_Code.md</td><td>Writing any Python — architecture rules, API table, service/repo patterns</td></tr>
    <tr><td>Spec_JS_Code.md</td><td>Writing any JS — module maps for rita/fno/ops, section loader pattern, chart pattern, gotchas</td></tr>
    <tr><td>Spec_DB.md</td><td>DB tables, migration commands, seeding rules</td></tr>
    <tr><td>Spec_Data.md</td><td>Data file locations, load_nifty_csv(), output paths</td></tr>
    <tr><td>Spec_Chat_Feature.md</td><td>Chat pipeline, 20 existing intents, classifier architecture</td></tr>
    <tr><td>Spec_RITA_App.md</td><td>General app overview, full API inventory, agent panel flow</td></tr>
    <tr><td>Spec_Mobile_App.md</td><td>Mobile PWA screens, fetch pattern, design tokens, touch rules</td></tr>
    <tr><td>Spec_HTML_Code.md</td><td>HTML structure for all three dashboards</td></tr>
  </tbody>
</table>

<hr/>

<h2>Development Workflow</h2>
<pre>
# From riia-jun-release/

# 1. Start the app
python start.py

# 2. Run database migrations
alembic upgrade head

# 3. Run tests
pytest tests/unit tests/integration
pytest tests/e2e  # requires uvicorn running on :8765

# 4. Lint
ruff check src/

# 5. Configuration
# Edit config/development.yaml
# JWT secret via env var: set RITA_JWT_SECRET=your-secret
</pre>
"""

# ─────────────────────────────────────────────────────────────────────────────
# 2d. OPERATIONS
# ─────────────────────────────────────────────────────────────────────────────

OPERATIONS_HTML = """
<h1>Operations</h1>
<p><strong>Version:</strong> v1.0 &nbsp;|&nbsp; <strong>Date:</strong> 2026-04-29</p>
<p>How to run, configure, monitor, and troubleshoot the RITA application.</p>

<hr/>

<h2>Starting the Application</h2>
<pre>
# From riia-jun-release/

# Run migrations (required after first install or model changes)
alembic upgrade head

# Start the API server
python start.py
# OR
uvicorn rita.main:app --host 0.0.0.0 --port 8000 --reload

# Open dashboards in browser
# RITA:  http://localhost:8000/dashboard/index.html
# FnO:   http://localhost:8000/dashboard/fno.html
# Ops:   http://localhost:8000/dashboard/ops.html
</pre>

<h3>Docker</h3>
<pre>
docker build -t rita:latest .
docker run -p 8000:8000 -e RITA_JWT_SECRET=your-secret rita:latest
</pre>

<hr/>

<h2>Configuration</h2>
<p>Configuration is layered — <code>base.yaml</code> sets defaults, environment files override.</p>
<table>
  <thead><tr><th>File</th><th>Use</th></tr></thead>
  <tbody>
    <tr><td><code>config/base.yaml</code></td><td>Shared defaults for all environments</td></tr>
    <tr><td><code>config/development.yaml</code></td><td>Local development overrides (debug logging, loose CORS)</td></tr>
    <tr><td><code>config/production.yaml</code></td><td>Production settings (strict CORS, production log level)</td></tr>
  </tbody>
</table>

<h3>Key Configuration Values</h3>
<table>
  <thead><tr><th>Setting</th><th>Where</th><th>Notes</th></tr></thead>
  <tbody>
    <tr><td><code>RITA_JWT_SECRET</code></td><td>Environment variable</td><td>Never in YAML. Required for workflow routes.</td></tr>
    <tr><td><code>database_url</code></td><td>base.yaml</td><td><code>sqlite:///data/output/rita.db</code> — change to PostgreSQL URL for v2</td></tr>
    <tr><td><code>security.cors_origins</code></td><td>base.yaml</td><td>List of allowed origins for CORS</td></tr>
    <tr><td><code>instruments.nifty.lot_size</code></td><td>base.yaml</td><td>75 — never hardcode in code</td></tr>
    <tr><td><code>instruments.banknifty.lot_size</code></td><td>base.yaml</td><td>30 — never hardcode in code</td></tr>
    <tr><td><code>app.environment</code></td><td>env yaml</td><td><code>development</code> | <code>production</code></td></tr>
  </tbody>
</table>

<hr/>

<h2>Health Probes</h2>
<table>
  <thead><tr><th>Endpoint</th><th>Type</th><th>What it checks</th><th>Failure response</th></tr></thead>
  <tbody>
    <tr><td><code>GET /health</code></td><td>Liveness</td><td>Model exists on disk, CSV loaded, data freshness, last pipeline run</td><td>200 with degraded status fields</td></tr>
    <tr><td><code>GET /readyz</code></td><td>Readiness</td><td>DB <code>SELECT 1</code></td><td>503 if DB unreachable</td></tr>
    <tr><td><code>GET /metrics</code></td><td>Prometheus</td><td>Request counts, latency histograms, error rate</td><td>—</td></tr>
  </tbody>
</table>

<hr/>

<h2>Data Management</h2>

<h3>Daily OHLCV Update (after each trading day)</h3>
<pre>
# Append the new day's row to nifty_manual.csv
# Format: dd-MMM-yyyy,open,high,low,close,shares_traded,turnover
# Example:
# 29-APR-2026,22450.0,22680.0,22310.0,22580.0,234567890,18234.56

# File location:
# riia-jun-release/data/input/DAILY-DATA/nifty_manual.csv

# After appending — restart the app to re-seed the DB with the new row
# OR run a direct DB insert if you don't want to restart
</pre>

<h3>Data Directory Rules</h3>
<table>
  <thead><tr><th>Directory</th><th>Rule</th></tr></thead>
  <tbody>
    <tr><td><code>data/raw/</code></td><td>Immutable — never write from code. Ground truth source of 25-year history.</td></tr>
    <tr><td><code>data/input/DAILY-DATA/</code></td><td>Manually updated. nifty_manual.csv and banknifty_manual.csv appended daily.</td></tr>
    <tr><td><code>data/output/</code></td><td>Written by API only. Model .zip files, backtest_results.csv, performance_summary.json.</td></tr>
  </tbody>
</table>

<h3>DB Backup</h3>
<pre>
# Before any schema change or destructive operation
cp data/output/rita.db data/output/rita.db.bak-$(date +%Y%m%d-%H%M)
</pre>

<hr/>

<h2>Monitoring</h2>

<h3>Ops Dashboard</h3>
<p>Open <code>http://localhost:8000/dashboard/ops.html</code> for:</p>
<ul>
  <li>System health KPIs (model age, data freshness, last pipeline run)</li>
  <li>Prometheus metrics (request count, latency, error rate)</li>
  <li>Test result summary (unit / integration / e2e pass rates)</li>
  <li>Drift detector status (5 checks)</li>
  <li>CI/CD pipeline status</li>
</ul>

<h3>Structured Logs</h3>
<p>All logs are JSON via structlog. Key fields: <code>event</code>, <code>trace_id</code>, <code>level</code>, <code>timestamp</code>.</p>
<pre>
# Filter errors
uvicorn rita.main:app 2>&amp;1 | python -c "import sys,json; [print(l) for l in sys.stdin if 'error' in l.lower()]"
</pre>

<hr/>

<h2>Troubleshooting</h2>
<table>
  <thead><tr><th>Symptom</th><th>Likely Cause</th><th>Fix</th></tr></thead>
  <tbody>
    <tr><td>All KPIs show <code>—</code> on RITA dashboard</td><td>API not running or RITA_API_BASE wrong</td><td>Check <code>window.RITA_API_BASE</code> in rita.html; confirm uvicorn is running on the expected port</td></tr>
    <tr><td><code>GET /health</code> returns <code>model_exists: false</code></td><td>No model trained yet</td><td>Run <code>POST /api/v1/train</code> (requires JWT) or copy a model .zip to <code>data/output/NIFTY/</code></td></tr>
    <tr><td><code>GET /readyz</code> returns 503</td><td>DB file missing or locked</td><td>Run <code>alembic upgrade head</code>; check for stale .db-shm / .db-wal lock files</td></tr>
    <tr><td>Market Signals all blank</td><td>DB not seeded or nifty_manual.csv empty</td><td>Restart app to re-trigger lifespan seeding; confirm <code>data/input/DAILY-DATA/nifty_manual.csv</code> has rows</td></tr>
    <tr><td>Auth 401 on workflow routes</td><td>Missing or expired JWT</td><td>POST to <code>/auth/token</code> to get a fresh token; check <code>RITA_JWT_SECRET</code> env var is set</td></tr>
    <tr><td>Training runs hang at "pending"</td><td>Background thread crashed silently</td><td>Check structlog for <code>"training failed"</code> events with the run_id; common cause: model file path issue</td></tr>
    <tr><td>Alembic migration fails</td><td>Model import missing in env.py</td><td>Add missing <code>from rita.models.x import X</code> to <code>alembic/env.py</code></td></tr>
  </tbody>
</table>

<hr/>

<h2>Infrastructure</h2>
<table>
  <thead><tr><th>Artefact</th><th>Location</th><th>Notes</th></tr></thead>
  <tbody>
    <tr><td>Dockerfile</td><td><code>riia-jun-release/Dockerfile</code></td><td>Multi-stage (builder: lint+test, runtime: non-root user)</td></tr>
    <tr><td>Docker Compose</td><td><code>riia-jun-release/docker-compose.yml</code></td><td>Local stack with volume mounts for data/</td></tr>
    <tr><td>k8s Deployment</td><td><code>riia-jun-release/k8s/deployment.yaml</code></td><td>Liveness and readiness probes configured</td></tr>
    <tr><td>k8s Service</td><td><code>riia-jun-release/k8s/service.yaml</code></td><td>ClusterIP — expose via Ingress</td></tr>
    <tr><td>Terraform</td><td><code>riia-jun-release/terraform/</code></td><td>Scaffolding for cloud provider swap (Sprint 5)</td></tr>
    <tr><td>CI Pipeline</td><td><code>.github/workflows/ci.yml</code></td><td>lint → test → alembic upgrade → e2e → docker build</td></tr>
  </tbody>
</table>
"""

# ─────────────────────────────────────────────────────────────────────────────
# PUBLISH
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("Publishing RIIA App product section + Project Summary")
    print("=" * 60)

    # 1. Project Summary (sibling of existing sections, under homepage)
    print("\n[1/6] Project Summary")
    publish("Project Summary", PROJECT_SUMMARY_HTML, HOMEPAGE_ID)

    # 2. RIIA App root (product section, under homepage)
    print("[2/6] RIIA App (product section root)")
    riia_app_id = publish("RIIA App", RIIA_APP_HTML, HOMEPAGE_ID)

    # 3-6. Child pages under RIIA App
    print("[3/6] Requirements")
    publish("Requirements", REQUIREMENTS_HTML, riia_app_id)

    print("[4/6] Architecture")
    publish("Architecture", ARCHITECTURE_HTML, riia_app_id)

    print("[5/6] Engineering")
    publish("Engineering", ENGINEERING_HTML, riia_app_id)

    print("[6/6] App Operations")
    publish("App Operations", OPERATIONS_HTML, riia_app_id)

    print("\n" + "=" * 60)
    print("Done. 6 pages published.")
    print("=" * 60)
