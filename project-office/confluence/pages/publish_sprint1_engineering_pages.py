"""
Day 8 — Publish Sprint 1 Engineering pages (Config Guide + Security) to Confluence.

Run from project root:
    CONFLUENCE_EMAIL=contact@ravionics.nl python project-office/confluence/pages/publish_sprint1_engineering_pages.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from confluence.publish import ConfluenceClient, SECTION

CONFIG_TITLE = "Sprint 1: Configuration Guide"
CONFIG_PAGE_ID = "65863699"

SECURITY_TITLE = "Sprint 1: Security — JWT & Secret Handling"
SECURITY_PAGE_ID = "65994769"

# ---------------------------------------------------------------------------
# Page 1 — Configuration Guide
# ---------------------------------------------------------------------------

CONFIG_BODY = """
<h1>Sprint 1: Configuration Guide</h1>

<p>
  This page documents how RITA loads and manages its configuration in production.
  Configuration is handled by <strong>Pydantic Settings v2</strong> with a two-layer
  YAML hierarchy, topped by environment-variable overrides for secrets.
</p>

<hr />

<h2>Overview</h2>
<p>
  RITA uses a layered configuration system:
</p>
<ol>
  <li><strong>base.yaml</strong> — environment-agnostic defaults loaded first.</li>
  <li><strong>{RITA_ENV}.yaml</strong> — environment-specific overrides deep-merged on top of base.</li>
  <li><strong>Environment variables</strong> — secrets and runtime overrides applied last (always win).</li>
</ol>
<p>
  The active environment is selected by the <code>RITA_ENV</code> environment variable,
  which defaults to <code>development</code> when unset.
</p>

<hr />

<h2>YAML Hierarchy</h2>
<table>
  <colgroup>
    <col style="width:25%" />
    <col style="width:15%" />
    <col style="width:60%" />
  </colgroup>
  <thead>
    <tr>
      <th>File</th>
      <th>Git-tracked</th>
      <th>Purpose</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>config/base.yaml</code></td>
      <td>Yes</td>
      <td>Safe defaults for all environments (no secrets).</td>
    </tr>
    <tr>
      <td><code>config/development.yaml</code></td>
      <td>Yes</td>
      <td>Development overrides: hot-reload, debug log level, loose CORS.</td>
    </tr>
    <tr>
      <td><code>config/staging.yaml</code></td>
      <td>No (.gitignore)</td>
      <td>Staging overrides. Never committed — injected at deploy time.</td>
    </tr>
    <tr>
      <td><code>config/production.yaml</code></td>
      <td>No (.gitignore)</td>
      <td>Production overrides. Never committed — injected at deploy time.</td>
    </tr>
  </tbody>
</table>

<p>
  Deep-merge semantics: nested keys from the environment YAML override only the
  keys they specify; the remainder of <code>base.yaml</code> is preserved untouched.
</p>

<p><strong>Example — development.yaml</strong> (only the changed keys are present):</p>
<pre>
server:
  reload: true
  log_level: "debug"

security:
  cors_origins: ["http://localhost:3000", "http://localhost:8000"]
</pre>

<hr />

<h2>Configuration Models</h2>
<p>
  All settings are declared as Pydantic <code>BaseSettings</code> sub-models
  under the root <code>Settings</code> class, located in
  <code>riia-jun-release/src/rita/config.py</code>.
</p>
<table>
  <colgroup>
    <col style="width:25%" />
    <col style="width:75%" />
  </colgroup>
  <thead>
    <tr>
      <th>Model</th>
      <th>Fields and defaults</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>AppSettings</code></td>
      <td><code>name="rita"</code>, <code>version="1.0.0"</code></td>
    </tr>
    <tr>
      <td><code>ServerSettings</code></td>
      <td><code>host="0.0.0.0"</code>, <code>port=8000</code>, <code>reload=False</code>, <code>log_level="info"</code></td>
    </tr>
    <tr>
      <td><code>DataSettings</code></td>
      <td><code>input_dir="rita_input"</code>, <code>output_dir="rita_output"</code></td>
    </tr>
    <tr>
      <td><code>ModelSettings</code></td>
      <td><code>path="rita_output/models"</code></td>
    </tr>
    <tr>
      <td><code>InstrumentsSettings</code></td>
      <td>Nests <code>InstrumentConfig</code> for each instrument (see lot sizes below).</td>
    </tr>
    <tr>
      <td><code>SecuritySettings</code></td>
      <td><code>jwt_secret</code> (SecretStr), <code>cors_origins</code></td>
    </tr>
  </tbody>
</table>

<hr />

<h2>Instrument Lot Sizes (Financial Constants)</h2>
<p>
  Lot sizes are configuration-driven and declared in <code>base.yaml</code>.
  They are <strong>never hardcoded</strong> in application or calculation code.
  Changing a lot size requires only a YAML update — no code change.
</p>
<table>
  <colgroup>
    <col style="width:30%" />
    <col style="width:20%" />
    <col style="width:50%" />
  </colgroup>
  <thead>
    <tr>
      <th>Instrument</th>
      <th>Lot size</th>
      <th>Notes</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>NIFTY 50</td>
      <td>75</td>
      <td>Updated from 50 in 2024 (NSE circular).</td>
    </tr>
    <tr>
      <td>BANKNIFTY</td>
      <td>30</td>
      <td>Current NSE lot size.</td>
    </tr>
  </tbody>
</table>
<p><strong>Access in code:</strong></p>
<pre>
from rita.config import settings
lot = settings.instruments.nifty.lot_size   # 75
</pre>

<hr />

<h2>Singleton and FastAPI Dependency Injection</h2>
<p>
  A module-level singleton is created once at import time:
</p>
<pre>
# config.py — module level
settings: Settings = Settings()
</pre>
<p>
  A cached accessor is provided for FastAPI dependency injection:
</p>
<pre>
from functools import lru_cache

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return settings
</pre>
<p>
  In route handlers, inject with:
</p>
<pre>
from fastapi import Depends
from rita.config import get_settings, Settings

@router.get("/info")
def info(cfg: Settings = Depends(get_settings)):
    return {"version": cfg.app.version}
</pre>

<hr />

<h2>Environment Variables Reference</h2>
<table>
  <colgroup>
    <col style="width:30%" />
    <col style="width:20%" />
    <col style="width:50%" />
  </colgroup>
  <thead>
    <tr>
      <th>Variable</th>
      <th>Required</th>
      <th>Description</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>RITA_ENV</code></td>
      <td>No (defaults to <code>development</code>)</td>
      <td>Selects the environment YAML overlay: <code>development</code>, <code>staging</code>, or <code>production</code>.</td>
    </tr>
    <tr>
      <td><code>RITA_JWT_SECRET</code></td>
      <td>Yes in staging/production</td>
      <td>JWT signing secret. Minimum 32 characters. Never placed in YAML. See Security page.</td>
    </tr>
    <tr>
      <td><code>RITA_SERVER__PORT</code></td>
      <td>No</td>
      <td>Overrides the server port at runtime (double-underscore = nested key).</td>
    </tr>
  </tbody>
</table>

<hr />

<h2>How to Add a New Config Key</h2>
<ol>
  <li>Add the field with its type and default to the appropriate nested <code>BaseSettings</code> class in <code>config.py</code>.</li>
  <li>Add the default value to <code>config/base.yaml</code>.</li>
  <li>Add environment-specific overrides to <code>development.yaml</code> (and staging/production YAMLs as needed).</li>
  <li>Access the value via <code>settings.&lt;section&gt;.&lt;field&gt;</code>.</li>
  <li>Never use <code>os.environ.get()</code> directly in route or service code — always go through <code>settings</code>.</li>
</ol>

<hr />

<p><em>Source file: <code>riia-jun-release/src/rita/config.py</code> — Sprint 1, Day 8.</em></p>
"""

# ---------------------------------------------------------------------------
# Page 2 — Security: JWT & Secret Handling
# ---------------------------------------------------------------------------

SECURITY_BODY = """
<h1>Sprint 1: Security — JWT &amp; Secret Handling</h1>

<p>
  This page documents RITA's rules for managing JWT signing secrets and sensitive
  credentials across all deployment environments.
</p>

<hr />

<h2>Core Principle</h2>
<p>
  <strong>Secrets never live in YAML files.</strong>
  All sensitive values are sourced exclusively from environment variables and
  stored as Pydantic <code>SecretStr</code> — a type that redacts the value from
  logs, repr output, and serialisation.
</p>

<hr />

<h2>JWT Secret Rules</h2>
<ol>
  <li>
    <strong>Single source of truth:</strong> <code>RITA_JWT_SECRET</code> environment variable only.
    Any <code>jwt_secret</code> key that accidentally appears in a YAML file is
    silently stripped before the config object is constructed.
  </li>
  <li>
    <strong>Development default:</strong> If <code>RITA_JWT_SECRET</code> is not set,
    the value defaults to <code>dev-secret-change-in-prod</code>.
    This is intentionally weak so it is obvious when the default is in use.
  </li>
  <li>
    <strong>Staging / Production enforcement:</strong> A Pydantic
    <code>model_validator(mode="after")</code> runs at application startup and
    raises <code>ValueError</code> if any of the following are true:
    <ul>
      <li>The secret is absent or empty.</li>
      <li>The secret equals the development default (<code>dev-secret-change-in-prod</code>).</li>
      <li>The secret is fewer than 32 characters.</li>
    </ul>
    The application will not start until the condition is resolved.
  </li>
  <li>
    <strong>No logging:</strong> Because <code>jwt_secret</code> is typed as
    <code>SecretStr</code>, Pydantic will never include the actual value in
    <code>__repr__</code>, <code>model_dump()</code>, or any structured log output.
  </li>
</ol>

<hr />

<h2>Implementation Reference</h2>
<p>From <code>riia-jun-release/src/rita/config.py</code>:</p>
<pre>
class SecuritySettings(BaseSettings):
    model_config = SettingsConfigDict(extra="forbid", env_prefix="RITA_")

    jwt_secret: SecretStr = Field(
        default=SecretStr("dev-secret-change-in-prod"),
        validation_alias="RITA_JWT_SECRET",
    )
    cors_origins: list[str] = ["http://localhost:8000"]
</pre>
<pre>
@model_validator(mode="after")
def _validate_secrets(self) -> "Settings":
    if self.env in ("staging", "production"):
        secret_val = self.security.jwt_secret.get_secret_value()
        if not secret_val or secret_val == "dev-secret-change-in-prod":
            raise ValueError(
                f"RITA_JWT_SECRET must be set to a strong secret in '{self.env}'."
            )
        if len(secret_val) &lt; 32:
            raise ValueError("RITA_JWT_SECRET must be at least 32 characters long.")
    return self
</pre>

<hr />

<h2>Environment Requirements Table</h2>
<table>
  <colgroup>
    <col style="width:20%" />
    <col style="width:30%" />
    <col style="width:50%" />
  </colgroup>
  <thead>
    <tr>
      <th>Environment</th>
      <th>RITA_JWT_SECRET required?</th>
      <th>Minimum requirement</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>development</td>
      <td>No</td>
      <td>Default <code>dev-secret-change-in-prod</code> is accepted.
          App starts without the variable set.</td>
    </tr>
    <tr>
      <td>staging</td>
      <td>Yes</td>
      <td>Must be set, must not equal the dev default, must be &ge;32 characters.
          App refuses to start otherwise.</td>
    </tr>
    <tr>
      <td>production</td>
      <td>Yes</td>
      <td>Same as staging. Rotate regularly. Store in secrets manager (e.g. AWS Secrets Manager, Kubernetes Secret).</td>
    </tr>
  </tbody>
</table>

<hr />

<h2>Generating a Strong Secret</h2>
<p>Use any of the following to generate a suitable value:</p>
<pre>
# Python (32 bytes = 64 hex chars — well above the 32-char minimum)
python -c "import secrets; print(secrets.token_hex(32))"

# OpenSSL
openssl rand -hex 32
</pre>

<hr />

<h2>Setting the Secret in Each Deployment Target</h2>
<table>
  <colgroup>
    <col style="width:25%" />
    <col style="width:75%" />
  </colgroup>
  <thead>
    <tr>
      <th>Target</th>
      <th>How to inject RITA_JWT_SECRET</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Local / shell</td>
      <td><code>export RITA_JWT_SECRET=&lt;your-secret&gt;</code> before running the app.</td>
    </tr>
    <tr>
      <td>Docker Compose</td>
      <td>Add to the <code>environment:</code> block or reference a <code>.env</code> file
          (which must be gitignored).</td>
    </tr>
    <tr>
      <td>Kubernetes</td>
      <td>Store in a <code>Secret</code> manifest and mount as an env var in the pod spec.
          Never store the raw secret in the manifest — use Sealed Secrets or
          an external secrets operator.</td>
    </tr>
    <tr>
      <td>CI / CD pipeline</td>
      <td>Store in the pipeline's secrets vault (e.g. GitHub Actions Secrets).
          Reference as <code>${{ secrets.RITA_JWT_SECRET }}</code>.</td>
    </tr>
  </tbody>
</table>

<hr />

<h2>What NOT to Do</h2>
<ul>
  <li>Do not place <code>jwt_secret</code> in any YAML file — it will be stripped silently
      but the practice increases the risk of accidental commits.</li>
  <li>Do not commit <code>.env</code> files containing real secrets.
      Only commit <code>.env.example</code> with placeholder values.</li>
  <li>Do not call <code>settings.security.jwt_secret.get_secret_value()</code>
      outside of the JWT signing/verification code path.</li>
  <li>Do not log or return the secret value in any API response or error message.</li>
</ul>

<hr />

<p><em>Source file: <code>riia-jun-release/src/rita/config.py</code> — Sprint 1, Day 8.</em></p>
"""

# ---------------------------------------------------------------------------
# Publish
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    client = ConfluenceClient()

    pages = [
        (CONFIG_TITLE,    CONFIG_BODY,    "CONFIG_PAGE_ID",    CONFIG_PAGE_ID),
        (SECURITY_TITLE,  SECURITY_BODY,  "SECURITY_PAGE_ID",  SECURITY_PAGE_ID),
    ]

    for title, body, var_name, page_id in pages:
        if page_id:
            pid, url = client.update_page(page_id, title, body)
            print(f"Updated: {title}")
        else:
            pid, url = client.create_page(title, body, parent_id=SECTION["engineering"])
            print(f"Created: {title}")
            print(f"  {var_name} = \"{pid}\"")

        print(f"  URL: {url}")
        print()
