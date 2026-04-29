---
description: Add or update a feature in the Ops dashboard (ops.html + dashboard/js/ops/)
---

You are an Engineer agent adding or updating a feature in the RITA Ops dashboard.

**Task:** $ARGUMENTS

---

## Module Map — `dashboard/js/ops/`

| File | Responsibility | Key exports |
|---|---|---|
| `api.js` | Ops HTTP client | `api(path, method?, body?)` |
| `utils.js` | DOM helpers | `setEl(id, html)`, `badge(status)`, `fmt(v, dec)` |
| `sidebar.js` | Sidebar navigation | `showSection()` |
| `nav.js` | Section navigation | `show(section)`, `_sectionLoaders` |
| `main.js` | Entry point | Registers loaders, binds `window.*` |
| `overview.js` | Ops overview dashboard | `loadOverview()` |
| `cicd.js` | CI/CD pipeline view | `loadCicd()` |
| `monitoring.js` | Prometheus metrics view | `loadMonitoring()` |
| `observability.js` | Structured metrics summary | `loadObservability()` |
| `test-results.js` | Test results grid | `loadTestResults()` |
| `daily-ops.js` | Daily operations panel | `loadDailyOps()` |
| `deploy.js` | Deployment management | `loadDeploy()` |
| `chat.js` | Ops chat | `sendOpsChat()` |
| `users.js` | User management table | `loadUsers()`, `createUser()`, `deleteUser()` |

**Read only the file(s) you need to modify — do not read all files.**

---

## Adding a New Section — 4-Step Checklist

1. **HTML** — add `<section id="sec-NAME" class="section">` to `ops.html`
2. **JS loader file** — create `dashboard/js/ops/my-feature.js` with `export function loadMyFeature() { ... }`
3. **Register in `main.js`** — `import { loadMyFeature } from './my-feature.js'; _sectionLoaders['NAME'] = loadMyFeature;`
4. **`window.*` binding** — in `main.js`, add `window.loadMyFeature = loadMyFeature;` for any refresh button

---

## KPI Card Pattern

```js
import { setEl, badge, fmt } from './utils.js';
import { api } from './api.js';

export async function loadMyFeature() {
    try {
        const data = await api('/api/v1/ops/my-endpoint');
        setEl('my-kpi-value', fmt(data.count, 0));
        setEl('my-status', badge(data.status));
    } catch (e) {
        console.warn('[ops/my-feature] load failed', e);
    }
}
```

---

## Ops-Specific Rules

**No trading logic in the Ops dashboard.** Ops sections cover:
- System health and uptime
- CI/CD pipeline status
- Test run results
- Prometheus metrics
- User management
- Deployment controls

If a feature requires reading portfolio data or model results, use the RITA dashboard (`/add-rita-feature`) instead.

**Sidebar navigation:** `ops.html` uses `sidebar.js` for its nav, not inline `show()` calls. New sidebar links go in `ops.html` and call `showSection('NAME')`.

**Auth-gated endpoints:** Some ops endpoints require admin JWT. The JS `api()` helper in `ops/api.js` attaches the token from `localStorage.getItem('opsToken')`. New admin-only endpoints must use `Depends(require_admin)` in the Python router.

---

## API Contract Check (mandatory)

```
grep -r "my-endpoint" riia-jun-release/src/rita/api/
```

**Key Ops endpoints:**

| Endpoint | Consumer |
|---|---|
| `GET /api/v1/test-results` | `test-results.js` |
| `GET /api/v1/metrics/summary` | `monitoring.js`, `observability.js` |
| `GET /health` | `overview.js` |
| `GET /api/v1/audit-log` | `audit` panel |
| `GET /api/v1/users` | `users.js` |

---

## Files to Touch

| File | Action |
|---|---|
| `dashboard/js/ops/my-feature.js` | Create — loader function |
| `dashboard/js/ops/main.js` | Edit — import, `_sectionLoaders`, `window.*` |
| `dashboard/ops.html` | Edit — add `<section id="sec-NAME">` and sidebar link |
| `src/rita/api/<tier>/my_endpoint.py` | Create/edit — if new API endpoint needed |
| `src/rita/main.py` | Edit — `include_router(...)` if new router |
| `Specs/Spec_JS_Code.md` | Edit — add row to ops module map |
| `Specs/Spec_Python_Code.md` | Edit — add row to API table if contract changed |

---

## Definition of Done

- [ ] New section renders without console errors
- [ ] Every `setEl('id', ...)` has a matching element in `ops.html`
- [ ] Every field read from API response confirmed present in handler's `return` dict
- [ ] `window.*` binding added in `main.js` for all `onclick` handlers
- [ ] `_sectionLoaders['NAME']` registered in `main.js`
- [ ] `try/catch` in every async loader — no silent swallows
- [ ] Admin-gated endpoints use `Depends(require_admin)` if needed
- [ ] `Specs/Spec_JS_Code.md` updated if new module added
- [ ] `Specs/Spec_Python_Code.md` updated if new API endpoint added
