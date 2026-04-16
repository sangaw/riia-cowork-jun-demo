"""
Publishes (or updates) the Sprint 5 board page under Sprint Boards in Confluence.
Run at end of each Sprint 5 day to reflect progress.

First run:  PAGE_ID = None  → creates the page, prints the ID → paste it below
Subsequent: PAGE_ID = "..."  → updates the existing page in-place
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from confluence.publish import ConfluenceClient, SECTION

TITLE = "Sprint 5 — Integration, Security & Release"

# After first run, paste the returned page ID here so subsequent runs update in-place.
PAGE_ID = "68878337"

BODY = """
<h1>Sprint 5 &mdash; Integration, Security &amp; Release</h1>
<p><strong>Duration:</strong> Days 31&ndash;34 &nbsp;|&nbsp; <strong>Theme:</strong> Full regression testing, security hardening, Terraform + k8s production deployment, RITA v1.0 release tag</p>

<table>
  <thead>
    <tr>
      <th>Day</th>
      <th>Role</th>
      <th>Task</th>
      <th>Status</th>
      <th>Notes</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Day 31</td>
      <td>QA</td>
      <td>Full end-to-end regression + coverage report</td>
      <td><strong style="color:#92480a">&#9670; Partial</strong></td>
      <td>Functional scenario tests created for RITA/FnO/Ops (48 tests total). TEST menu added to ops.html. /api/v1/test-results endpoint reads JUnit XML. RITA suite: 3/20 pass (9 missing endpoints, 8 timeouts). FnO + Ops suites pending. Coverage &#8805;80% already enforced in CI.</td>
    </tr>
    <tr>
      <td>Day 32</td>
      <td>Security</td>
      <td>CORS, JWT, rate limiting, input validation</td>
      <td><strong style="color:#1a6b3c">&#10003; Done</strong></td>
      <td>CORSMiddleware from settings.security.cors_origins. POST /auth/token (python-jose JWT, HS256). get_current_user dependency on workflow routers (train/backtest/evaluate). slowapi: 60/min global, 10/min on /auth/token. Field constraints (max_length, ge=0, pattern) on 9 schemas. 8/8 new tests; 128/129 total (1 pre-existing config test failure).</td>
    </tr>
    <tr>
      <td>Day 33</td>
      <td>Ops</td>
      <td>Terraform: k8s manifests, AlertManager, cloud provider swap</td>
      <td><strong style="color:#1a6b3c">&#10003; Done</strong></td>
      <td>k8s/deployment.yaml, k8s/service.yaml, k8s/ingress.yaml, docker-compose.yml, and terraform/ scaffolding delivered via external AI agent. Files committed to repo.</td>
    </tr>
    <tr>
      <td>Day 34</td>
      <td>PM + TechWriter</td>
      <td>Release checklist, v1.0 tag, release notes</td>
      <td><strong style="color:#92480a">&#9670; Deferred</strong></td>
      <td>Deferred pending end-to-end application testing. Will run after all defects identified during testing are resolved.</td>
    </tr>
  </tbody>
</table>

<h2>Day 32 Deliverables &mdash; Security Hardening</h2>

<h3>New Files</h3>
<table>
  <thead><tr><th>File</th><th>Purpose</th></tr></thead>
  <tbody>
    <tr><td><code>src/rita/auth.py</code></td><td>JWT utilities: <code>create_access_token()</code> and <code>get_current_user()</code> FastAPI dependency using <code>python-jose</code>.</td></tr>
    <tr><td><code>src/rita/limiter.py</code></td><td>Shared <code>slowapi.Limiter</code> instance (avoids circular imports between main.py and auth router).</td></tr>
    <tr><td><code>src/rita/api/v1/auth.py</code></td><td><code>POST /auth/token</code> login endpoint. Returns signed JWT. Rate-limited to 10 requests/minute per IP.</td></tr>
    <tr><td><code>tests/unit/test_auth.py</code></td><td>3 JWT unit tests: create/decode, expired token, invalid token.</td></tr>
    <tr><td><code>tests/integration/test_security.py</code></td><td>5 integration tests: CORS preflight, unauthenticated workflow (401), wrong password (401), login returns token, authenticated workflow (200).</td></tr>
  </tbody>
</table>

<h3>Modified Files</h3>
<table>
  <thead><tr><th>File</th><th>Change</th></tr></thead>
  <tbody>
    <tr><td><code>src/rita/config.py</code></td><td>Added <code>jwt_algorithm: str = "HS256"</code> and <code>jwt_expiry_minutes: int = 60</code> to <code>SecuritySettings</code>.</td></tr>
    <tr><td><code>src/rita/main.py</code></td><td>Added <code>CORSMiddleware</code> (outermost, reads from settings). Added slowapi rate limit exception handler. Auth router included. Workflow routers (train/backtest/evaluate) now require <code>Depends(get_current_user)</code>.</td></tr>
    <tr><td><code>src/rita/middleware.py</code></td><td>Fixed pre-existing bug: <code>response</code> unbound in finally block when <code>call_next</code> raises before returning.</td></tr>
    <tr><td><code>pyproject.toml</code></td><td>Added <code>slowapi&gt;=0.1.9</code> dependency.</td></tr>
    <tr><td>9 schema files</td><td>Added <code>Field(max_length=...)</code> and <code>Field(ge=0)</code> constraints to free-text and quantity/price fields in positions, orders, trades, alerts, audit, training, backtest, manoeuvres, config_overrides schemas.</td></tr>
  </tbody>
</table>

<h3>Security Architecture</h3>
<table>
  <thead><tr><th>Layer</th><th>Mechanism</th><th>Config</th></tr></thead>
  <tbody>
    <tr><td>CORS</td><td><code>CORSMiddleware</code></td><td><code>settings.security.cors_origins</code> (default: localhost:8000; override via <code>RITA_CORS_ORIGINS</code>)</td></tr>
    <tr><td>Authentication</td><td>JWT Bearer token (HS256, 60-min expiry)</td><td>Secret from <code>RITA_JWT_SECRET</code> env var (min 32 chars in staging/prod)</td></tr>
    <tr><td>Rate limiting</td><td><code>slowapi</code> per-IP</td><td>60 req/min global; 10 req/min on <code>POST /auth/token</code></td></tr>
    <tr><td>Input validation</td><td>Pydantic field constraints</td><td>max_length on strings; ge=0 on quantities/prices; pattern on symbol fields</td></tr>
    <tr><td>Protected routes</td><td><code>Depends(get_current_user)</code></td><td>Workflow tier only (train/backtest/evaluate). System CRUD + Experience routers open for v1 dashboard access.</td></tr>
  </tbody>
</table>

<h3>Test Results</h3>
<table>
  <thead><tr><th>Suite</th><th>Pass</th><th>Fail</th><th>Note</th></tr></thead>
  <tbody>
    <tr><td>Unit (all)</td><td>98</td><td>1</td><td>Pre-existing: test_jwt_secret_from_env_var (pydantic-settings validation_alias + env_prefix conflict)</td></tr>
    <tr><td>Integration (all)</td><td>30</td><td>0</td><td>Includes 5 new security tests</td></tr>
    <tr><td><strong>Total</strong></td><td><strong>128</strong></td><td><strong>1</strong></td><td>1 pre-existing failure, not introduced by Day 32</td></tr>
  </tbody>
</table>

<h2>Day 31 Deliverables &mdash; Regression &amp; TEST Dashboard (Partial)</h2>
<ul>
  <li>48 functional scenario tests authored (RITA: 20, FnO: 14, Ops: 14)</li>
  <li><code>GET /api/v1/test-results</code> endpoint reads JUnit XML and returns structured JSON</li>
  <li>TEST section added to ops.html navigation (<code>nav.js</code> updated)</li>
  <li>Suite cards display pass counts; defects table shows failures with messages</li>
  <li>RITA suite result: 3/20 pass (9 endpoints not yet implemented, 8 timeout on background jobs)</li>
  <li>FnO and Ops suites pending full run</li>
</ul>

<h2>Sprint 5 Definition of Done</h2>
<ul>
  <li>&#9670; Full scenario test suite &mdash; all 3 dashboards (Day 31, partial)</li>
  <li>&#10003; Security hardening &mdash; CORS, JWT, rate limiting, input validation (Day 32)</li>
  <li>&#10003; Terraform + k8s manifests + docker-compose (Day 33, done via external agent)</li>
  <li>&#9670; CHANGELOG.md, git tag v1.0, release notes, PM retrospective (Day 34, deferred pending testing)</li>
</ul>
"""


if __name__ == "__main__":
    client = ConfluenceClient()

    if PAGE_ID:
        page_id, url = client.update_page(PAGE_ID, TITLE, BODY)
        print(f"Sprint 5 board updated: {url}")
    else:
        page_id, url = client.create_page(TITLE, BODY, parent_id=SECTION["sprint_boards"])
        print(f"Sprint 5 board created: {url}")
        print(f"Page ID: {page_id}")
        print(f"\nPaste this into PAGE_ID at the top of this script for future updates:")
        print(f'PAGE_ID = "{page_id}"')
