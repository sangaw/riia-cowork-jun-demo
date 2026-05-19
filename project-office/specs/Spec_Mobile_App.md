# RITA Mobile App — Specification

High-density reference for AI agents working on the RITA mobile PWA.

**File:** `riia-jun-release/mobileapp/index.html`
**Type:** Single-file Progressive Web App (PWA) — 1,311+ lines
**Platform target:** Android Chrome (installable via manifest.json)

---

## 1. Architecture

| Decision | Detail |
|---|---|
| Single file | All HTML, CSS, and JS in `index.html` — no bundler, no external JS files |
| PWA | `manifest.json` + `sw.js` (service worker) — installable on Android |
| Live data | Toggle-gated — `LIVE_MODE = localStorage.getItem('ritaLiveMode') === 'true'` |
| Fallback | Every API call silently falls back to hardcoded DOM values on failure — app never breaks |
| Backend URL | `API_BASE = 'http://localhost:8000'` (hardcoded constant) — change for production |
| Chat | Hardcoded overlay — no backend API connection |
| Home screen | Hardcoded — user will redesign later |

---

## 2. 10 App Screens

| ID | Screen name | Description |
|---|---|---|
| s0 | Home | Avatar, greeting, RITA SAYS banner, Live toggle |
| s1 | Goal | YTD return radial ring, Sharpe, Win Rate |
| s2 | Market | Timeframe tabs (Daily/Weekly/Monthly) + 8-KPI grid (RSI-14, MACD, BB %B, ATR-14, EMA5, EMA13, EMA26, Trend) + Signal highlights + Price & Volume SVG chart |
| s3 | Signal Hero | Active signal types, regime, confidence |
| s4 | Strategy | P&L, Win Rate, Sharpe, trade decisions list |
| s5 | Today | Date hero, regime card, NIFTY price, signal type rows |
| s6 | Overview | Market hero price, goal progress bar, signal previews |
| s7 | Market Feed | Regime pill, factor bars, narrative paragraph |
| s8 | Portfolio | Total value, daily gain, holdings list + sparklines |
| overlay | Portfolio overlay | Detailed holdings with sparklines |

Navigation: `goTo(screenIndex)` — slides left/right between screens.

---

## 3. API Client Functions (6 total)

All functions return `null` on failure (never throw). Callers check `if (!data) return`.

```js
// ── Config ───────────────────────────────────────────────────────────────────
const API_BASE  = 'http://localhost:8000';
let   LIVE_MODE = localStorage.getItem('ritaLiveMode') === 'true';

// ── API client ───────────────────────────────────────────────────────────────
async function fetchTimeline()        // GET /api/v1/risk-timeline
async function fetchSignals()         // GET /api/v1/market-signals?instrument=NIFTY&periods=5
async function fetchPerformance()     // GET /api/v1/performance-summary
async function fetchPortfolioSummary()// GET /api/v1/portfolio/summary
async function fetchPositions()       // GET /api/v1/portfolio/positions?mode=paper
async function fetchPriceHistory()    // GET /api/v1/portfolio/price-history?periods=30
async function fetchTradeEvents()     // GET /api/v1/trade-events
```

---

## 4. Live Data Coordinator (`initLiveData()`)

Called when app starts (if LIVE_MODE) and when Live toggle is turned on.

```js
async function initLiveData() {
  if (!LIVE_MODE) return;
  const [timeline, signals, perf, portSummary] = await Promise.all([
    fetchTimeline(), fetchSignals(), fetchPerformance(), fetchPortfolioSummary()
  ]);
  applyRegime(timeline);           // body background color
  bindGoalScreen(perf);            // s1
  bindMarketScreen(signals, portSummary);   // s2
  bindSignalHero(signals, portSummary);     // s3
  bindStrategyScreen(perf, events);         // s4 (events fetched separately)
  bindTodayScreen(timeline, signals, portSummary, perf);   // s5
  bindOverviewScreen(timeline, signals, portSummary, perf); // s6
  bindMarketFeedScreen(timeline, signals);  // s7
  const [positions, priceHistory] = await Promise.all([fetchPositions(), fetchPriceHistory()]);
  bindPortfolioScreen(positions, portSummary, priceHistory); // s8
}
```

---

## 5. Regime Background Colors

```js
function applyRegime(timeline) {
  const regime = timeline[timeline.length - 1].regime || '';
  const colors  = { Bull: '#EDFAF3', Bear: '#FFF7ED' };
  const color   = colors[regime] || '#FEFCE8';  // Neutral / unknown → light yellow
  document.body.style.backgroundColor = color;
}
```

| Regime | Color | CSS Variable |
|---|---|---|
| Bull | `#EDFAF3` | `--regime-bull` |
| Neutral (default) | `#FEFCE8` | `--regime-neutral` |
| Bear | `#FFF7ED` | `--regime-bear` |

Body has `transition: background-color 0.6s ease` for smooth regime transitions.

---

## 6. Signal Threshold Logic (Client-side)

Derived from the latest row of `GET /api/v1/market-signals?instrument=NIFTY&periods=5`:

```
Momentum   → rsi_14 > 60
Trend      → trend_score > 0.6
Volatility → atr_14 > average of last 5 rows' atr_14
Reversal   → bb_pct_b > 0.85 or bb_pct_b < 0.15
```

Display format: `"Momentum · Trend · 2 active"` — signal type labels only, no timestamps.

---

## 7. Screen Binding Functions

| Function | Source data | DOM bindings |
|---|---|---|
| `bindGoalScreen(perf)` | `performance-summary` | YTD % text, radial ring dashoffset, Sharpe, Win Rate |
| `bindMarketScreen(signals, portSummary, timeline)` | `market-signals`, `portfolio/summary`, `risk-timeline` | Regime label (`s2-regime-label`), price hero (`s2-price-hero`, `s2-price-change`), Signal Hero (s3) — KPI grid populated separately by `loadMsSignals()` |
| `bindSignalHero(signals, portSummary)` | `market-signals`, `portfolio/summary` | Confidence, regime, instrument, signal headline |
| `bindStrategyScreen(perf, events)` | `performance-summary`, `trade-events` | P&L, Win Rate, Sharpe, last 4 trade decisions |
| `bindTodayScreen(timeline, signals, portSummary, perf)` | all 4 | Date string, regime card, NIFTY price, signal type rows |
| `bindOverviewScreen(...)` | all 4 | Market hero price, goal bar, signal previews |
| `bindMarketFeedScreen(timeline, signals)` | timeline, signals | Regime pill, factor bars, narrative paragraph |
| `bindPortfolioScreen(positions, portSummary, priceHistory)` | positions, summary, history | Total value, daily gain, holdings list, sparklines |

---

## 8. Factor Bar Mapping

Market screen (s2) and Market Feed (s7) use 4 factor bars derived from the latest `market-signals` row:

```
Momentum bar  = rsi_14 / 100
Value bar     = 1 - bb_pct_b          (low BB position = value)
Quality bar   = trend_score            (normalized to [0,1])
Volatility bar = atr_14 / close_price  (normalized, capped at 1)
```

---

## 9. Sparkline Generation

Portfolio holdings (s8) use SVG polylines derived from `price-history` data:

```js
function pricesToPolyline(prices, w=200, h=60) {
  const min = Math.min(...prices), max = Math.max(...prices);
  return prices.map((p, i) =>
    `${(i/(prices.length-1)*w).toFixed(1)},${(h - (p-min)/(max-min)*h).toFixed(1)}`
  ).join(' ');
}
```

---

## 10. Live Toggle

DOM: `#liveToggle` (42×24px rounded div) + `#liveToggleKnob` + `#liveStatusDot`

```js
function toggleLiveMode() {
  LIVE_MODE = !LIVE_MODE;
  localStorage.setItem('ritaLiveMode', LIVE_MODE);
  updateToggleUI();
  if (LIVE_MODE) initLiveData();
  else document.body.style.backgroundColor = '';  // reset to CSS --bg
}
function updateToggleUI() {
  // Green (#1A6B3C) when ON, grey (#D0CBBC) when OFF
  // Knob slides: translateX(18px) ON, translateX(0) OFF
  // Dot: #4ADE80 (green) ON, #B8B2A6 (grey) OFF
}
// On load: updateToggleUI() to reflect persisted state
```

---

## 11. Trade Decisions List (Strategy screen s4)

Source: `GET /api/v1/trade-events` — last 4 entries displayed as:
```
{date (no time)} · {event_type} · {instrument}
```
Example: `"24 Apr · entry · NIFTY"`

---

## 12. PWA Files

| File | Purpose |
|---|---|
| `index.html` | App — all HTML, CSS, JS |
| `manifest.json` | PWA metadata (name, icons, theme_color, display=standalone) |
| `sw.js` | Service worker — offline caching |
| `icons/icon.svg` | Source icon (vector) |
| `icons/generate-icons.html` | Helper to generate PNG icons from SVG |

---

## 13. Integration Status

All 10 integration steps are complete:

| Step | Description | Status |
|---|---|---|
| 1 | CSS regime color tokens + body transition | Done |
| 2 | Config block + API client module | Done |
| 3 | Regime fetch + body background color | Done |
| 4 | Live toggle switch on Home screen | Done |
| 5 | Goal screen (s1) data binding | Done |
| 6 | Market (s2) + Signal Hero (s3) data binding | Done |
| 7 | Today (s5) + Overview (s6) data binding | Done |
| 8 | Market Feed (s7) data binding | Done |
| 9 | Strategy screen (s4) data binding | Done |
| 10 | Portfolio (s8 + overlay) + sparklines | Done |

---

## 14. AI Agent Directives

1. **Single file** — all changes go into `index.html`. No new `.js` or `.css` files.
2. **Fallback required** — every API binding must check `if (!data) return` before accessing fields.
3. **No new APIs** — use only existing backend endpoints listed in Section 3.
4. **`API_BASE` constant** — never hardcode the URL in individual functions; always prefix with `API_BASE`.
5. **`LIVE_MODE` check** — never call API functions if `LIVE_MODE` is false; respect the toggle.
6. **SVG sparklines** — use `pricesToPolyline()` helper, not Chart.js (too heavy for mobile).
7. **Factor bars** — use the threshold mapping in Section 8 exactly; do not invent new signal logic.
8. **No timestamps on signals** — display signal type labels only (e.g. "Momentum · Trend").
