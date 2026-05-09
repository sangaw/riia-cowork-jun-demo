# Skill: Add RITA Dashboard Feature
**App:** RITA main dashboard (`rita.html` + `dashboard/js/rita/`)
**Use for:** New UI sections, panels, widgets, or data views in the RITA trading dashboard
**Compiled from:** `Spec_RITA_App.md` + `Spec_JS_Code.md`

---

## App Identity

| Item | Value |
|---|---|
| HTML file | `riia-jun-release/dashboard/rita.html` — 4,000 lines. **Never read directly.** Use spec. |
| JS module dir | `riia-jun-release/dashboard/js/rita/` |
| Experience API | `riia-jun-release/src/rita/api/experience/rita.py` |
| System API | `riia-jun-release/src/rita/api/v1/system/` (one file per table) |
| Workflow API | `riia-jun-release/src/rita/api/v1/workflow/` (JWT-protected — avoid for UI reads) |
| Spec file | `project-office/specs/Spec_RITA_App.md` |
| JS Spec file | `project-office/specs/Spec_JS_Code.md` |

---

## File Map — What to Touch for a Typical UI Feature

| Layer | File | What to do |
|---|---|---|
| **Backend** | `src/rita/api/experience/rita.py` | Add read-only aggregation endpoint (Experience tier) |
| **Backend** | `src/rita/api/v1/system/{name}.py` | Add system CRUD endpoint only if the feature needs raw table access |
| **Backend** | `src/rita/schemas/{name}.py` | Add Pydantic response schema for the new endpoint |
| **Frontend** | `dashboard/js/rita/{name}.js` | Create new JS module with loader function |
| **Frontend** | `dashboard/js/rita/main.js` | Register section loader + bind window.* functions |
| **HTML** | `rita.html` | Add `<section id="sec-NAME">` with DOM elements (read HTML spec first for nav pattern) |
| **Spec** | `project-office/specs/Spec_RITA_App.md` | Update endpoint inventory + section description |

---

## Step-by-Step Task Rules

### Step 1 — Design the API Contract First
Before writing any code, define:
- Endpoint: method + path + query params
- Response shape: field names + types (write this as a Pydantic schema first)
- Frontend consumer: which JS module, which DOM element IDs

Write the contract in the task brief `[Architect] Design` section before proceeding.

### Step 2 — Add the Backend Endpoint
**Tier selection:**
- New data aggregation for the UI → Experience Tier (`src/rita/api/experience/rita.py`)
- Raw table CRUD → System Tier (`src/rita/api/v1/system/`)
- Never add read-only UI endpoints to the Workflow tier

**Experience tier rules:**
- Read-only — never call `db.commit()`, `repo.upsert()`, or `repo.delete()` in Experience routes
- Call repositories directly — no service layer needed for Experience reads
- All repos require `db: Session` — always use `Depends(get_db)`
- Return a Pydantic schema, not a raw dict

**Example pattern:**
```python
@router.get("/api/experience/rita/my-feature", response_model=MyFeatureResponse)
def get_my_feature(db: Session = Depends(get_db)):
    repo = MyRepo(db)
    data = repo.get_all()
    return MyFeatureResponse(items=data)
```

### Step 3 — Add the Pydantic Schema
File: `src/rita/schemas/{name}.py`
- Define request + response models
- Use field constraints: `ge=0`, `max_length=255`, `pattern=` where relevant
- Match field names exactly to what the JS frontend will read

### Step 4 — Register the Router (if new file)
In `src/rita/main.py`, include the new router with the correct prefix.
Only needed if you created a new router file — existing routers are already registered.

### Step 5 — Write the JS Module
File: `dashboard/js/rita/{name}.js`

**Module template:**
```js
import { api } from './api.js';
import { setEl, badge, fmt, fmtPct } from './utils.js';
import { mkChart, C } from './charts.js';

export async function loadMyFeature() {
  try {
    const data = await api('/api/experience/rita/my-feature');
    setEl('my-feature-value', fmt(data.value));
    mkChart('chart-my-feature', { type: 'line', data: { ... }, options: { ... } });
  } catch (e) {
    setEl('my-feature-value', '—');
  }
}
```

**Rules:**
- Always import `api` from `./api.js` — never use raw `fetch()`
- Always wrap API calls in `try/catch` — show `—` on error, never crash
- Use `setEl(id, html)` from `utils.js` — never `document.getElementById(...).innerHTML = ...`
- Use `mkChart(id, config)` from `charts.js` — never `new Chart(...)` directly
- Use `C` color palette: `C.run` (blue), `C.build` (green), `C.warn` (amber), `C.danger` (red)
- No `fetch()`, `console.log()`, or DOM queries at module top level — only inside functions
- Base URL from `window.RITA_API_BASE` — never hardcode `http://localhost:8000`

### Step 6 — Register Section Loader in main.js
In `dashboard/js/rita/main.js`:
```js
import { loadMyFeature } from './my-feature.js';

// In the loader registration block:
_sectionLoaders['my-feature'] = loadMyFeature;

// At the bottom, window bindings:
window.loadMyFeature = loadMyFeature;
// Add any onclick handlers here too:
window.myFeatureAction = myFeatureAction;
```

**Rules:**
- Section id in HTML must be `sec-my-feature` (prefix `sec-`)
- Loader key is `my-feature` (no `sec-` prefix)
- Every function called from `onclick=""` in HTML must be on `window.*`

### Step 7 — Update the Spec
File: `project-office/specs/Spec_RITA_App.md`
- Add the new endpoint to Section 3 (Endpoint Inventory) under the correct tier
- Add the new JS module to Section 2 (Module Structure)
- Add API→JS consumer mapping to `Spec_JS_Code.md` Section 9

**This step is mandatory. Do not mark the task complete without it.**

---

## Guardrails

| Rule | Detail |
|---|---|
| Never read `rita.html` directly | File is 4,000 lines. Use `Spec_HTML_Code.md` and spec section descriptions. |
| Never hardcode lot sizes or config values | Read from `settings.instruments.*` or `config_overrides` table |
| Never call `db.commit()` in Experience tier | Experience routes are read-only by design (ADR-001) |
| Never use bare `pd.read_csv()` | Always use `load_nifty_csv()` or `load_instrument_data()` from `core/data_loader.py` |
| Never call a repo directly from a Workflow router | Workflow tier uses service layer; System tier uses repo-per-router |
| Never add `print()` statements | Use `structlog` for logging |
| Never hardcode `http://localhost:8000` in JS | Use `window.RITA_API_BASE` |
| Never call `new Chart(...)` directly | Always use `mkChart(id, config)` from `charts.js` |
| Never expose ES module functions without `window.*` | `onclick=""` handlers silently fail if not on `window` |
| Always update spec when contract changes | Spec drift breaks future agents |

---

## Definition of Done

Before marking this task complete, verify each item:

- [ ] **API contract matches** — Pydantic schema field names match JS `data.field` reads exactly
- [ ] **Experience tier is read-only** — no `db.commit()` calls in the new route
- [ ] **Section loader registered** — `_sectionLoaders['name'] = loadName` in `main.js`
- [ ] **Window bindings set** — all `onclick` handlers exposed on `window.*` in `main.js`
- [ ] **Error handled** — `try/catch` in JS loader; shows `—` on failure, no crash
- [ ] **Spec updated** — endpoint added to `Spec_RITA_App.md` Section 3; JS module added to `Spec_JS_Code.md` Section 2
- [ ] **Ruff passes** — `ruff check src/` returns no errors
- [ ] **No hardcoded values** — no localhost URLs, no hardcoded lot sizes or config values
