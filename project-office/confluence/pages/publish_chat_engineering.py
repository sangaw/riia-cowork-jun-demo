"""
Publish RITA Chat Feature — Engineering Reference to Confluence.

Run from the project root:
    CONFLUENCE_EMAIL=you@example.com python project-office/confluence/pages/publish_chat_engineering.py
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

TITLE = "RITA Chat Feature — Engineering Reference"

BODY = """
<h1>RITA Chat Feature — Engineering Reference</h1>
<table><tbody>
  <tr><td><strong>Router</strong></td><td><code>src/rita/api/v1/workflow/chat.py</code></td></tr>
  <tr><td><strong>Classifier</strong></td><td><code>src/rita/core/classifier.py</code></td></tr>
  <tr><td><strong>Monitor</strong></td><td><code>src/rita/core/chat_monitor.py</code></td></tr>
  <tr><td><strong>Frontend</strong></td><td><code>dashboard/js/rita/chat.js</code></td></tr>
  <tr><td><strong>API prefix</strong></td><td><code>/api/v1/chat</code></td></tr>
  <tr><td><strong>Auth</strong></td><td>JWT required on all endpoints</td></tr>
</tbody></table>

<h2>API Endpoints</h2>

<h3>POST /api/v1/chat/warmup</h3>
<p>Pre-warms the SentenceTransformer classifier and computes market-driven chip suggestions for the current instrument. Called by the dashboard when the user opens the chat panel. Idempotent &mdash; safe to call multiple times.</p>

<p><strong>Query parameters:</strong></p>
<table><thead><tr><th>Parameter</th><th>Type</th><th>Default</th><th>Description</th></tr></thead><tbody>
  <tr><td><code>instrument</code></td><td>string (optional)</td><td>active instrument</td><td>Override the instrument for chip generation</td></tr>
</tbody></table>

<p><strong>Response:</strong></p>
<pre>
{
  "status":     "ready",
  "instrument": "NIFTY",
  "chips": [
    { "label": "RSI at 58 — what does it mean?", "query": "What is the RSI reading today?" },
    ...                                           // up to 10 chips
  ],
  "alerts": [
    { "severity": "warn", "message": "Volatility near historic lows..." }
    ...                                           // up to 2 alerts; null if no extreme conditions
  ]
}
</pre>
<p>If chip generation fails (e.g. no CSV data), <code>chips</code> is <code>null</code> and <code>status</code> is still <code>"ready"</code> &mdash; the warmup never blocks the UI.</p>

<h3>POST /api/v1/chat</h3>
<p>Classify a free-text query and return a deterministic, data-driven response.</p>

<p><strong>Request body:</strong></p>
<pre>
{
  "query":              "Is the market overbought?",   // required
  "instrument":         "NIFTY",                       // optional; falls back to active instrument
  "portfolio_inr":      1000000,                       // default 1,000,000 INR
  "target_return_pct":  15.0,                          // optional; used by return_estimates handler
  "time_horizon_days":  365                            // optional; used by return_estimates handler
}
</pre>

<p><strong>Response:</strong></p>
<pre>
{
  "instrument":     "NIFTY",
  "intent":         "market_overbought_oversold",
  "handler":        "market_sentiment",
  "confidence":     0.7231,
  "low_confidence": false,
  "response":       "RSI is currently 58.4, which sits in neutral territory ...",
  "latency_ms":     42.3
}
</pre>

<p><strong>Error responses:</strong></p>
<table><thead><tr><th>HTTP</th><th>Condition</th></tr></thead><tbody>
  <tr><td>503</td><td>CSV data not found for the requested instrument</td></tr>
  <tr><td>500</td><td>Classification or dispatch error</td></tr>
</tbody></table>

<p><strong>low_confidence behaviour:</strong> When <code>confidence &lt; 0.42</code>, the response still returns HTTP 200 with <code>low_confidence: true</code>. The response text acknowledges the ambiguity and suggests a rephrased question. The frontend renders a muted style for low-confidence replies.</p>

<h3>GET /api/v1/chat/monitor</h3>
<p>Returns KPIs and the recent query log from the chat monitor CSV. Used by the Ops dashboard chat monitoring panel.</p>

<p><strong>Response shape:</strong></p>
<pre>
{
  "summary": {
    "total_queries":        142,
    "success_rate_pct":     94.4,
    "avg_latency_ms":       38.1,
    "low_confidence_pct":   5.6
  },
  "recent": [
    {
      "timestamp":    "2026-04-26T10:14:03",
      "query":        "Is the market overbought?",
      "intent":       "market_overbought_oversold",
      "confidence":   0.72,
      "latency_ms":   41.0,
      "status":       "success"
    },
    ...                    // last 20 queries
  ],
  "intents": {
    "market_overbought_oversold": 38,
    "strategy_recommendation":    24,
    ...
  }
}
</pre>

<h2>Classifier — Implementation Details</h2>

<h3>Model loading</h3>
<pre>
# classifier.py
_model: SentenceTransformer | None = None

def _build_seed_index() -> None:
    global _model
    if _model is not None:
        return                        # already loaded — no-op
    _model = SentenceTransformer(settings.chat.embed_model_path)
    # embed all 20 x N seed phrases once; stored as numpy arrays
</pre>
<p>The model path is read from <code>settings.chat.embed_model_path</code> (config YAML). Default: <code>data/models/all-MiniLM-L6-v2</code>.</p>

<h3>Intent matching</h3>
<pre>
def classify(query: str) -> ClassifyResult:
    query_vec = _model.encode([query])                 # 384-dim embedding
    scores = cosine_similarity(query_vec, seed_vecs)   # shape: (1, N)
    best_idx = scores.argmax()
    confidence = scores[0, best_idx]
    intent = INTENTS[seed_intent_map[best_idx]]
    return ClassifyResult(
        intent=intent,
        confidence=float(confidence),
        low_confidence=confidence &lt; 0.42,
    )
</pre>

<h2>Data Cache — _market_signals_cache</h2>
<pre>
# chat.py
_market_signals_cache: dict[str, dict[str, Any]] = {}
# key = instrument id ("NIFTY", "NVIDIA", ...)
# value = { "df": DataFrame, "mtime_key": (mtime_primary, mtime_manual) }

def _get_df(instrument: str) -&gt; DataFrame:
    mtime_key = (os.path.getmtime(primary_path), mtime_manual)
    if cached and cached["mtime_key"] == mtime_key:
        return cached["df"]           # cache hit
    df = calculate_indicators(load_nifty_csv(primary_path))
    _market_signals_cache[instrument] = {"df": df, "mtime_key": mtime_key}
    return df
</pre>
<p>The cache is process-scoped (in-memory). A server restart clears it. The first request after restart reloads the CSV.</p>

<h2>Chat Monitor — Logging</h2>
<p>File: <code>src/rita/core/chat_monitor.py</code></p>
<p>Every query is appended to a CSV log. Fields written per row:</p>
<table><thead><tr><th>Field</th><th>Type</th><th>Description</th></tr></thead><tbody>
  <tr><td><code>timestamp</code></td><td>ISO datetime</td><td>UTC time of the request</td></tr>
  <tr><td><code>query_text</code></td><td>string</td><td>Raw user query (truncated to 500 chars)</td></tr>
  <tr><td><code>intent_name</code></td><td>string</td><td>Matched intent identifier</td></tr>
  <tr><td><code>handler</code></td><td>string</td><td>Handler function dispatched</td></tr>
  <tr><td><code>confidence</code></td><td>float</td><td>Cosine similarity score (0–1)</td></tr>
  <tr><td><code>low_confidence</code></td><td>bool</td><td>True if confidence &lt; 0.42</td></tr>
  <tr><td><code>latency_ms</code></td><td>float</td><td>End-to-end response time</td></tr>
  <tr><td><code>response_preview</code></td><td>string</td><td>First 200 chars of the response</td></tr>
  <tr><td><code>status</code></td><td>string</td><td><code>success</code> or <code>low_confidence</code></td></tr>
</tbody></table>

<h2>Frontend Integration — chat.js</h2>
<p>File: <code>dashboard/js/rita/chat.js</code></p>
<table><thead><tr><th>Function</th><th>Triggered by</th><th>Description</th></tr></thead><tbody>
  <tr><td><code>sendChatMsg()</code></td><td>Enter key / Send button</td><td>Reads <code>#chat-input</code>, calls <code>POST /api/v1/chat</code>, appends message to thread</td></tr>
  <tr><td><code>useChip(query)</code></td><td>Chip button click</td><td>Pre-fills <code>#chat-input</code> and submits via <code>sendChatMsg()</code></td></tr>
  <tr><td><code>clearChat()</code></td><td>Clear button</td><td>Empties the chat thread DOM</td></tr>
</tbody></table>

<p>Warmup is called automatically when the chat section is first navigated to (registered in <code>main.js</code> section loader). Chips and alerts returned by warmup are rendered into the chip strip and alert banner above the input box.</p>

<p><strong>Low-confidence rendering:</strong> Responses with <code>low_confidence: true</code> are rendered with a muted text style and a &ldquo;Low confidence&rdquo; label to inform the user that the query did not match a known intent clearly.</p>

<h2>Configuration</h2>
<table><thead><tr><th>Config key</th><th>Default</th><th>Description</th></tr></thead><tbody>
  <tr><td><code>chat.embed_model_path</code></td><td><code>data/models/all-MiniLM-L6-v2</code></td><td>Local path to the SentenceTransformer model directory</td></tr>
  <tr><td><code>chat.confidence_threshold</code></td><td><code>0.42</code></td><td>Minimum cosine similarity to trust the top intent</td></tr>
</tbody></table>

<h2>Adding a New Intent</h2>
<ol>
  <li>Add an entry to the <code>INTENTS</code> list in <code>classifier.py</code> with a name, handler, and seed phrases</li>
  <li>If the handler is new, implement it in <code>classifier.py</code> under <code>dispatch()</code></li>
  <li>Rebuild the seed index by calling <code>_build_seed_index()</code> (happens automatically on next warmup)</li>
  <li>Add a unit test in <code>tests/unit/test_classifier.py</code> verifying the new intent is matched by at least 3 representative queries</li>
  <li>Update <code>Specs/Spec_Chat_Feature.md</code> to reflect the new intent count and handler mapping</li>
</ol>
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
