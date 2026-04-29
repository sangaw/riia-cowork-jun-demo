---
description: Add or update a feature in the RITA main dashboard (rita.html + dashboard/js/rita/)
---

You are an Engineer agent adding or updating a feature in the RITA main dashboard.

**Task:** $ARGUMENTS

---

## Module Map — `dashboard/js/rita/`

| File | Responsibility | Key exports |
|---|---|---|
| `api.js` | HTTP client | `api(path, method?, body?)` |
| `utils.js` | DOM helpers | `setEl(id, html)`, `badge(status)`, `fmt(v, dec)`, `fmtPct(v)` |
| `charts.js` | Chart.js registry | `mkChart(id, config)`, `destroyChart(id)`, `C` (palette), `chartOpts()` |
| `nav.js` | Section navigation | `show(section)`, `_sectionLoaders` map |
| `main.js` | Entry point | Registers `_sectionLoaders`, binds `window.*` |
| `health.js` | Home KPIs + model status | `loadHealth()`, `loadMetrics()`, `loadPerfSummary()`, `loadDrift()` |
| `market-signals.js` | Market Signals + tabs | `loadMarketSignals()`, `switchMsTab(tf)` |
| `trades.js` | Trade Journal | `loadTrades()`, `downloadTradeJournal()` |
| `observability.js` | Ops monitoring panel | `loadObservability()` |
| `scenarios.js` | Backtest runner | `loadScenarios()`, `runScenarioBacktest()` |
| `export.js` | Pipeline step buttons | `runGoal()`, `runMarket()`, `runStrategy()` |
| `pipeline.js` | Pipeline result renderers | `renderGoalResult()`, `renderMarketResult()` |
| `performance.js` | Performance charts | `loadPerformance()` |
| `risk.js` | Live risk view | `loadRisk()` |
| `training.js` | Training progress | `loadTrainProgress()` |
| `chat.js` | Chat assistant | `sendChatMsg()`, `useChip()` |
| `agent-panel.js` | LangGraph 6-agent sim | `loadAgentPanel()`, `agentPanelStep()` |
| `ai-compliance.js` | AI Compliance panel | `loadAiCompliance()`, `switchAcTab()` |

**Read only the file(s) you need to modify — do not read all files.**

---

## Adding a New Section — 4-Step Checklist

1. **HTML** — add `<section id="sec-NAME" class="section">` to `rita.html`
2. **JS loader file** — create `dashboard/js/rita/my-feature.js` with `export function loadMyFeature() { ... }`
3. **Register in `main.js`** — `import { loadMyFeature } from './my-feature.js'; _sectionLoaders['NAME'] = loadMyFeature;`
4. **`window.*` binding** — in `main.js`, add `window.loadMyFeature = loadMyFeature;` for any refresh button

Section id in HTML is `sec-NAME`. The loader key is `NAME` (without the `sec-` prefix).

---

## KPI Card Pattern

```js
import { setEl, badge, fmt, fmtPct } from './utils.js';
import { api } from './api.js';

export async function loadMyFeature() {
    try {
        const data = await api('/api/v1/my-endpoint');
        setEl('my-kpi-value', fmt(data.some_number, 2));
        setEl('my-kpi-status', badge(data.status));
        setEl('my-pct', fmtPct(data.pct_value));
    } catch (e) {
        console.warn('[my-feature] load failed', e);
    }
}
```

- `fmt(v, dec)` — formats a number; returns `'—'` if null
- `fmtPct(v)` — formats as percentage; returns `'—'` if null
- `badge(status)` — returns a coloured `<span>` for `ok/warn/error/bull/bear`
- **Always** wrap in `try/catch` — log with `console.warn`, never swallow silently

---

## Chart Pattern

```js
import { mkChart, C, chartOpts } from './charts.js';

// Always use mkChart — it destroys the previous instance automatically
mkChart('chart-my-id', {
    type: 'line',
    data: {
        labels: data.map(r => r.date),
        datasets: [{
            label: 'My Series',
            data: data.map(r => r.value),
            borderColor: C.run,
            backgroundColor: C.run + '22',
        }]
    },
    options: chartOpts('My Series', v => fmt(v, 2), data.map(r => r.date))
});
```

**Color palette `C`:**

| Key | Use |
|---|---|
| `C.run` | Primary line (portfolio / main metric) |
| `C.build` | Positive / bullish |
| `C.warn` | Warning / neutral |
| `C.danger` | Negative / bearish |
| `C.mon` | Model / monitoring |
| `C.t3` | Muted label text |

- Never patch an existing Chart.js instance — always call `mkChart()` which recreates it
- Canvas element `id` in HTML must match the `id` passed to `mkChart()`

---

## Table Pattern

```js
const rows = data.map(r => `
    <tr>
        <td>${r.date}</td>
        <td>${fmt(r.value, 2)}</td>
        <td>${badge(r.status)}</td>
    </tr>
`).join('');
setEl('my-table-body', rows);
```

---

## API Communication

```js
// GET
const data = await api('/api/v1/my-endpoint?param=value');

// POST
const result = await api('/api/v1/my-action', 'POST', { key: 'value' });
```

- Base URL from `window.RITA_API_BASE` — **never** hardcode `http://localhost:8000`
- `api()` throws on non-2xx — always wrap in `try/catch`

---

## API Contract Check (mandatory if endpoint exists)

Before writing the JS consumer, grep for the endpoint handler and verify every field:

```
grep -r "my-endpoint" riia-jun-release/src/rita/api/
```

List every field the JS reads (`data.fieldName`, `r.key`, etc.) and confirm each is present in the handler's `return` dict. Missing fields silently become `undefined` → UI shows `—` or `NaN`.

---

## Window Binding (required for all `onclick=""` handlers)

In `main.js`:
```js
window.myFunction = myFunction;
window.myOtherFn  = myOtherFn;
```

ES modules are scoped — HTML `onclick="foo()"` fails unless `window.foo` is set.

---

## Known Gotchas

| Gotcha | Detail |
|---|---|
| `parseFloat(null)` → NaN | Guard: `v !== null ? parseFloat(v).toFixed(2) : '—'` |
| Silent `catch (_) {}` | Always: `catch (e) { console.warn('[module] failed', e); }` |
| Section loaders fire once | `nav.js` fires on first visit. Force reload: call the loader directly, e.g. `window.loadMyFeature()` |
| Wrong element id | Before writing `setEl('id', ...)`, grep the HTML to confirm that exact `id` exists |
| `macd_signal` naming differs | `/api/v1/market-signals` → `macd_signal` (number); `POST /api/v1/market` → `macd_signal` (string label) + `macd_signal_line` (number) |

---

## Files to Touch

| File | Action |
|---|---|
| `dashboard/js/rita/my-feature.js` | Create — loader function |
| `dashboard/js/rita/main.js` | Edit — import, `_sectionLoaders`, `window.*` |
| `dashboard/rita.html` | Edit — add `<section id="sec-NAME">` and nav link |
| `src/rita/api/<tier>/my_endpoint.py` | Create/edit — if new API endpoint needed |
| `src/rita/main.py` | Edit — `include_router(...)` if new router |
| `Specs/Spec_JS_Code.md` | Edit — add row to module map |
| `Specs/Spec_Python_Code.md` | Edit — add row to API table if contract changed |

---

## Definition of Done

- [ ] New section renders without console errors
- [ ] Every `setEl('id', ...)` has a matching element in `rita.html`
- [ ] Every field read from API response confirmed present in handler's `return` dict
- [ ] `window.*` binding added in `main.js` for all `onclick` handlers
- [ ] `_sectionLoaders['NAME']` registered in `main.js`
- [ ] `try/catch` present in every async loader — no silent swallows
- [ ] `Specs/Spec_JS_Code.md` module map updated if new file added
- [ ] `Specs/Spec_Python_Code.md` updated if new API endpoint added
