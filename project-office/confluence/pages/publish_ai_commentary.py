"""
Publish RITA Agent Commentary Feature — Engineering Reference to Confluence.

Run from the project root:
    CONFLUENCE_EMAIL=you@example.com python project-office/confluence/pages/publish_ai_commentary.py
"""
import sys, os
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

if not os.environ.get("CONFLUENCE_EMAIL"):
    os.environ["CONFLUENCE_EMAIL"] = "contact@ravionics.nl"

from confluence.publish import ConfluenceClient, SECTION

if not os.environ.get("CONFLUENCE_API_TOKEN"):
    _here = Path(__file__).resolve()
    for _ancestor in _here.parents:
        _candidate = _ancestor / "confluence-api-key.txt"
        if _candidate.exists():
            os.environ["CONFLUENCE_API_TOKEN"] = _candidate.read_text().splitlines()[0].strip()
            break

TITLE = "RITA Agent Commentary Feature — Engineering Reference"

BODY = """
<h1>RITA Agent Commentary Feature — Engineering Reference</h1>
<table><tbody>
  <tr><td><strong>Router</strong></td><td><code>src/rita/api/v1/workflow/commentary.py</code></td></tr>
  <tr><td><strong>Schemas</strong></td><td><code>src/rita/schemas/commentary.py</code></td></tr>
  <tr><td><strong>ORM Model</strong></td><td><code>src/rita/models/commentary_log.py</code> &rarr; <code>commentary_logs</code> table</td></tr>
  <tr><td><strong>Repository</strong></td><td><code>src/rita/repositories/commentary_log.py</code></td></tr>
  <tr><td><strong>Migration</strong></td><td><code>alembic/versions/c7e2a4f81d39_add_commentary_log.py</code></td></tr>
  <tr><td><strong>Frontend module</strong></td><td><code>dashboard/js/rita/commentary.js</code></td></tr>
  <tr><td><strong>API prefix</strong></td><td><code>/api/v1/commentary</code></td></tr>
  <tr><td><strong>Auth</strong></td><td>None — matches chat_router pattern</td></tr>
  <tr><td><strong>Merged</strong></td><td>2026-05-15 — master branch</td></tr>
</tbody></table>

<h2>What It Does</h2>
<p>Auto-generates plain-English narrative commentary for two RITA dashboard pages. Fully local &mdash; no external LLM. Deterministic rule-based reasoning today; <code>_build_narrative()</code> is the single swap point for a future LLM upgrade.</p>
<table><thead><tr><th>Page</th><th>Trigger</th><th>Display</th></tr></thead><tbody>
  <tr><td>Overview (Market Signals)</td><td>Auto-fires on section load</td><td>Typewriter animation in narrator box above Overview title</td></tr>
  <tr><td>Strategy</td><td>Fires in parallel with POST /api/v1/strategy on button click</td><td>Typewriter animation above result grid</td></tr>
</tbody></table>

<h2>API Endpoint</h2>
<h3>POST /api/v1/commentary</h3>
<p>Generates deterministic narrative commentary for the given app+page combination.</p>

<p><strong>Request body:</strong></p>
<pre>
{
  "app":        "rita",       // required — valid values: rita
  "page":       "overview",   // required — valid values: overview, strategy
  "instrument": "NIFTY"       // required for page=strategy; ignored for overview
}
</pre>

<p><strong>Response:</strong></p>
<pre>
{
  "app":                  "rita",
  "page":                 "overview",
  "commentary":           "Cross-instrument overview: US: NVIDIA (STRONG weekly / NEUTRAL monthly)...",
  "instruments_analyzed": ["NVIDIA", "ASML", "NIFTY", "BANKNIFTY"],
  "latency_ms":           142.3
}
</pre>

<p><strong>Error responses:</strong></p>
<table><thead><tr><th>Case</th><th>HTTP</th><th>Detail</th></tr></thead><tbody>
  <tr><td>Unknown app+page</td><td>400</td><td>No handler registered for app='X' page='Y'</td></tr>
  <tr><td>Strategy without instrument</td><td>400</td><td>instrument is required for page='strategy'</td></tr>
  <tr><td>Data error</td><td>200</td><td>Fallback sentence in commentary — never HTTP 500</td></tr>
</tbody></table>

<h2>Reasoning Layer</h2>
<p><strong>Overview handler:</strong> Iterates NVIDIA, ASML, NIFTY, BANKNIFTY. Per-instrument try/except. Resamples daily OHLCV to weekly (W) and monthly (ME). Computes SMA-20, RSI-14, EMA-20 slope, volume avg-20 per timeframe. Classifies each instrument&times;timeframe as STRONG / NEUTRAL / CONSOLIDATING / WEAK / RECOVERING. Rankings by composite z-score (weekly &times;2 + monthly). Geographic buckets: US=NVIDIA, EU=ASML, India=NIFTY+BANKNIFTY.</p>
<p><strong>Strategy handler:</strong> Calls <code>get_market_summary()</code>, <code>get_sentiment_score()</code>, <code>get_allocation_recommendation()</code> from core modules. Builds rationale from recommendation, allocation_pct, rationale, primary_constraint.</p>
<p><strong>LLM swap point:</strong> <code>_build_narrative(data: dict) -> str</code> in <code>commentary.py</code>. Replace body with LLM call; signature and call sites unchanged.</p>

<h2>DB Audit — commentary_logs Table</h2>
<p>One row written per request via <code>CommentaryLogRepository(db).create(...)</code>.</p>
<table><thead><tr><th>Column</th><th>Type</th><th>Notes</th></tr></thead><tbody>
  <tr><td>id</td><td>str (UUID)</td><td>Primary key</td></tr>
  <tr><td>app</td><td>str</td><td>e.g. rita</td></tr>
  <tr><td>page</td><td>str</td><td>e.g. overview, strategy</td></tr>
  <tr><td>instrument</td><td>str (nullable)</td><td>Set for strategy, null for overview</td></tr>
  <tr><td>latency_ms</td><td>float</td><td>End-to-end handler latency</td></tr>
  <tr><td>status</td><td>str</td><td>ok or error</td></tr>
  <tr><td>commentary_preview</td><td>str</td><td>First 200 chars of generated text</td></tr>
  <tr><td>timestamp</td><td>datetime (UTC)</td><td>Request time</td></tr>
</tbody></table>

<h2>Monitor KPIs (added to GET /api/v1/chat/monitor)</h2>
<p>Three fields merged into the existing chat monitor response via <code>CommentaryLogRepository.get_summary()</code>:</p>
<table><thead><tr><th>Field</th><th>Description</th></tr></thead><tbody>
  <tr><td>commentary_count</td><td>Total rows in commentary_logs</td></tr>
  <tr><td>commentary_avg_latency_ms</td><td>Average latency across all rows</td></tr>
  <tr><td>commentary_error_count</td><td>Count of rows where status = error</td></tr>
</tbody></table>
<p>These KPIs are displayed on the Ops dashboard &rarr; Chat Analytics page in the <strong>Agent Commentary Metrics</strong> panel (right half of the intent distribution row).</p>

<h2>Frontend Integration</h2>
<table><thead><tr><th>File</th><th>Change</th></tr></thead><tbody>
  <tr><td>dashboard/js/rita/commentary.js</td><td>New module &mdash; loadOverviewCommentary(), showOverviewCommentary(text), showStrategyCommentary(text). Typewriter animator with _twToken cancel.</td></tr>
  <tr><td>dashboard/js/rita/market-signals.js</td><td>Calls await loadOverviewCommentary() after loadGeoPanels()</td></tr>
  <tr><td>dashboard/js/rita/export.js</td><td>runStrategy() uses Promise.allSettled([commentary, strategy]) &mdash; strategy grid always renders even if commentary fails</td></tr>
  <tr><td>dashboard/js/rita/main.js</td><td>window.loadOverviewCommentary = loadOverviewCommentary</td></tr>
  <tr><td>dashboard/rita.html</td><td>Two narrator boxes: commentary-overview-box (after geo-panels) and commentary-strategy-box (above strategy-result)</td></tr>
  <tr><td>dashboard/js/ops/chat.js</td><td>Agent Commentary Metrics panel added to Ops Chat Analytics page</td></tr>
</tbody></table>

<h2>Tests</h2>
<p>34 unit tests in <code>tests/unit/test_commentary.py</code> &mdash; all pass. Coverage: schemas 100%, repository 100%, ORM model 100%, router 54% (narrative builders require live CSV data).</p>

<h2>Spec Reference</h2>
<p>Full specification: <code>project-office/specs/Spec_Commentary_Feature.md</code></p>
"""


def main():
    client = ConfluenceClient()
    parent_id = SECTION["engineering"]

    result, status = client._request(
        "GET",
        f"/content?spaceKey=RIIAProjec&title={quote(TITLE)}&type=page&expand=version",
    )
    existing = None
    if status == 200:
        existing = next((p for p in result.get("results", []) if p["title"] == TITLE), None)

    if existing:
        _, url = client.update_page(existing["id"], TITLE, BODY)
        print(f"UPDATED: {TITLE}")
        print(f"  URL: {url}")
    else:
        page_id, url = client.create_page(TITLE, BODY, parent_id=parent_id)
        print(f"CREATED: {TITLE}")
        print(f"  Page ID: {page_id}")
        print(f"  URL: {url}")


if __name__ == "__main__":
    main()
