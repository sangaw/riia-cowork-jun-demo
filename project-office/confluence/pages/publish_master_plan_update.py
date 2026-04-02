"""
Day 14 — Update Master Plan overview page on Confluence to reflect current status.

Sprint 0, 1, 2 complete. Sprint 3 is next.

Run from project root:
    CONFLUENCE_EMAIL=contact@ravionics.nl python project-office/confluence/pages/publish_master_plan_update.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from confluence.publish import ConfluenceClient, SECTION

PAGE_ID = "65110386"
PAGE_TITLE = "RITA Production Refactor -- Master Plan"

PAGE_BODY = """
<h1>RITA Production Refactor &mdash; Master Plan</h1>
<p><strong>Version:</strong> 2.0 &nbsp;|&nbsp; <strong>Last updated:</strong> 2026-04-02 &nbsp;|&nbsp; <strong>Owner:</strong> Project Team</p>
<p style="background:#e8f4fd;border-left:4px solid #2196F3;padding:12px;">
<strong>Project Goal:</strong> Refactor RITA (Risk Informed Trading Approach) from a working POC into a production-grade, cloud-native, secure and maintainable system &mdash; using a Claude Cowork multi-agent team executing daily sprint cycles.
</p>

<p style="background:#e8f5e9;border-left:4px solid #4CAF50;padding:12px;">
<strong>Current Status (Day 14 of 30):</strong> Sprint 2 complete. Sprints 0, 1, and 2 all done.
Three-tier API fully decomposed and contract-tested. Sprint 3 (Service Layer &amp; Observability) starts next.
</p>

<h2>Project Repositories &amp; References</h2>
<table>
  <tbody>
    <tr><th>Item</th><th>Location</th></tr>
    <tr><td>POC Source</td><td><code>rita-cowork-demo/</code></td></tr>
    <tr><td>Production Target</td><td><code>riia-cowork-jun/</code></td></tr>
    <tr><td>Assessment Doc</td><td><code>production_ready.md</code> (v2.0, 1908 lines, 29-Mar-2026)</td></tr>
    <tr><td>Daily Status</td><td><code>PLAN_STATUS.md</code> (updated each session)</td></tr>
    <tr><td>Confluence Space</td><td>RIIA-Project-Refactor (this space)</td></tr>
  </tbody>
</table>

<h2>Team &mdash; Claude Cowork Agent Roles</h2>
<table>
  <tbody>
    <tr><th>Role</th><th>Agent Type</th><th>Responsibility</th></tr>
    <tr>
      <td><strong>Project Manager</strong></td>
      <td>general-purpose</td>
      <td>Sprint planning, daily work breakdown, risk tracking, status updates, dependency management</td>
    </tr>
    <tr>
      <td><strong>Architect</strong></td>
      <td>Plan agent</td>
      <td>Target folder structure, ADRs, API tier contracts, Pydantic schemas, dependency injection design</td>
    </tr>
    <tr>
      <td><strong>Design &amp; Code Reviewer</strong></td>
      <td>general-purpose</td>
      <td>Reviews designs before implementation; reviews diffs after engineering; checks ADR compliance, security patterns, coding standards; approves or requests changes</td>
    </tr>
    <tr>
      <td><strong>Engineer (x N)</strong></td>
      <td>general-purpose, isolated worktrees</td>
      <td>Code implementation split by domain: Config/Security, Data Layer, API tiers, Services, Observability, Frontend</td>
    </tr>
    <tr>
      <td><strong>QA Tester</strong></td>
      <td>general-purpose</td>
      <td>Unit tests, integration tests, e2e tests (Playwright), coverage reports, regression suites</td>
    </tr>
    <tr>
      <td><strong>Ops Engineer</strong></td>
      <td>general-purpose</td>
      <td>Multi-stage Dockerfile, GitHub Actions CI/CD pipeline, Kubernetes manifests, secrets config, canary rollout</td>
    </tr>
    <tr>
      <td><strong>Technical Writer</strong></td>
      <td>general-purpose</td>
      <td>Authors sprint documentation and publishes all 14 Confluence pages (ADRs, API reference, runbooks, release notes)</td>
    </tr>
  </tbody>
</table>

<h2>Sprint Roadmap</h2>
<table>
  <tbody>
    <tr><th>Sprint</th><th>Name</th><th>Work Days</th><th>Key Deliverables</th><th>Status</th></tr>
    <tr>
      <td><strong>Sprint 0</strong></td>
      <td>Architecture &amp; Planning</td>
      <td>Days 1–3</td>
      <td>Target folder structure, ADR-001 (API tiers) &amp; ADR-002 (Repository pattern), Pydantic schemas for 15 CSV tables, Confluence bootstrapped</td>
      <td><strong style="color:#1a6b3c">&#10003; Done</strong></td>
    </tr>
    <tr>
      <td><strong>Sprint 1</strong></td>
      <td>Foundation</td>
      <td>Days 4–8</td>
      <td>Pydantic config + YAML hierarchy, repository layer (15 CSV tables), multi-stage Dockerfile, CI v2 with 80% coverage gate, config and repository tests (19 tests)</td>
      <td><strong style="color:#1a6b3c">&#10003; Done</strong></td>
    </tr>
    <tr>
      <td><strong>Sprint 2</strong></td>
      <td>API Decomposition</td>
      <td>Days 9–14</td>
      <td>Three-tier API routers (8 system + 3 workflow + 3 experience), global exception handler, trace IDs, 78 API contract tests, Confluence API Reference</td>
      <td><strong style="color:#1a6b3c">&#10003; Done</strong></td>
    </tr>
    <tr>
      <td><strong>Sprint 3</strong></td>
      <td>Service Layer &amp; Observability</td>
      <td>Days 15–20</td>
      <td>WorkflowService, ManoeuvreService, PortfolioService, structlog JSON logging, Prometheus metrics, /health and /readyz endpoints</td>
      <td><strong style="color:#e65100">&#9654; Up Next</strong></td>
    </tr>
    <tr>
      <td><strong>Sprint 4</strong></td>
      <td>Frontend &amp; Responsive Design</td>
      <td>Days 21–26</td>
      <td>ES module decomposition of all 3 HTML apps, responsive CSS, Playwright e2e tests</td>
      <td>Planned</td>
    </tr>
    <tr>
      <td><strong>Sprint 5</strong></td>
      <td>Integration, Security &amp; Release</td>
      <td>Days 27–30</td>
      <td>Full regression suite, security audit (CORS, JWT, rate limiting), Terraform k8s manifests, canary rollout, Release v1.0 notes</td>
      <td>Planned</td>
    </tr>
  </tbody>
</table>

<h2>Progress Summary</h2>
<table>
  <tbody>
    <tr><th>Milestone</th><th>Target</th><th>Actual</th><th>Status</th></tr>
    <tr><td>Folder structure + ADRs</td><td>Day 1</td><td>Day 1</td><td><strong style="color:#1a6b3c">&#10003; Done</strong></td></tr>
    <tr><td>16 Pydantic schemas</td><td>Day 2</td><td>Day 2</td><td><strong style="color:#1a6b3c">&#10003; Done</strong></td></tr>
    <tr><td>Confluence bootstrapped</td><td>Day 3</td><td>Day 3</td><td><strong style="color:#1a6b3c">&#10003; Done</strong></td></tr>
    <tr><td>Pydantic Settings + YAML config</td><td>Day 4</td><td>Day 4</td><td><strong style="color:#1a6b3c">&#10003; Done</strong></td></tr>
    <tr><td>Repository layer (15 CSV tables)</td><td>Day 5</td><td>Day 5</td><td><strong style="color:#1a6b3c">&#10003; Done</strong></td></tr>
    <tr><td>Multi-stage Dockerfile + CI v2</td><td>Day 6</td><td>Day 6</td><td><strong style="color:#1a6b3c">&#10003; Done</strong></td></tr>
    <tr><td>Config + repository tests (19 tests)</td><td>Day 7</td><td>Day 7</td><td><strong style="color:#1a6b3c">&#10003; Done</strong></td></tr>
    <tr><td>Confluence: Config Guide + Security page</td><td>Day 8</td><td>Day 8</td><td><strong style="color:#1a6b3c">&#10003; Done</strong></td></tr>
    <tr><td>8 System CRUD routers</td><td>Day 9</td><td>Day 9</td><td><strong style="color:#1a6b3c">&#10003; Done</strong></td></tr>
    <tr><td>3 Workflow routers (train/backtest/evaluate)</td><td>Day 10</td><td>Day 10</td><td><strong style="color:#1a6b3c">&#10003; Done</strong></td></tr>
    <tr><td>3 Experience Layer BFF routers</td><td>Day 11</td><td>Day 11</td><td><strong style="color:#1a6b3c">&#10003; Done</strong></td></tr>
    <tr><td>Global exception handler + trace IDs</td><td>Day 12</td><td>Day 12</td><td><strong style="color:#1a6b3c">&#10003; Done</strong></td></tr>
    <tr><td>78 API contract tests (100% pass)</td><td>Day 13</td><td>Day 13</td><td><strong style="color:#1a6b3c">&#10003; Done</strong></td></tr>
    <tr><td>Confluence API Reference published</td><td>Day 14</td><td>Day 14</td><td><strong style="color:#1a6b3c">&#10003; Done</strong></td></tr>
    <tr><td>WorkflowService + BacktestService</td><td>Day 15</td><td>&mdash;</td><td>Next</td></tr>
    <tr><td>ManoeuvreService + PortfolioService</td><td>Day 16</td><td>&mdash;</td><td>Planned</td></tr>
    <tr><td>structlog JSON logging</td><td>Day 17</td><td>&mdash;</td><td>Planned</td></tr>
    <tr><td>Prometheus metrics + /health + /readyz</td><td>Day 18</td><td>&mdash;</td><td>Planned</td></tr>
    <tr><td>Greeks + manoeuvre + workflow integration tests</td><td>Day 19</td><td>&mdash;</td><td>Planned</td></tr>
    <tr><td>Confluence: Observability &amp; Runbook</td><td>Day 20</td><td>&mdash;</td><td>Planned</td></tr>
  </tbody>
</table>

<h2>Critical Issues Being Addressed</h2>
<p>Source: <code>production_ready.md</code> v2.0</p>
<table>
  <tbody>
    <tr><th>Priority</th><th>Issue</th><th>Current State</th><th>Target (v1)</th><th>Status</th></tr>
    <tr><td><strong>[P0]</strong></td><td>API Monolith</td><td>1,533-line rest_api.py</td><td>Three-tier: BFF / Business Process / System</td><td><strong style="color:#1a6b3c">&#10003; Sprint 2 Done</strong></td></tr>
    <tr><td><strong>[P0]</strong></td><td>Security</td><td>API key hardcoded, CORS wildcard, no JWT</td><td>JWT auth, restricted CORS, rate limiting</td><td>Sprint 5</td></tr>
    <tr><td><strong>[P0]</strong></td><td>Data Layer</td><td>Direct CSV I/O in route handlers</td><td>Repository pattern + service layer</td><td><strong style="color:#1a6b3c">&#10003; Sprint 1 Done</strong></td></tr>
    <tr><td><strong>[P0]</strong></td><td>Configuration</td><td>Raw os.getenv(), no validation</td><td>Pydantic Settings with field-level validation</td><td><strong style="color:#1a6b3c">&#10003; Sprint 1 Done</strong></td></tr>
    <tr><td><strong>[P0]</strong></td><td>Testing</td><td>&lt;5% coverage, no API tests</td><td>80% coverage, full test pyramid in CI</td><td>97 tests passing &mdash; Sprint 3 adds more</td></tr>
    <tr><td><strong>[P1]</strong></td><td>Error Handling</td><td>Silent NaN failures, no trace IDs</td><td>Structured errors, global handler, trace IDs</td><td><strong style="color:#1a6b3c">&#10003; Sprint 2 Done</strong></td></tr>
    <tr><td><strong>[P1]</strong></td><td>Observability</td><td>print() statements throughout</td><td>structlog JSON logging + Prometheus metrics</td><td>Sprint 3</td></tr>
    <tr><td><strong>[P1]</strong></td><td>Frontend</td><td>3 HTML files at 4,000+ lines each</td><td>ES modules, responsive design</td><td>Sprint 4</td></tr>
  </tbody>
</table>

<h2>Agent Workflow (How Roles Interact Each Sprint)</h2>
<pre>
PM Agent
  +--> Daily task list + risk updates
         |
         v
Architect Agent
  +--> ADRs + module contracts + Pydantic schemas
         |
         v
Design &amp; Code Reviewer
  +--> Approves design BEFORE engineers start
         |
         +--> Engineer A (Config / Security)       [isolated worktree]
         +--> Engineer B (Data Layer / Repos)      [isolated worktree]
         +--> Ops (Dockerfile + CI/CD)             [isolated worktree]
         |
         v
Design &amp; Code Reviewer
  +--> Reviews diffs, approves or requests changes
         |
         v
QA Agent
  +--> Tests written and passing, coverage report
         |
         v
Technical Writer
  +--> Confluence pages published
         |
         v
  (repeat per sprint)
</pre>

<h2>Risk Register</h2>
<table>
  <tbody>
    <tr><th>#</th><th>Risk</th><th>Likelihood</th><th>Impact</th><th>Mitigation</th><th>Status</th></tr>
    <tr><td>R1</td><td>Token budget exceeded mid-sprint on large file reads</td><td>High</td><td>Medium</td><td>Agents read scoped file sections only; pre-digested excerpts passed as context</td><td>Active &mdash; managed per session</td></tr>
    <tr><td>R2</td><td>Parallel engineers create merge conflicts</td><td>Medium</td><td>High</td><td>Worktree isolation per agent branch; merge only at end-of-day code review</td><td>No conflicts to date</td></tr>
    <tr><td>R3</td><td>Greeks calculation regression during refactor</td><td>Medium</td><td>Critical</td><td>QA writes Black-Scholes reference tests before engineers touch core/ modules</td><td>core/ not yet touched</td></tr>
    <tr><td>R4</td><td>CSV race conditions surface in production</td><td>Medium</td><td>High</td><td>Repository file locking implemented (Day 5)</td><td><strong style="color:#1a6b3c">&#10003; Mitigated</strong></td></tr>
    <tr><td>R5</td><td>Security gaps missed during API decomposition</td><td>Medium</td><td>Critical</td><td>Design &amp; Code Reviewer checks security patterns at every sprint boundary</td><td>Sprint 5 security audit scheduled</td></tr>
  </tbody>
</table>

<h2>Definition of Done (v1 Release)</h2>
<ul>
  <li><strong style="color:#1a6b3c">&#10003;</strong> All API endpoints in three-tier router structure (System / Business Process / BFF) &mdash; no monolith</li>
  <li><strong style="color:#1a6b3c">&#10003;</strong> All CSV access via repository classes &mdash; no direct file I/O in route handlers</li>
  <li><strong style="color:#1a6b3c">&#10003;</strong> Pydantic Settings validates config at startup; missing secrets crash at boot, not at runtime</li>
  <li>&#9744; Test coverage at or above 80% (unit + integration), enforced by CI gate</li>
  <li>&#9744; No hardcoded secrets, API keys, or localhost URLs in any code or HTML file</li>
  <li>&#9744; Structured JSON logs (structlog) throughout &mdash; zero print() statements</li>
  <li>&#9744; Prometheus metrics exported at /metrics; /health and /readyz endpoints live</li>
  <li>&#9744; All dashboard HTML decomposed into ES modules; responsive at 480/768/1100px</li>
  <li>&#9744; Kubernetes manifests valid and deployable with canary rollout strategy</li>
  <li>&#9744; All 14 Confluence documentation pages published and current</li>
  <li>&#9744; Design &amp; Code Reviewer sign-off recorded for each sprint</li>
</ul>
"""


if __name__ == "__main__":
    client = ConfluenceClient()
    pid, url = client.update_page(PAGE_ID, PAGE_TITLE, PAGE_BODY)
    print(f"Updated: {PAGE_TITLE}")
    print(f"  URL: {url}")
