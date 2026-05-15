"""
Publish RITA Chat Feature — Architecture & Design to Confluence.

Run from the project root:
    CONFLUENCE_EMAIL=you@example.com python project-office/confluence/pages/publish_chat_architecture.py
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

TITLE = "RITA Chat Feature — Architecture & Design"

BODY = """
<h1>RITA Chat Feature — Architecture &amp; Design</h1>
<table><tbody>
  <tr><td><strong>Status</strong></td><td>Production</td></tr>
  <tr><td><strong>Date</strong></td><td>2026-04-26</td></tr>
  <tr><td><strong>Component</strong></td><td>Chat Pipeline (Workflow Layer)</td></tr>
  <tr><td><strong>Key constraint</strong></td><td>Fully local &mdash; zero external API calls at runtime</td></tr>
</tbody></table>

<h2>Overview</h2>
<p>The RITA Chat feature allows users to query the system in natural language and receive deterministic, data-driven responses about market conditions, portfolio performance, and investment scenarios. It is <strong>fully local</strong> &mdash; no Claude, OpenAI, or any other LLM API is called at runtime. Every response is computed from live OHLCV data and pre-calculated technical indicators.</p>

<h2>Three-Layer Pipeline</h2>

<h3>Layer 1 — Intent Classification</h3>
<p>File: <code>src/rita/core/classifier.py</code></p>
<ul>
  <li>Uses <strong>sentence-transformers/all-MiniLM-L6-v2</strong> &mdash; a 22MB local embedding model that runs entirely offline</li>
  <li>20 fixed investment intents, each pre-seeded with representative phrases</li>
  <li>On startup, seed phrases are embedded once and cached in memory (<code>_model</code> global)</li>
  <li>Each user query is embedded and matched against all seeds via <strong>cosine similarity</strong></li>
  <li>Confidence threshold: <strong>0.42</strong> &mdash; queries below this score route to a low-confidence fallback response</li>
  <li>Warmup endpoint (<code>POST /api/v1/chat/warmup</code>) pre-loads the model before the user types their first query</li>
</ul>

<h3>Layer 2 — Deterministic Data Dispatch</h3>
<p>File: <code>src/rita/core/classifier.py</code> &mdash; <code>dispatch()</code></p>
<ul>
  <li>Once an intent is classified, a matching handler runs against <strong>live OHLCV data</strong> (loaded from CSV, cached by mtime)</li>
  <li>Handlers cover six data domains:</li>
</ul>
<table><thead><tr><th>Handler</th><th>What it computes</th></tr></thead><tbody>
  <tr><td><code>market_sentiment</code></td><td>RSI, MACD, Bollinger, EMA trend &mdash; composite market score</td></tr>
  <tr><td><code>strategy_recommendation</code></td><td>Allocation advice based on regime + feasibility</td></tr>
  <tr><td><code>return_estimates</code></td><td>1yr / 3yr / 5yr projections from historical CAGR</td></tr>
  <tr><td><code>stress_scenarios</code></td><td>Portfolio impact of -10%, -20%, -30%, +20% market moves</td></tr>
  <tr><td><code>performance_feedback</code></td><td>RITA vs benchmark &mdash; Sharpe, MDD, CAGR from latest backtest</td></tr>
  <tr><td><code>portfolio_comparison</code></td><td>RITA vs buy-and-hold normalised return comparison</td></tr>
</tbody></table>
<p>All handlers are <strong>deterministic</strong> &mdash; the same market state always produces the same response. No stochastic generation.</p>

<h3>Layer 3 — Response Caching</h3>
<p>File: <code>src/rita/api/v1/workflow/chat.py</code> &mdash; <code>_market_signals_cache</code></p>
<ul>
  <li>The market signals DataFrame is cached per instrument, keyed by the CSV file&rsquo;s <code>mtime</code></li>
  <li>Cache is invalidated automatically when the source CSV is updated</li>
  <li>A manual supplement file (<code>data/input/DAILY-DATA/{instrument}_manual.csv</code>) is appended when present, allowing intraday updates without a full CSV rebuild</li>
  <li>This is <strong>data caching</strong>, not LLM response caching &mdash; the handler always runs fresh calculations</li>
</ul>

<h2>Data Flow</h2>
<pre>
User types query
      |
      v
POST /api/v1/chat/warmup  (called once when chat panel opens)
  -> _build_seed_index()  loads all-MiniLM-L6-v2, embeds 20 seed phrases
  -> get_market_summary() computes current indicators
  -> returns dynamic chip suggestions + proactive alerts

User submits query
      |
      v
POST /api/v1/chat
  -> classify(query)     cosine similarity -> best intent (confidence score)
  -> dispatch(intent)    runs deterministic handler against cached OHLCV df
  -> log_query()         appends to chat_monitor.csv (query, intent, latency)
  -> returns { intent, confidence, response, latency_ms }
</pre>

<h2>Intent Taxonomy — 20 Fixed Intents</h2>
<p>Intents are grouped by domain. Each has a canonical handler and a set of seed phrases used for similarity matching.</p>
<table><thead><tr><th>Domain</th><th>Intent examples</th><th>Handler</th></tr></thead><tbody>
  <tr><td>Market conditions</td><td>Is the market overbought? What is the RSI today? Market sentiment?</td><td><code>market_sentiment</code></td></tr>
  <tr><td>Volatility</td><td>How volatile is the market? Current ATR? High volatility warning?</td><td><code>market_sentiment</code></td></tr>
  <tr><td>Trend analysis</td><td>Is there an uptrend? EMA crossover signal? Market direction?</td><td><code>market_sentiment</code></td></tr>
  <tr><td>Investment strategy</td><td>What allocation should I have? Safe investment approach? Aggressive strategy?</td><td><code>strategy_recommendation</code></td></tr>
  <tr><td>Return estimates</td><td>3-year return estimate? Annual return? What returns can I expect?</td><td><code>return_estimates</code></td></tr>
  <tr><td>Stress scenarios</td><td>What if market crashes 20%? What if it rallies 10%? Downside risk?</td><td><code>stress_scenarios</code></td></tr>
  <tr><td>RITA performance</td><td>How has RITA performed? Sharpe ratio? Historical backtest results?</td><td><code>performance_feedback</code></td></tr>
  <tr><td>Portfolio comparison</td><td>RITA vs buy-and-hold? How does RITA compare to the index?</td><td><code>portfolio_comparison</code></td></tr>
</tbody></table>

<h2>Dynamic Chat Chips &amp; Proactive Alerts</h2>
<p>On warmup, the server computes the current market state and returns:</p>
<ul>
  <li><strong>Up to 10 dynamic chips</strong> &mdash; suggested questions tailored to RSI, trend, volatility, and sentiment conditions. E.g. if RSI &gt; 70, the chip reads &ldquo;Market overbought? (RSI 74)&rdquo;</li>
  <li><strong>Up to 2 proactive alerts</strong> &mdash; extreme condition warnings (RSI &gt; 78, ATR percentile &gt; 90th, confirmed downtrend). Shown as inline alert banners in the chat UI.</li>
</ul>

<h2>Key Design Decisions</h2>
<table><thead><tr><th>Decision</th><th>Rationale</th></tr></thead><tbody>
  <tr><td>Local embedding model (all-MiniLM-L6-v2) instead of an LLM API</td><td>Zero latency, zero token cost, fully offline. Adequate for intent classification with 20 fixed intents.</td></tr>
  <tr><td>20 fixed intents rather than open-ended generation</td><td>Deterministic, testable, auditable. Every response is traceable to a specific calculation. No hallucination risk.</td></tr>
  <tr><td>Confidence threshold 0.42 for low-confidence fallback</td><td>Tuned empirically. Below this the cosine similarity is too low to trust the top intent. Fallback response guides user to a supported question.</td></tr>
  <tr><td>Instrument-scoped OHLCV cache keyed by mtime</td><td>Avoids re-loading a large CSV on every request. Invalidates automatically when the file changes &mdash; no TTL needed.</td></tr>
  <tr><td>Warmup endpoint called by the dashboard, not on API startup</td><td>The embedding model takes ~2s to load. Calling it on first chat open (not on server start) keeps startup fast and avoids loading it if chat is never used.</td></tr>
</tbody></table>

<h2>Instrument Support</h2>
<p>The chat feature supports all instruments in the RITA universe: <strong>NIFTY, BANKNIFTY, ASML, NVIDIA</strong>. The active instrument is resolved from:</p>
<ol>
  <li><code>req.instrument</code> field in the POST body (explicit override)</li>
  <li><code>_get_active_instrument_id(db)</code> &mdash; reads the <code>active_instrument_id</code> config override from the database (set via the instrument selector in the dashboard)</li>
  <li>Default: <strong>NIFTY</strong></li>
</ol>
"""


def main():
    client = ConfluenceClient()
    parent_id = SECTION["architecture"]

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
