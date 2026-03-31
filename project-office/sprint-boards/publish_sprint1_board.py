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
      <td>Pending</td>
      <td></td>
    </tr>
    <tr>
      <td>Day 6</td>
      <td>Ops</td>
      <td>Multi-stage Dockerfile, CI v2 pipeline</td>
      <td>Pending</td>
      <td></td>
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

<h2>Sprint 1 Definition of Done</h2>
<ul>
  <li>&#10003; Config crashes at boot on missing secrets in staging/production</li>
  <li>&#9744; 12+ repository classes with file locking (Day 5)</li>
  <li>&#9744; CI green with coverage gate &ge;80% (Day 6)</li>
  <li>&#9744; Tests for config edge cases and repo round-trips pass (Day 7)</li>
  <li>&#9744; Confluence Security &amp; Config pages published (Day 8)</li>
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
