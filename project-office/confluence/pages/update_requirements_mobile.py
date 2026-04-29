"""
Append a Mobile App (PWA) section to the Requirements Confluence page (76644353).

Reads the current page body, appends the new section, then updates in-place.

Run from any directory:
  CONFLUENCE_EMAIL=contact@ravionics.nl python project-office/confluence/pages/update_requirements_mobile.py
"""

import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from confluence.publish import ConfluenceClient, SECTION

PAGE_ID = SECTION["requirements"]  # 76644353

MOBILE_SECTION_HTML = """
<hr/>

<h2>Mobile App (PWA)</h2>
<p>An installable Progressive Web App (PWA) built for Android Chrome.
Single-file architecture — all HTML, CSS, and JavaScript live in
<code>rita-build-portfolio/android-mobile-app/index.html</code>.
Live data is toggle-gated; every API call silently falls back to hardcoded
DOM values on failure so the app never breaks.</p>

<h3>PWA Files</h3>
<table>
  <thead><tr><th>File</th><th>Purpose</th></tr></thead>
  <tbody>
    <tr><td><code>index.html</code></td><td>Entire app — HTML, CSS, and JS in one file</td></tr>
    <tr><td><code>manifest.json</code></td><td>PWA metadata (name, icons, theme_color, display=standalone)</td></tr>
    <tr><td><code>sw.js</code></td><td>Service worker — offline caching</td></tr>
    <tr><td><code>icons/icon.svg</code></td><td>Source icon (vector)</td></tr>
  </tbody>
</table>

<h3>10 Screens</h3>
<table>
  <thead><tr><th>ID</th><th>Screen</th><th>Contents</th></tr></thead>
  <tbody>
    <tr><td>s0</td><td>Home</td><td>Avatar, greeting, RITA SAYS banner, Live data toggle</td></tr>
    <tr><td>s1</td><td>Goal</td><td>YTD return radial ring, Sharpe ratio, Win Rate</td></tr>
    <tr><td>s2</td><td>Market</td><td>Timeframe tabs (Daily/Weekly/Monthly), 8-KPI grid (RSI-14, MACD, BB %B, ATR-14, EMA5/13/26, Trend score), signal highlights, price &amp; volume SVG chart</td></tr>
    <tr><td>s3</td><td>Signal Hero</td><td>Active signal types, market regime, confidence</td></tr>
    <tr><td>s4</td><td>Strategy</td><td>P&amp;L, Win Rate, Sharpe, last 4 trade decisions</td></tr>
    <tr><td>s5</td><td>Today</td><td>Date hero, regime card, NIFTY price, signal type rows</td></tr>
    <tr><td>s6</td><td>Overview</td><td>Market hero price, goal progress bar, signal previews</td></tr>
    <tr><td>s7</td><td>Market Feed</td><td>Regime pill, factor bars (Momentum/Value/Quality/Volatility), narrative paragraph</td></tr>
    <tr><td>s8</td><td>Portfolio</td><td>Total value, daily gain, holdings list with SVG sparklines</td></tr>
    <tr><td>overlay</td><td>Portfolio Detail</td><td>Detailed holdings with sparklines</td></tr>
  </tbody>
</table>
<p>Navigation: <code>goTo(screenIndex)</code> — slides left/right between screens.</p>

<h3>Live Data</h3>
<table>
  <thead><tr><th>API Call</th><th>Endpoint</th><th>Used by</th></tr></thead>
  <tbody>
    <tr><td>fetchTimeline()</td><td>GET /api/v1/risk-timeline</td><td>Regime color, Today (s5), Overview (s6), Market Feed (s7)</td></tr>
    <tr><td>fetchSignals()</td><td>GET /api/v1/market-signals?instrument=NIFTY&amp;periods=5</td><td>Market (s2), Signal Hero (s3), Today (s5), Market Feed (s7)</td></tr>
    <tr><td>fetchPerformance()</td><td>GET /api/v1/performance-summary</td><td>Goal (s1), Strategy (s4), Overview (s6)</td></tr>
    <tr><td>fetchPortfolioSummary()</td><td>GET /api/v1/portfolio/summary</td><td>Market (s2), Signal Hero (s3), Portfolio (s8)</td></tr>
    <tr><td>fetchPositions()</td><td>GET /api/v1/portfolio/positions?mode=paper</td><td>Portfolio (s8)</td></tr>
    <tr><td>fetchPriceHistory()</td><td>GET /api/v1/portfolio/price-history?periods=30</td><td>Sparklines on Portfolio (s8)</td></tr>
    <tr><td>fetchTradeEvents()</td><td>GET /api/v1/trade-events</td><td>Strategy (s4) — last 4 trade decisions</td></tr>
  </tbody>
</table>
<p>The Live toggle (<code>#liveToggle</code>) persists state to <code>localStorage</code>.
When toggled on, <code>initLiveData()</code> fetches all sources in parallel and binds each screen.
When toggled off, the background color resets and all screens show hardcoded fallback values.</p>

<h3>Regime Background</h3>
<table>
  <thead><tr><th>Regime</th><th>Background color</th></tr></thead>
  <tbody>
    <tr><td>Bull</td><td><code>#EDFAF3</code> (light green)</td></tr>
    <tr><td>Neutral / unknown</td><td><code>#FEFCE8</code> (light yellow)</td></tr>
    <tr><td>Bear</td><td><code>#FFF7ED</code> (light amber)</td></tr>
  </tbody>
</table>
<p>Body background transitions smoothly (<code>transition: background-color 0.6s ease</code>)
when the regime changes.</p>

<h3>Signal Thresholds (client-side)</h3>
<table>
  <thead><tr><th>Signal type</th><th>Condition</th></tr></thead>
  <tbody>
    <tr><td>Momentum</td><td>rsi_14 &gt; 60</td></tr>
    <tr><td>Trend</td><td>trend_score &gt; 0.6</td></tr>
    <tr><td>Volatility</td><td>atr_14 &gt; average of last 5 rows</td></tr>
    <tr><td>Reversal</td><td>bb_pct_b &gt; 0.85 or bb_pct_b &lt; 0.15</td></tr>
  </tbody>
</table>

<h3>Out of Scope (v1.0)</h3>
<ul>
  <li>iOS PWA — service worker limitations on iOS Safari</li>
  <li>Chat backend integration — the chat overlay is hardcoded UI only</li>
  <li>Home screen redesign — hardcoded placeholder; user will redesign later</li>
  <li>Bundler or external JS files — stays single-file by design</li>
</ul>
"""


if __name__ == "__main__":
    client = ConfluenceClient()
    print(f"Appending Mobile App section to Requirements [{PAGE_ID}]...")
    page_id, url = client.append_to_page(PAGE_ID, "Requirements", MOBILE_SECTION_HTML)
    print(f"  UPDATED [{page_id}]")
    print(f"  {url}")
