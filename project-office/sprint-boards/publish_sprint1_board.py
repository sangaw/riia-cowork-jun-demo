"""
Publishes (or updates) the Sprint 1 board page under Sprint Boards in Confluence.
Run at end of each Sprint 1 day to reflect progress.

First run:  PAGE_ID = None  → creates the page, prints the ID → paste it below
Subsequent: PAGE_ID = "..."  → updates the existing page in-place
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from confluence.publish import ConfluenceClient, SECTION

TITLE = "Sprint 1 — Foundation"

# After first run, paste the returned page ID here so subsequent runs update in-place.
PAGE_ID = "65863682"

BODY = """
<h1>Sprint 1 &mdash; Foundation</h1>
<p><strong>Duration:</strong> Days 4&ndash;8 &nbsp;|&nbsp; <strong>Theme:</strong> Validated config, repository layer, and enforced CI gate</p>

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
      <td>Day 4</td>
      <td>Engineer A</td>
      <td>Pydantic Settings, config YAML hierarchy, remove hardcoded secrets</td>
      <td><strong style="color:#1a6b3c">&#10003; Done</strong></td>
      <td><code>src/rita/config.py</code> — Settings with YAML deep-merge, <code>RITA_ENV</code> selection, <code>RITA_JWT_SECRET</code> from env var only. Startup fails in staging/prod if secret absent or &lt;32 chars. <code>pyproject.toml</code> and <code>.env.example</code> added.</td>
    </tr>
    <tr>
      <td>Day 5</td>
      <td>Engineer B</td>
      <td>Repository layer — CSV tables, file locking, schema validation</td>
      <td><strong style="color:#1a6b3c">&#10003; Done</strong></td>
      <td><code>CsvRepository[T]</code> base with per-instance <code>threading.Lock</code>; Pydantic validation on every read and write; <code>upsert</code> and <code>delete</code> atomic under single lock acquisition. 15 concrete classes covering all CSV tables.</td>
    </tr>
    <tr>
      <td>Day 6</td>
      <td>Ops</td>
      <td>Multi-stage Dockerfile, CI v2 pipeline</td>
      <td><strong style="color:#1a6b3c">&#10003; Done</strong></td>
      <td>Multi-stage Dockerfile: <code>builder</code> runs lint + tests; <code>runtime</code> copies venv only, runs as non-root <code>rita</code> (uid 1000). CI: <code>lint</code> &rarr; <code>test</code> &rarr; <code>docker-build</code> on push/PR to main/master. <code>rita/main.py</code> entry point with <code>/health</code> endpoint added.</td>
    </tr>
    <tr>
      <td>Day 7</td>
      <td>QA</td>
      <td>Config + repository tests</td>
      <td>Pending</td>
      <td></td>
    </tr>
    <tr>
      <td>Day 8</td>
      <td>TechWriter</td>
      <td>Confluence: Security &amp; Config pages</td>
      <td>Pending</td>
      <td></td>
    </tr>
  </tbody>
</table>

<h2>Day 4 Deliverables &mdash; Config &amp; Security</h2>

<h3>Pydantic Settings (<code>src/rita/config.py</code>)</h3>
<ul>
  <li>Nested models: <code>AppSettings</code>, <code>ServerSettings</code>, <code>DataSettings</code>, <code>ModelSettings</code>, <code>InstrumentsSettings</code>, <code>SecuritySettings</code></li>
  <li>YAML loading: <code>base.yaml</code> loaded first, then environment-specific YAML deep-merged on top</li>
  <li>Environment selected via <code>RITA_ENV</code> env var (default: <code>development</code>)</li>
  <li>Module-level <code>settings</code> singleton + <code>get_settings()</code> with <code>@lru_cache</code> for FastAPI <code>Depends</code> injection</li>
</ul>

<h3>Secret Handling</h3>
<ul>
  <li><code>jwt_secret</code> sourced exclusively from <code>RITA_JWT_SECRET</code> env var — never from YAML</li>
  <li><code>jwt_secret</code> removed from <code>config/development.yaml</code></li>
  <li>Startup validator raises <code>ValueError</code> in <code>staging</code> / <code>production</code> if secret is absent or shorter than 32 characters</li>
</ul>

<h3>New Files</h3>
<ul>
  <li><code>riia-jun-release/pyproject.toml</code> — package definition, all runtime and dev dependencies (FastAPI, pydantic-settings, PyYAML, stable-baselines3, pytest, ruff)</li>
  <li><code>riia-jun-release/.env.example</code> — documents <code>RITA_ENV</code>, <code>RITA_JWT_SECRET</code>, optional port override</li>
</ul>

<h2>Day 5 Deliverables &mdash; Repository Layer</h2>

<h3><code>CsvRepository[T]</code> — Base Implementation</h3>
<ul>
  <li>Per-instance <code>threading.Lock</code> — all CSV reads and writes are lock-protected</li>
  <li><code>upsert</code> and <code>delete</code> each operate under a single lock acquisition using internal <code>_read_unlocked</code> / <code>_write_unlocked</code> helpers — no re-entrant locking</li>
  <li>Reads with <code>dtype=str</code> then validates every row via <code>model_validate()</code> — raises <code>RepositoryValidationError</code> on any bad row</li>
  <li>Writes re-validate before committing; creates parent directories if absent; writes empty CSV with headers when record list is empty</li>
  <li>Missing CSV file returns <code>[]</code> (not an error) — safe for first-run bootstrap</li>
</ul>

<h3>15 Concrete Repository Classes</h3>
<ul>
  <li><code>PositionsRepository</code>, <code>OrdersRepository</code>, <code>SnapshotsRepository</code>, <code>TradesRepository</code></li>
  <li><code>PortfolioRepository</code>, <code>ManoeuvresRepository</code></li>
  <li><code>BacktestRunsRepository</code>, <code>BacktestResultsRepository</code></li>
  <li><code>TrainingRunsRepository</code>, <code>TrainingMetricsRepository</code></li>
  <li><code>ModelRegistryRepository</code>, <code>AlertsRepository</code>, <code>AuditLogRepository</code></li>
  <li><code>MarketDataCacheRepository</code>, <code>ConfigOverridesRepository</code></li>
</ul>
<p>Each accepts an optional <code>data_dir: Path | None</code> for testability; defaults to <code>settings.data.output_dir</code>.</p>

<h2>Sprint 1 Definition of Done</h2>
<ul>
  <li>&#10003; Config crashes at boot on missing secrets in staging/production</li>
  <li>&#10003; 15 repository classes with file locking and schema validation</li>
  <li>&#10003; CI pipeline wired: lint &rarr; test &rarr; docker-build</li>
  <li>&#9744; Tests for config edge cases and repo round-trips pass (Day 7)</li>
  <li>&#9744; Confluence Security &amp; Config pages published (Day 8)</li>
</ul>

<h2>Day 6 Deliverables &mdash; Dockerfile &amp; CI v2</h2>

<h3>Multi-stage Dockerfile (<code>riia-jun-release/Dockerfile</code>)</h3>
<ul>
  <li><strong>builder stage:</strong> installs all deps into a venv, runs <code>ruff check src/</code> lint gate then <code>pytest</code> with coverage &mdash; build fails if either fails</li>
  <li><strong>runtime stage:</strong> copies only the pre-built venv and source, sets <code>PYTHONPATH</code>, runs as non-root user <code>rita</code> (uid 1000), exposes port 8000</li>
</ul>

<h3>GitHub Actions CI (<code>.github/workflows/ci.yml</code>)</h3>
<ul>
  <li><strong>lint</strong> &rarr; <strong>test</strong> &rarr; <strong>docker-build</strong> on push/PR to <code>main</code>/<code>master</code></li>
  <li>Coverage artifact uploaded; threshold at 0 for now &mdash; raised to 80 after Day 7 tests</li>
</ul>

<h3>App entry point (<code>src/rita/main.py</code>)</h3>
<ul>
  <li>Minimal FastAPI app with <code>GET /health</code> &mdash; title and version from <code>get_settings()</code></li>
</ul>
"""


if __name__ == "__main__":
    client = ConfluenceClient()

    if PAGE_ID:
        page_id, url = client.update_page(PAGE_ID, TITLE, BODY)
        print(f"Sprint 1 board updated: {url}")
    else:
        page_id, url = client.create_page(TITLE, BODY, parent_id=SECTION["sprint_boards"])
        print(f"Sprint 1 board created: {url}")
        print(f"Page ID: {page_id}")
        print(f"\nPaste this into PAGE_ID at the top of this script for future updates:")
        print(f'PAGE_ID = "{page_id}"')
