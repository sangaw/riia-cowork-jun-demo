import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from confluence.publish import ConfluenceClient, SECTION

TITLE = "Sprint 3 — Observability & Runbook"
PAGE_ID = "67895297"

BODY = """
<h2>1. Overview</h2>
<p>
  Sprint 3 added a full observability stack to RITA. Every HTTP request is traced end-to-end
  through structured JSON logs; Prometheus scrapes request metrics from a dedicated
  <code>/metrics</code> endpoint; and two health probes give Kubernetes the signals it needs
  to manage pod lifecycle correctly.
</p>
<ul>
  <li><strong>Structured JSON logging</strong> — <code>structlog</code> emits machine-readable
      JSON on every log call. All lines for a single request share a <code>trace_id</code>.</li>
  <li><strong>Prometheus metrics</strong> — <code>prometheus-fastapi-instrumentator</code>
      tracks HTTP request counts, duration histograms, and status-code distributions at
      <code>GET /metrics</code>.</li>
  <li><strong>Liveness probe</strong> — <code>GET /health</code> confirms the process is alive.
      No database check; never expected to fail.</li>
  <li><strong>Readiness probe</strong> — <code>GET /readyz</code> runs <code>SELECT 1</code>
      against the SQLAlchemy engine and returns HTTP 503 if the database is unreachable.</li>
</ul>

<h2>2. Log Format</h2>
<p>
  <code>configure_logging()</code> (called once in the FastAPI lifespan handler) configures
  structlog with the following processor chain:
</p>
<ol>
  <li><code>merge_contextvars</code> — merges context variables (including <code>trace_id</code>) into every log event.</li>
  <li><code>add_log_level</code> — adds a <code>level</code> field.</li>
  <li><code>TimeStamper(fmt="iso")</code> — adds an ISO-8601 <code>timestamp</code> field.</li>
  <li><code>StackInfoRenderer</code> + <code>format_exc_info</code> — formats exception tracebacks inline.</li>
  <li><code>JSONRenderer</code> — serialises the event dict to a single JSON line.</li>
</ol>
<p>The minimum log level is <code>INFO</code> (set via <code>make_filtering_bound_logger(logging.INFO)</code>).</p>

<h3>Example log line</h3>
<pre><code>{
  "event": "http.request",
  "trace_id": "4f3a1c22-8d0b-4e2a-b9f7-12345678abcd",
  "method": "GET",
  "path": "/api/v1/positions",
  "status_code": 200,
  "level": "info",
  "timestamp": "2026-04-05T09:14:33.412Z"
}</code></pre>

<h3>trace_id injection (TraceIDMiddleware)</h3>
<p>
  <code>TraceIDMiddleware</code> (registered via <code>app.add_middleware(TraceIDMiddleware)</code>
  in <code>main.py</code>) runs before every request handler:
</p>
<ul>
  <li>Reads <code>X-Request-ID</code> from the incoming request headers if the client supplies one.</li>
  <li>Generates a new UUID4 otherwise.</li>
  <li>Binds the value to structlog context vars (<code>structlog.contextvars.bind_contextvars(trace_id=...)</code>),
      so every log call within that request automatically inherits it.</li>
  <li>Writes <code>X-Request-ID</code> back onto the response headers so callers can correlate.</li>
  <li>Clears the context vars after the response is sent, preventing leakage between requests.</li>
</ul>
<p>
  Because the trace_id is stored in a <code>ContextVar</code>, concurrent async requests each
  get their own slot — there is no cross-request contamination.
</p>

<h2>3. Health Probes</h2>
<table>
  <thead>
    <tr>
      <th>Endpoint</th>
      <th>Purpose</th>
      <th>Success response</th>
      <th>Failure response</th>
      <th>Notes</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>GET /health</code></td>
      <td>Liveness probe</td>
      <td>HTTP 200 <code>{"status":"ok","version":"&lt;ver&gt;"}</code></td>
      <td>Never fails by design</td>
      <td>No database check performed. Kubernetes liveness probe target. Returns the app version string from settings.</td>
    </tr>
    <tr>
      <td><code>GET /readyz</code></td>
      <td>Readiness probe</td>
      <td>HTTP 200 <code>{"status":"ready"}</code></td>
      <td>HTTP 503 <code>{"status":"unavailable","detail":"&lt;error&gt;"}</code></td>
      <td>Executes <code>SELECT 1</code> via the SQLAlchemy engine. Kubernetes readiness probe target. Logs <code>readyz_check_failed</code> on failure.</td>
    </tr>
  </tbody>
</table>

<h2>4. Prometheus Metrics</h2>
<p>
  Metrics are exposed at <code>GET /metrics</code> in standard Prometheus text exposition format.
  The endpoint is instrumented by <code>prometheus-fastapi-instrumentator</code> via the
  <code>instrument_app(app)</code> call in <code>main.py</code>.
</p>
<p>
  <strong>Important:</strong> <code>instrument_app(app)</code> must be called <em>after</em>
  all routers are registered so the instrumentator captures every route.
</p>

<h3>Excluded paths</h3>
<p>The following endpoints are excluded from tracking to avoid high-frequency noise in dashboards:</p>
<ul>
  <li><code>/metrics</code> — the scrape endpoint itself</li>
  <li><code>/health</code> — liveness probe (polled every 30 s by Kubernetes)</li>
  <li><code>/readyz</code> — readiness probe (polled every 10 s by Kubernetes)</li>
</ul>

<h3>Key metric names</h3>
<table>
  <thead>
    <tr>
      <th>Metric</th>
      <th>Type</th>
      <th>Description</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>http_requests_total</code></td>
      <td>Counter</td>
      <td>Total HTTP requests, labelled by method, handler, and status code.</td>
    </tr>
    <tr>
      <td><code>http_request_duration_seconds</code></td>
      <td>Histogram</td>
      <td>Request latency distribution, labelled by method and handler. Use the <code>_bucket</code> series for percentile calculations.</td>
    </tr>
  </tbody>
</table>
<p>
  Status codes are <strong>not grouped</strong> (<code>should_group_status_codes=False</code>),
  so <code>200</code>, <code>404</code>, <code>422</code>, and <code>503</code> appear as
  separate label values.
</p>

<h2>5. Runbook — Common Scenarios</h2>

<h4>Scenario 1: Readiness probe returning HTTP 503</h4>
<p><strong>Symptom:</strong> <code>GET /readyz</code> returns <code>{"status":"unavailable","detail":"..."}</code>.</p>
<p><strong>Diagnosis:</strong></p>
<ol>
  <li>Search structured logs for <code>"event": "readyz_check_failed"</code> — the <code>error</code> field contains the raw exception message.</li>
  <li>Confirm the <code>RITA_DATABASE__DATABASE_URL</code> environment variable is set and points to a valid path (e.g. <code>sqlite:////data/rita.db</code>).</li>
  <li>Check that the SQLite DB file exists and the process has read/write permissions.</li>
  <li>If running in a container, verify the data volume is mounted and not full (<code>df -h</code>).</li>
</ol>
<p><strong>Resolution:</strong> Fix the DB file path or permissions, then re-check <code>GET /readyz</code>. The pod will be taken out of the Kubernetes endpoint slice until the probe passes.</p>

<h4>Scenario 2: Missing trace_id in logs</h4>
<p><strong>Symptom:</strong> Log lines lack a <code>trace_id</code> field, making it impossible to correlate a request across log lines.</p>
<p><strong>Diagnosis:</strong></p>
<ol>
  <li>Verify that <code>app.add_middleware(TraceIDMiddleware)</code> appears in <code>main.py</code> <em>before</em> any route handlers or exception handlers are registered.</li>
  <li>Confirm that <code>structlog.contextvars.merge_contextvars</code> is present as the first processor in <code>configure_logging()</code>.</li>
</ol>
<p><strong>Resolution:</strong> <code>TraceIDMiddleware</code> calls <code>structlog.contextvars.bind_contextvars(trace_id=...)</code> — it must execute before any log calls are made. Middleware is applied in reverse-registration order in Starlette, so add it last if other middleware must run first.</p>

<h4>Scenario 3: /metrics returning 404</h4>
<p><strong>Symptom:</strong> Prometheus scraper receives HTTP 404 when hitting <code>GET /metrics</code>.</p>
<p><strong>Diagnosis:</strong></p>
<ol>
  <li>Open <code>main.py</code> and confirm that <code>instrument_app(app)</code> is present.</li>
  <li>Confirm it is called <em>after</em> all <code>app.include_router()</code> calls — if it is called before routers are registered, the <code>/metrics</code> route may not be set up correctly.</li>
</ol>
<p><strong>Resolution:</strong> Move <code>instrument_app(app)</code> to the end of <code>main.py</code>, after all router registrations. The route <code>GET /metrics</code> is created by <code>.expose(app)</code> inside <code>instrument_app</code>.</p>

<h4>Scenario 4: Log verbosity too high in production</h4>
<p><strong>Symptom:</strong> Logs are human-readable coloured output (ConsoleRenderer) in a production container, flooding log aggregators with ANSI escape codes.</p>
<p><strong>Diagnosis:</strong></p>
<ol>
  <li>Check the <code>RITA_ENV</code> environment variable in the running container.</li>
  <li>If unset or set to <code>development</code>, structlog uses <code>ConsoleRenderer</code>.</li>
</ol>
<p><strong>Resolution:</strong> Set <code>RITA_ENV=production</code> to switch to <code>JSONRenderer</code>, which emits machine-readable JSON only. No application restart is required if the env var is injected via a Kubernetes ConfigMap update and the pod is cycled.</p>
<p><em>Note:</em> The current implementation in <code>logging_config.py</code> always uses <code>JSONRenderer</code> (no ConsoleRenderer branch). If a development-friendly renderer is added in future, the <code>RITA_ENV</code> guard described above is the correct place to switch.</p>

<h2>6. Kubernetes Probe Configuration</h2>
<p>
  Add the following stanza to the RITA container spec in your Kubernetes Deployment manifest.
  Adjust <code>initialDelaySeconds</code> to match your observed startup time.
</p>
<pre><code>livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 30
readinessProbe:
  httpGet:
    path: /readyz
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 10
  failureThreshold: 3</code></pre>
<p>
  The liveness probe polls every 30 seconds; a single failure restarts the pod.
  The readiness probe polls every 10 seconds; three consecutive failures remove the pod
  from the service endpoint slice (traffic is drained, not killed).
</p>
"""

if __name__ == "__main__":
    client = ConfluenceClient()
    if PAGE_ID:
        pid, url = client.update_page(PAGE_ID, TITLE, BODY)
        print(f"Updated: {url}")
    else:
        pid, url = client.create_page(TITLE, BODY, parent_id=SECTION["operations"])
        print(f"Created: {url}")
        print(f'PAGE_ID = "{pid}"')
