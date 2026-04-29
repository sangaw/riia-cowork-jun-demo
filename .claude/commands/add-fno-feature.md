---
description: Add or update a feature in the FnO dashboard (fno.html + dashboard/js/fno/)
---

You are an Engineer agent adding or updating a feature in the RITA FnO (Futures & Options) dashboard.

**Task:** $ARGUMENTS

---

## Module Map — `dashboard/js/fno/`

| File | Responsibility | Key exports |
|---|---|---|
| `api.js` | FnO HTTP client | `api(path, method?, body?)` |
| `state.js` | Shared FnO state | `state` object (active group, instrument, expiry, etc.) |
| `utils.js` | DOM helpers | `setEl(id, html)`, `badge(status)`, `fmt(v, dec)`, `fmtPct(v)` |
| `nav.js` | Section navigation | `show(section)`, `_sectionLoaders` map |
| `main.js` | Entry point | Registers loaders, binds `window.*` |
| `dashboard.js` | FnO overview KPI cards | `loadFnoDashboard()` |
| `positions.js` | Open positions table | `loadPositions()` |
| `greeks.js` | Greeks calculator | `loadGreeks()`, `calculateGreeks()` |
| `margin.js` | Margin tracker | `loadMargin()` |
| `payoff.js` | Payoff diagram | `loadPayoff()` |
| `stress.js` | Stress test section | `loadStress()` |
| `rr.js` | Risk-Reward chart | `loadRR()` |
| `hedge.js` | Hedge Radar section | `loadHedge()` |
| `manoeuvre.js` | Manoeuvre section | `loadManoeuvre()` |

**Read only the file(s) you need to modify — do not read all files.**

---

## Shared FnO State (`state.js`)

All FnO modules share a single `state` object. Import it before reading any user-selected instrument or group:

```js
import { state } from './state.js';

// state.activeGroup     — current instrument group selected in UI
// state.activeInstrument — currently selected instrument (NIFTY/BANKNIFTY/ASML/NVIDIA)
// state.activeExpiry    — selected expiry date
// state.mode            — 'paper' | 'live'
```

Use `state.*` instead of reading DOM elements directly for the current selection.

---

## Adding a New Section — 4-Step Checklist

1. **HTML** — add `<section id="sec-NAME" class="section">` to `fno.html`
2. **JS loader file** — create `dashboard/js/fno/my-feature.js` with `export function loadMyFeature() { ... }`
3. **Register in `main.js`** — `import { loadMyFeature } from './my-feature.js'; _sectionLoaders['NAME'] = loadMyFeature;`
4. **`window.*` binding** — in `main.js`, add `window.loadMyFeature = loadMyFeature;` for any refresh/calculate button

---

## KPI Card Pattern

```js
import { setEl, badge, fmt, fmtPct } from './utils.js';
import { api } from './api.js';
import { state } from './state.js';

export async function loadMyFeature() {
    try {
        const data = await api(`/api/v1/fno/my-endpoint?instrument=${state.activeInstrument}`);
        setEl('my-kpi-value', fmt(data.some_number, 2));
        setEl('my-kpi-status', badge(data.status));
    } catch (e) {
        console.warn('[fno/my-feature] load failed', e);
    }
}
```

---

## FnO-Specific Rules

**Lot sizes — never hardcode:**
```js
// Wrong
const lots = qty / 75;

// Correct — read from API response or settings
const lotSize = data.lot_size;  // provided by /api/v1/portfolio/positions response
```
Lot sizes (NIFTY=75, BANKNIFTY=30) must come from `settings.instruments.*` in Python. The JS consumer reads them from the API response field `lot_size`.

**Greeks — always use the Experience Layer:**
Greeks calculations (`delta`, `gamma`, `theta`, `vega`) go through `/api/experience/greeks` — never reimplement Black-Scholes in JS.

**P&L display:** Use `fmt(v, 2)` for currency values. Green/red colouring: positive PnL → `C.build`, negative → `C.danger`.

**Instrument-aware API calls:** Most FnO endpoints accept `?instrument=` or `?mode=`. Always pass `state.activeInstrument` and `state.mode`.

---

## Chart Pattern (same as rita — uses Chart.js)

```js
// fno/ does not export charts.js — use inline Chart.js
const ctx = document.getElementById('chart-my-id').getContext('2d');
if (window._myChart) window._myChart.destroy();
window._myChart = new Chart(ctx, {
    type: 'line',
    data: { labels: [...], datasets: [{ ... }] },
    options: { responsive: true, ... }
});
```

Or if the module imports from a shared charts utility, use that pattern consistently with existing FnO charts.

---

## API Contract Check (mandatory)

```
grep -r "my-endpoint" riia-jun-release/src/rita/api/
```

Confirm every field the JS reads is present in the handler's `return` dict.

**Key FnO endpoints:**

| Endpoint | Consumer |
|---|---|
| `GET /api/v1/portfolio/summary` | `dashboard.js` — KPI cards |
| `GET /api/v1/portfolio/positions?mode=paper` | `positions.js` — positions table |
| `GET /api/v1/portfolio/price-history?periods=30` | `rr.js` — price chart |
| `GET /api/experience/greeks` | `greeks.js` |
| `GET /api/experience/fno/stress` | `stress.js` |

---

## Files to Touch

| File | Action |
|---|---|
| `dashboard/js/fno/my-feature.js` | Create — loader function |
| `dashboard/js/fno/main.js` | Edit — import, `_sectionLoaders`, `window.*` |
| `dashboard/fno.html` | Edit — add `<section id="sec-NAME">` and nav link |
| `src/rita/api/<tier>/my_endpoint.py` | Create/edit — if new API endpoint needed |
| `src/rita/main.py` | Edit — `include_router(...)` if new router |
| `Specs/Spec_JS_Code.md` | Edit — add row to fno module map |
| `Specs/Spec_Python_Code.md` | Edit — add row to API table if contract changed |

---

## Definition of Done

- [ ] New section renders without console errors
- [ ] Every `setEl('id', ...)` has a matching element in `fno.html`
- [ ] Every field read from API response confirmed present in handler's `return` dict
- [ ] No hardcoded lot sizes — `lot_size` comes from API response or `settings.instruments.*`
- [ ] `window.*` binding added in `main.js` for all `onclick` handlers
- [ ] `_sectionLoaders['NAME']` registered in `main.js`
- [ ] `try/catch` in every async loader — no silent swallows
- [ ] `Specs/Spec_JS_Code.md` updated if new module added
- [ ] `Specs/Spec_Python_Code.md` updated if new API endpoint added
