# Feature 30 — Engineering Context

This file is the hand-off brief for engineers picking up any phase of F30.
Read REQUIREMENTS.md first for the full design. This file contains implementation notes only.

---

## Key Files to Read Before Starting

| File | Why |
|---|---|
| `dashboard/js/fno/app-init.js` | The broken init chain that Phase 2 replaces |
| `dashboard/js/fno/state.js` | Shared state object — all modules read from this |
| `src/rita/api/experience/portfolio_hedge.py` | Black-Scholes functions to reuse in Phase 1 |
| `src/rita/api/experience/fno_hedge_plan.py` | Pattern for JWT-gated experience endpoint |
| `src/rita/api/experience/rita.py` | `geography_overview()` — contains `ann_vol_pct`, `return_1y_pct`, `risk_score` per instrument |
| `src/rita/repositories/user_portfolio.py` | How to load the user's saved holdings |
| `src/rita/repositories/user_hedge_plan.py` | How to load the user's saved hedge plan |
| `src/rita/repositories/market_data.py` | Latest OHLCV per instrument from `market_data_cache` table |

---

## C1 — Real Data Path: Loading Portfolio + Hedge Plan

```python
# 1. Resolve key_id from JWT
key_id = current_user.id   # same pattern as fno_hedge_plan.py

# 2. Load portfolio
portfolio = UserPortfolioRepo(db).find_by_key_id(key_id)
if not portfolio:
    raise HTTPException(404, "No portfolio saved")

holdings = [HoldingItem(**h) if isinstance(h, dict) else h
            for h in (portfolio.holdings or [])]

# 3. Load hedge plan (optional — 404 is normal)
try:
    hedge_plan = UserHedgePlanRepo(db).find_by_key_id(key_id)
except:
    hedge_plan = None

hedged_ids   = set(hedge_plan.hedged_ids or []) if hedge_plan else set()
coverage_pct = hedge_plan.coverage if hedge_plan else 50
scenario_tab = hedge_plan.scenario_tab if hedge_plan else 'pp'
```

---

## C2 — Greek Computation Per Holding

Reuse `_compute_bs_price(S, K, T, r, sigma, option_type)` from `portfolio_hedge.py`.

For each holding in the portfolio:
- `S` = latest close price of the instrument (from market_data_cache)
- `K` = S × (1 - coverage_pct/100)  → ATM-ish put strike
- `T` = 1.0  (1 year duration, always)
- `r` = 0.05  (5% risk-free rate, same as portfolio_hedge.py)
- `sigma` = ann_vol_pct / 100  (from geography_overview computation)
- `option_type` = 'put' for put_buy, 'call' for call_sell

Greeks derivation:
```python
from scipy.stats import norm
import math

d1 = (math.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma * math.sqrt(T))
d2 = d1 - sigma * math.sqrt(T)

# Delta: long put = N(d1) - 1; long equity = 1.0
equity_delta = 1.0
put_delta    = norm.cdf(d1) - 1   # ≈ -0.5 for ATM
net_delta    = equity_delta + put_delta  if instrument in hedged_ids else equity_delta

# Theta (EUR/day): negative for long put (cost)
put_theta    = -(S * norm.pdf(d1) * sigma / (2 * math.sqrt(T))
                 + r * K * math.exp(-r*T) * norm.cdf(-d2)) / 365
theta_eur_day = put_theta * position_eur / S  if instrument in hedged_ids else 0.0

# Vega (EUR per 1% IV move)
vega_per_pct = S * norm.pdf(d1) * math.sqrt(T) * 0.01
vega_eur     = vega_per_pct * position_eur / S  if instrument in hedged_ids else 0.0

# Gamma
gamma = norm.pdf(d1) / (S * sigma * math.sqrt(T))
```

If `hedge_plan` is None or instrument not in `hedged_ids`: delta=1.0, gamma=0, theta=0, vega=0.

---

## C3 — Scenario Computation

σ-anchored moves: ±2σ, ±1σ, flat. For each holding, portfolio P&L = position_eur × move.

```python
SCENARIO_SIGMAS = [-2.0, -1.0, 0.0, 1.0, 2.0]

for sigma_mult in SCENARIO_SIGMAS:
    portfolio_pnl = 0.0
    for h in holdings:
        ann_vol  = instruments[h.instrument_id]['ann_vol_pct'] / 100
        move_pct = sigma_mult * ann_vol          # e.g. -1σ for NIFTY = -0.184
        pos_eur  = h.allocation_pct / 100 * total_value_eur
        portfolio_pnl += pos_eur * move_pct
    # ... build scenario_levels entry
```

`scenario_levels` shape for frontend (matches what `rr.js` reads):
```json
{
  "NIFTY": { "target": 26400, "sl": 21900 },
  "BANKNIFTY": { "target": 57700, "sl": 46500 }
}
```
`target` = spot × (1 + 1σ), `sl` = spot × (1 - 2σ). Only include instruments in `market` data.

---

## C4 — Payoff Grid

20-point price grid from spot × 0.70 to spot × 1.30 (±30% range).
For each grid point, compute:
- `unhedged_value` = total_value_eur × (grid_price / spot_proxy)
  where `spot_proxy` = weighted average of all instrument prices
- `hedged_value` = unhedged_value with put protection applied:
  If instrument is hedged and grid_price drops below strike, add
  `position_eur × max(0, strike_pct - grid_pct)` as protection gain

Keep it simple for v1: use the **aggregate portfolio** move rather than per-instrument.

```python
spot_ref   = 1.0  # normalised
grid       = [spot_ref * (0.70 + i * 0.03) for i in range(21)]  # 0.70..1.30
unhedged   = [total_value_eur * g for g in grid]
hedged     = []
for g in grid:
    drop = max(0, spot_ref - g)  # downside from current
    hedge_gain = (coverage_pct / 100) * hedged_alloc_eur * drop if drop > 0 else 0.0
    hedged.append(total_value_eur * g + hedge_gain)

payoff = {
    "portfolio": { "labels": [round(g * 100 - 100, 1) for g in grid],  # % move
                   "data":   [round(v - total_value_eur) for v in unhedged] },
    "hedged":    { "labels": [round(g * 100 - 100, 1) for g in grid],
                   "data":   [round(v - total_value_eur) for v in hedged] }
}
```

---

## C5 — Stress Scenarios

Five hardcoded events. Applied as a uniform portfolio move (all instruments drop/rise by the same %).

```python
STRESS_EVENTS = [
    {"label": "2008 Crisis",    "move_pct": -50},
    {"label": "COVID-2020",     "move_pct": -35},
    {"label": "Rate Hike 2022", "move_pct": -20},
    {"label": "Tech Rally",     "move_pct": +25},
    {"label": "India Slowdown", "move_pct": -15},
]

stress_output = []
for ev in STRESS_EVENTS:
    move       = ev["move_pct"] / 100
    unh_pnl    = total_value_eur * move
    # Hedged: protection kicks in on downside only
    hedge_gain = 0.0
    if move < 0 and hedged_alloc_eur > 0:
        hedge_gain = hedged_alloc_eur * abs(move) * (coverage_pct / 100) * 0.5
        # 0.5 = partial protection (put only covers extreme tail, not full move)
    stress_output.append({
        "label":             ev["label"],
        "move_pct":          ev["move_pct"],
        "portfolio_pnl_eur": round(unh_pnl),
        "hedged_pnl_eur":    round(unh_pnl + hedge_gain),
    })
```

Frontend `stress.js` will need updating to read from `state.stressData` (new array format) instead of computing from `state.greeksData`. See Phase 5 notes.

---

## C6 — Hedge Quality Score (HQS)

Score 0–100 per instrument. Three components:

| Component | Max pts | Logic |
|---|---|---|
| Is hedged | 40 | 40 if instrument in hedged_ids, else 0 |
| Cost vs risk | 30 | 30 if put_cost_pct < ann_vol_pct × 0.5 (cheap relative to risk), 15 if < ann_vol_pct × 1.0, else 5 |
| Coverage match | 30 | 30 if coverage_pct 40–70% (balanced), 15 if 20–40% or 70–90%, 5 if <20% or >90% |

HQS tier: green ≥ 70, yellow 40–69, red < 40.

---

## C7 — Frontend initApp Replacement

Replace `app-init.js:initApp()` with:

```js
export async function initApp() {
  const token = sessionStorage.getItem('auth_token');
  const mode  = state.portfolioMode || sessionStorage.getItem('fno_portfolio_mode') || 'real';

  try {
    const headers = (mode === 'real' && token) ? { Authorization: `Bearer ${token}` } : {};
    const resp = await fetch(apiBase() + `/api/v1/experience/fno/portfolio-analytics?mode=${mode}`, { headers });

    if (resp.status === 404 && mode === 'real') {
      // No portfolio saved — fall back to mock
      state.portfolioMode = 'mock';
      sessionStorage.setItem('fno_portfolio_mode', 'mock');
      _showBanner('No portfolio saved — showing demo data. Build yours in Portfolio Builder →');
      return initApp();  // recurse once
    }
    if (!resp.ok) throw new Error(`API ${resp.status}`);

    const d = await resp.json();
    state.portfolioMeta   = d.portfolio_meta || {};
    state.marketData      = d.market         || {};
    state.positions       = d.positions      || [];
    state.greeksData      = d.greeks         || [];
    state.closedPositions = d.closed_positions || [];
    state.realizedPnl     = d.realized_pnl   || 0;
    state.portDelta       = d.net_delta      || {};
    state.netGreeks       = d.net_greeks     || {};
    state.scenarioLevels  = d.scenario_levels || {};
    state.marginData      = d.margin         || {};
    state.stressData      = d.stress         || [];
    state.payoffData      = d.payoff         || {};
    state.hedgeQuality    = d.hedge_quality  || {};

    const asOf = d.portfolio_meta?.updated_at || '';
    document.getElementById('sidebar-as-of').textContent = asOf
      ? `Updated ${new Date(asOf).toLocaleDateString()}` : '';

  } catch (e) {
    console.error('Portfolio analytics error:', e);
    document.getElementById('sidebar-as-of').textContent = 'API error — check server';
  }

  // Render all sections (unchanged)
  buildExpiryPills();
  renderDashboard();
  renderPositionsKpis();
  renderPositionsTable();
  renderClosedPositions();
  renderMarginKpis();
  updateMarginSections();
  renderMarginTables();
  updateRiskSections();
  renderGreeksCards();
  renderGreeksTable();
  renderStressScenarios();
  renderScenarios();
  renderPayoffChart();
  renderHedgeRadar();
  initManoeuvre();
}
```

Key removals vs current `initApp()`:
- No `fetchPositions()` call
- No `loadEquityHedge(false)` call
- No `rita:asml-state-updated` event listener
- No `saveToday()` / `syncPriceHistory()` (NIFTY/BANKNIFTY F&O daily tracking — remove or move to optional)

---

## C8 — Mock Data Structure

The mock data module should be a Python dict constant at the top of `portfolio_analytics.py`:

```python
MOCK_PORTFOLIO = {
    "mode": "mock",
    "portfolio_meta": {
        "name": "Demo Portfolio",
        "total_value_eur": 50000,
        "updated_at": "2026-01-01T00:00:00"
    },
    "market": {
        "NIFTY":     {"close": 24200, "chgFromOpen": 0.8,  "date": "2026-01-01", "open": 24000, "high": 24300, "low": 23900, "prevClose": 23800, "chgFromPrev": 1.7, "shares": "—", "turnover": 0},
        "BANKNIFTY": {"close": 52100, "chgFromOpen": -0.3, "date": "2026-01-01", "open": 52260, "high": 52500, "low": 51800, "prevClose": 51900, "chgFromPrev": 0.4, "shares": "—", "turnover": 0},
        "ASML":      {"close": 890.5, "chgFromOpen": 1.2,  "date": "2026-01-01", "open": 880.0, "high": 895.0, "low": 875.0, "prevClose": 870.0, "chgFromPrev": 2.4, "shares": "—", "turnover": 0, "currency": "EUR"},
        "NVIDIA":    {"close": 132.4, "chgFromOpen": 2.1,  "date": "2026-01-01", "open": 129.5, "high": 133.0, "low": 128.0, "prevClose": 128.0, "chgFromPrev": 3.4, "shares": "—", "turnover": 0, "currency": "USD"},
        "TRU":       {"close": 18.2,  "chgFromOpen": 0.4,  "date": "2026-01-01", "open": 18.1,  "high": 18.5,  "low": 17.9,  "prevClose": 17.8,  "chgFromPrev": 2.2, "shares": "—", "turnover": 0, "currency": "EUR"},
    },
    # ... positions, greeks, stress, payoff, hedge_quality, scenario_levels
    # pre-computed for the 5-instrument demo; see REQUIREMENTS.md mock table
}
```

---

## C9 — Real/Mock Toggle UI

The toggle matches the existing Paper/Live button in the FnO sidebar. Add to `fno.html` near `#sidebar-as-of`:

```html
<div class="mode-toggle" style="margin-top:8px;display:flex;gap:4px;">
  <button id="btn-mode-real" class="mode-pill active" onclick="fnoSetPortfolioMode('real')">Real</button>
  <button id="btn-mode-mock" class="mode-pill"        onclick="fnoSetPortfolioMode('mock')">Demo</button>
</div>
```

In `main.js`:
```js
window.fnoSetPortfolioMode = async (mode) => {
  state.portfolioMode = mode;
  sessionStorage.setItem('fno_portfolio_mode', mode);
  document.getElementById('btn-mode-real').classList.toggle('active', mode === 'real');
  document.getElementById('btn-mode-mock').classList.toggle('active', mode === 'mock');
  await initApp();
};
```

On page load, read `sessionStorage('fno_portfolio_mode')` to set initial active button state.

---

## C10 — Stress.js Update (Phase 5)

Current `computeFilteredStress()` in `stress.js` computes from `state.greeksData` × spot × move.
After Phase 5, it reads from `state.stressData` directly.

Replace the function body:
```js
export function computeFilteredStress() {
  // state.stressData is now an array from the endpoint:
  // [{ label, move_pct, portfolio_pnl_eur, hedged_pnl_eur }, ...]
  return state.stressData.map(s => ({
    move_pct:           s.move_pct,
    move_label:         (s.move_pct > 0 ? '+' : '') + s.move_pct + '%',
    label:              s.label,
    pnl:                s.portfolio_pnl_eur,
    hedged_pnl:         s.hedged_pnl_eur,
    nifty_level:        null,   // not applicable for portfolio view
  }));
}
```

`renderStressScenarios()` will also need to add a second P&L column for `hedged_pnl`.

---

## Known Gotchas

| # | Note |
|---|---|
| G1 | `HoldingItem(**h) if isinstance(h, dict)` pattern is required when reading `portfolio.holdings` — the JSON column may return dicts or objects depending on SQLAlchemy version. See `portfolio_hedge.py` for the pattern. |
| G2 | `ann_vol_pct` is not stored in the `user_portfolio` table. It must be computed from the market data CSVs via the same code path as `geography_overview()` in `experience/rita.py`. Factor this out to avoid duplication. |
| G3 | `UserHedgePlanRepo.find_by_key_id()` returns `None` when no plan exists — handle this gracefully; all greeks default to equity delta=1.0 when no hedge plan is present. |
| G4 | Mock mode must not call `get_current_user()` — no JWT needed. Route must not use `Depends(get_current_user)` when `mode=mock`. Use an optional dependency or check mode before verifying token. |
| G5 | `equity_hedge.js` `injectAsmlToState()` is still importable but must no longer be called from `app-init.js`. It can stay in the file for potential future use (e.g., equity hedge standalone section). Remove only the call site in `initApp()`. |
| G6 | `buildExpiryPills()` in `nav.js` iterates `state.positions` looking for `.exp` values. After Phase 3, positions will have `exp='EQUITY'` for all holdings. Ensure `buildExpiryPills()` handles this gracefully (either hide the pills for equity mode or show a single "EQUITY" pill). |
