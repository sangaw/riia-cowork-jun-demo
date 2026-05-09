# Skill: Add FnO Dashboard Feature
**App:** FnO Options dashboard (`fno.html` + `dashboard/js/fno/`)
**Use for:** New UI sections, panels, or data views in the FnO portfolio/options dashboard
**Compiled from:** `Spec_RITA_App.md` + `Spec_JS_Code.md`

---

## App Identity

| Item | Value |
|---|---|
| HTML file | `riia-jun-release/dashboard/fno.html` — 3,500 lines. **Never read directly.** Use spec. |
| JS module dir | `riia-jun-release/dashboard/js/fno/` |
| Primary API | Portfolio tier: `riia-jun-release/src/rita/api/v1/portfolio.py` |
| Experience API | `riia-jun-release/src/rita/api/experience/fno.py` |
| Key tables | `positions`, `orders`, `snapshots`, `trades`, `manoeuvres`, `portfolio` |
| Spec file | `project-office/specs/Spec_RITA_App.md` |
| JS Spec file | `project-office/specs/Spec_JS_Code.md` |

---

## File Map — What to Touch for a Typical FnO UI Feature

| Layer | File | What to do |
|---|---|---|
| **Backend** | `src/rita/api/v1/portfolio.py` | Add endpoint for FnO data (no auth, heavy computation allowed) |
| **Backend** | `src/rita/api/experience/fno.py` | Add aggregated read-only payload if feature is UI-only read |
| **Backend** | `src/rita/schemas/{name}.py` | Add Pydantic response schema |
| **Backend** | `src/rita/services/portfolio_service.py` | Add business logic if computation is non-trivial |
| **Frontend** | `dashboard/js/fno/{name}.js` | Create new JS module with loader function |
| **Frontend** | `dashboard/js/fno/main.js` | Register section loader + bind window.* functions |
| **Frontend** | `dashboard/js/fno/state.js` | Add to shared state only if multiple modules need the value |
| **HTML** | `fno.html` | Add `<section id="sec-NAME">` with DOM elements |
| **Spec** | `project-office/specs/Spec_RITA_App.md` | Update Portfolio endpoint inventory + section description |

---

## FnO Module Reference (existing — do not duplicate)

| Existing module | What it already handles |
|---|---|
| `dashboard.js` | FnO overview KPI cards — `loadFnoDashboard()` → `GET /api/v1/portfolio/summary` |
| `positions.js` | Open positions table — `GET /api/v1/portfolio/positions?mode=paper\|live` |
| `greeks.js` | Greeks calculator — `loadGreeks()`, `calculateGreeks()` |
| `margin.js` | Margin tracker |
| `payoff.js` | Payoff diagram |
| `stress.js` | Stress test section |
| `rr.js` | Risk-Reward chart — `GET /api/v1/portfolio/price-history` |
| `hedge.js` | Hedge Radar section — `GET /api/v1/portfolio/hedge-history` |
| `manoeuvre.js` | Manoeuvre tracking — `GET /api/v1/portfolio/man-groups` + man-snapshot + man-pnl-history |

Before adding a new module, confirm the feature is not already covered by an existing one.

---

## Portfolio API Reference (existing endpoints — do not add duplicates)

| Endpoint | Method | Returns |
|---|---|---|
| `/api/v1/portfolio/overview` | GET | Cross-instrument normalised prices + correlation matrix |
| `/api/v1/portfolio/backtest` | POST | Multi-instrument DDQN portfolio backtest |
| `/api/v1/portfolio/positions?mode=` | GET | Paper or live positions |
| `/api/v1/portfolio/summary` | GET | KPI cards + market prices (nifty_spot, banknifty_spot, asml_close, nvidia_close) |
| `/api/v1/portfolio/price-history?periods=N` | GET | Recent NIFTY OHLCV |
| `/api/v1/portfolio/hedge-history` | GET | Historical hedge suggestions |
| `/api/v1/portfolio/man-groups` | GET | Manoeuvre group list |
| `/api/v1/portfolio/man-snapshot` | POST | Record snapshot when manoeuvre applied |
| `/api/v1/portfolio/man-pnl-history` | GET | Daily P&L history |
| `/api/v1/portfolio/man-daily-status` | GET | Today's manoeuvre count + last record |
| `/api/v1/portfolio/man-daily-snapshot` | POST | Record daily portfolio snapshot |

---

## Step-by-Step Task Rules

### Step 1 — Design the API Contract First
Define before writing code:
- Endpoint: method + path + query params
- Which FnO tables it reads (positions / orders / manoeuvres / portfolio)
- Response shape: field names + types as a Pydantic schema
- Frontend consumer: which JS module, which DOM element IDs

Write the contract in the task brief `[Architect] Design` section before proceeding.

### Step 2 — Choose the Right API Tier
- **Portfolio tier** (`portfolio.py`): FnO-specific computation, no auth required, may be heavy
- **Experience tier** (`fno.py`): Aggregated read-only UI payload, no auth, no commits
- **System tier**: Only for raw CRUD on FnO tables (positions, orders, manoeuvres)

### Step 3 — Add the Backend Endpoint

**Portfolio tier pattern:**
```python
@router.get("/api/v1/portfolio/my-feature", response_model=MyFeatureResponse)
def get_my_feature(db: Session = Depends(get_db)):
    service = PortfolioService(db)
    data = service.my_feature_calculation()
    return MyFeatureResponse(items=data)
```

**Key rules:**
- FnO tables: `positions`, `orders`, `snapshots`, `trades`, `manoeuvres`, `portfolio`
- Never read lot sizes from hardcoded values — read from `settings.instruments.*`
- `PortfolioService` and `ManoeuvreService` constructors require `db: Session`
- Background threads must open their own `SessionLocal()` — never pass request-scoped session

### Step 4 — Add the Pydantic Schema
File: `src/rita/schemas/{name}.py`
- Match field names exactly to what `fno/dashboard.js` will read
- Key existing field names to be aware of: `total_pnl`, `lot_count`, `nifty_spot`, `banknifty_spot`, `asml_close`, `nvidia_close`

### Step 5 — Write the JS Module
File: `dashboard/js/fno/{name}.js`

**Module template:**
```js
import { api } from './api.js';
import { setEl, badge, fmt, fmtPct } from './utils.js';
import { mkChart, C } from './charts.js';
import { state } from './state.js';    // only if you need shared FnO state

export async function loadMyFeature() {
  try {
    const data = await api('/api/v1/portfolio/my-feature');
    setEl('my-feature-value', fmt(data.value, 2));
  } catch (e) {
    setEl('my-feature-value', '—');
  }
}
```

**Rules (same as RITA):**
- Import `api` from `./api.js` — never raw `fetch()`
- Wrap API calls in `try/catch` — show `—` on error
- Use `setEl(id, html)` — never `document.getElementById(...).innerHTML`
- Use `mkChart(id, config)` — never `new Chart(...)`
- Use `C` color palette from `charts.js`
- No top-level `fetch()` or DOM queries
- Use `state` from `state.js` for active group/instrument if needed

### Step 6 — Register Section Loader in main.js
In `dashboard/js/fno/main.js`:
```js
import { loadMyFeature } from './my-feature.js';

_sectionLoaders['my-feature'] = loadMyFeature;
window.loadMyFeature = loadMyFeature;
```

### Step 7 — Update the Spec
File: `project-office/specs/Spec_RITA_App.md`
- Add the new endpoint to the Portfolio tier table in Section 3
- Add the new JS module to `Spec_JS_Code.md` Section 3 (FnO module structure)

**This step is mandatory. Do not mark the task complete without it.**

---

## Guardrails

| Rule | Detail |
|---|---|
| Never read `fno.html` directly | File is 3,500 lines. Use spec and HTML spec for nav/DOM patterns. |
| Never hardcode lot sizes | Read from `settings.instruments.*` |
| Never call `db.commit()` in Experience tier | Experience routes are read-only |
| Never use bare `pd.read_csv()` | Use `load_nifty_csv()` or `load_instrument_data()` from `core/data_loader.py` |
| Never add `print()` statements | Use `structlog` |
| Never hardcode `http://localhost:8000` in JS | Use `window.RITA_API_BASE` |
| Never call `new Chart(...)` directly | Use `mkChart(id, config)` from `charts.js` |
| Never expose ES module functions without `window.*` | `onclick=""` handlers silently fail |
| Never duplicate existing portfolio endpoints | Check the Portfolio API Reference table above first |
| Always update spec when contract changes | Spec drift breaks future agents |

---

## Definition of Done

Before marking this task complete, verify each item:

- [ ] **API contract matches** — Pydantic schema field names match JS `data.field` reads exactly
- [ ] **Correct tier used** — Portfolio for FnO computation, Experience for read-only aggregation
- [ ] **Section loader registered** — `_sectionLoaders['name'] = loadName` in `fno/main.js`
- [ ] **Window bindings set** — all `onclick` handlers on `window.*` in `fno/main.js`
- [ ] **Error handled** — `try/catch` in JS loader; shows `—` on failure
- [ ] **Spec updated** — endpoint added to `Spec_RITA_App.md` Portfolio tier; JS module added to `Spec_JS_Code.md` Section 3
- [ ] **Ruff passes** — `ruff check src/` returns no errors
- [ ] **No hardcoded values** — no localhost URLs, no hardcoded lot sizes
