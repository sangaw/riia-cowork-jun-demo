# Skill: Add Ops Dashboard Feature
**App:** Ops dashboard (`ops.html` + `dashboard/js/ops/`)
**Use for:** New UI sections in the Ops monitoring/admin dashboard (CI/CD, metrics, users, deployments)
**Compiled from:** `Spec_RITA_App.md` + `Spec_JS_Code.md`

---

## App Identity

| Item | Value |
|---|---|
| HTML file | `riia-jun-release/dashboard/ops.html` — **Never read directly.** Use spec. |
| JS module dir | `riia-jun-release/dashboard/js/ops/` |
| Experience API | `riia-jun-release/src/rita/api/experience/ops.py` |
| System APIs used | `api/v1/users.py`, `api/v1/audit.py`, `api/v1/market_data.py` |
| Spec file | `project-office/specs/Spec_RITA_App.md` |
| JS Spec file | `project-office/specs/Spec_JS_Code.md` |

---

## File Map — What to Touch for a Typical Ops UI Feature

| Layer | File | What to do |
|---|---|---|
| **Backend** | `src/rita/api/experience/ops.py` | Add aggregated read-only payload endpoint |
| **Backend** | `src/rita/api/v1/users.py` | Only for user management operations (GET/POST users) |
| **Backend** | `src/rita/schemas/{name}.py` | Add Pydantic response schema |
| **Frontend** | `dashboard/js/ops/{name}.js` | Create new JS module with loader function |
| **Frontend** | `dashboard/js/ops/main.js` | Register section loader + bind window.* functions |
| **HTML** | `ops.html` | Add `<section id="sec-NAME">` + sidebar nav item |
| **Spec** | `project-office/specs/Spec_RITA_App.md` | Update Experience/Ops tier endpoint inventory |

---

## Ops Module Reference (existing — do not duplicate)

| Existing module | What it already handles |
|---|---|
| `overview.js` | Ops overview dashboard — `loadOverview()` |
| `cicd.js` | CI/CD pipeline view — `loadCicd()` |
| `monitoring.js` | Prometheus metrics view — `loadMonitoring()` |
| `observability.js` | Structured metrics summary — `loadObservability()` |
| `test-results.js` | Test results grid — `loadTestResults()` → `GET /api/v1/test-results` |
| `daily-ops.js` | Daily operations panel — `loadDailyOps()` |
| `deploy.js` | Deployment management — `loadDeploy()` |
| `chat.js` | Ops chat — `sendOpsChat()` |
| `users.js` | User management table — `loadUsers()`, `createUser()`, `deleteUser()` |

Before adding a new module, confirm the feature is not already covered by an existing one.

---

## Ops Experience API Reference (existing endpoints)

| Endpoint | Method | Returns |
|---|---|---|
| `/api/experience/ops` | GET | Ops aggregated payload (legacy) |
| `/api/experience/ops/metrics/summary` | GET | API request counts, latency, error rate, pipeline stats |
| `/api/experience/ops/step-log` | GET | Pipeline step log entries |
| `/api/experience/ops/users` | GET | User list for Ops view |
| `/api/v1/users` | GET/POST | User management (system tier) |
| `/api/v1/audit` | GET | Audit log entries |
| `/api/v1/test-results` | GET | Unit/integration/e2e test result summary |

---

## Step-by-Step Task Rules

### Step 1 — Design the API Contract First
Define before writing code:
- Endpoint: method + path + query params
- What data it aggregates (metrics, logs, user data, test results)
- Response shape: field names + types as Pydantic schema
- Frontend consumer: which JS module, which DOM element IDs

Write the contract in the task brief `[Architect] Design` section before proceeding.

### Step 2 — Add the Backend Endpoint
Ops features almost always go in the Experience tier (`ops.py`) — they aggregate data from multiple sources for the dashboard display.

**Experience tier pattern:**
```python
@router.get("/api/experience/ops/my-feature", response_model=MyOpsFeatureResponse)
def get_my_ops_feature(db: Session = Depends(get_db)):
    # Aggregate from repos — no commits
    audit_repo = AuditRepository(db)
    entries = audit_repo.list_recent(100)
    return MyOpsFeatureResponse(items=[...])
```

**Key rules:**
- Experience tier is **read-only** — never call `db.commit()` in ops.py
- `get_settings()` is a function call — never use bare `settings` at module level (causes NameError → endpoint returns `[]`)
- Repos require `db: Session` — always use `Depends(get_db)`
- For metrics, read from Prometheus via `get_metrics_summary()` pattern in existing `ops.py`

### Step 3 — Add the Pydantic Schema
File: `src/rita/schemas/{name}.py`
- Match field names to what the JS will read
- Key existing field names: `total_requests`, `avg_latency_ms`, `error_rate_pct`, `pipeline.completed_steps`

### Step 4 — Write the JS Module
File: `dashboard/js/ops/{name}.js`

**Module template:**
```js
import { api } from './api.js';
import { setEl, badge, fmt } from './utils.js';
import { mkChart, C } from './charts.js';

export async function loadMyOpsFeature() {
  try {
    const data = await api('/api/experience/ops/my-feature');
    setEl('ops-my-feature-value', fmt(data.value));
  } catch (e) {
    setEl('ops-my-feature-value', '—');
  }
}
```

**Rules:**
- Import `api` from `./api.js` — never raw `fetch()`
- Wrap in `try/catch` — show `—` on error
- Use `setEl(id, html)` from `utils.js`
- Use `mkChart(id, config)` from `charts.js`
- Use `C` color palette
- No top-level `fetch()` or DOM queries

### Step 4.5 — FC-IMP Check: Verify Named Imports (run before Step 5)

> **Run this immediately after writing the JS module — before registering in main.js.**

For every `import { name1, name2 } from './module.js'` line in the new JS file:
1. Open `module.js` and grep for `export` statements
2. Confirm each imported name appears as `export function name` or `export const name`
3. Report explicitly: "FC-IMP: [name1] ✓ in [module.js]" — one line per import

**A missing named export is a static binding error** — the browser throws a `SyntaxError` at parse time and the entire app module tree dies, not just the new section. Do NOT proceed to main.js registration until all imports are confirmed.

If any name is missing: find the correct exported name in the file, or add the export — report the resolution. Do not silently skip a check.

### Step 5 — Register Section Loader in main.js
In `dashboard/js/ops/main.js`:
```js
import { loadMyOpsFeature } from './my-ops-feature.js';

_sectionLoaders['my-ops-feature'] = loadMyOpsFeature;
window.loadMyOpsFeature = loadMyOpsFeature;
```

**Note:** Ops dashboard also has a sidebar nav (`sidebar.js`). If the new section needs a sidebar entry, add it to `sidebar.js:showSection()` in addition to `_sectionLoaders`.

### Step 6 — Update the Spec

> **STOP — do not run `git add` until this step is complete. This is a blocking gate — spec not updated = orchestrator will re-invoke you to fix it before QA runs.**

File: `project-office/specs/Spec_RITA_App.md`
- Add the new endpoint to Section 3, Experience Tier (Ops row)
- Add the new JS module to `Spec_JS_Code.md` Section 4 (Ops module structure)

Open each spec file. Read the relevant table. Add the new row. **Report the exact line you added to each file** (e.g. `| GET | /api/experience/ops/my-feature | MyOpsFeatureResponse |`). Only after reporting the exact lines may you proceed to commit.

### Step 7 — TechWriter: Confluence + Human Score Prompt

> **STOP — before closing the run, confirm `Spec_RITA_App.md` and `Spec_JS_Code.md` reflect the new endpoint and module. If the Engineer skipped Step 6, do it now before emitting the human score prompt.**

After confirming spec files and updating Confluence, ask the user to run a smoke test before scoring:

> **Smoke-test gate:** "Please open the Ops dashboard in a browser and verify the new section renders without JavaScript console errors. Open browser DevTools → Console and confirm no `SyntaxError`, `Cannot resolve module`, or `is not exported` errors appear. Report: page loads OK / page broken."
>
> If the user reports a runtime error: do NOT emit the scoring prompt. Investigate and fix the error first — it is likely a missing named export (FC-IMP) or a conflict marker (FC-MERGE). Only emit the scoring prompt after the user confirms the page loads cleanly.

Once the user confirms the page loads, emit the following prompt:

```
=== Agent Run Complete — Please score this run ===
Output accuracy (1–5, where 5 = exactly what was needed): _
Relevance to stated intent (1–5): _
Did PM + Architect decompose the task correctly first time? (y/n): _
Overall satisfaction / CSAT (1–5): _
Estimated hours this would have taken manually: _
Press Enter to skip any field.
=========================================
```

Record responses as `human_score{}` in the run JSON: `accuracy`, `relevance`, `planning_ok` (y→true), `csat`, `time_saved_hours`. Skipped fields default to `null`.

---

## Guardrails

| Rule | Detail |
|---|---|
| Never read `ops.html` directly | Use spec and HTML spec for nav/DOM patterns |
| Never use bare `settings` at module level | Always call `get_settings()` — bare `settings` throws NameError silently, endpoint returns `[]` |
| Never call `db.commit()` in Experience tier | Experience routes are read-only |
| Never add `print()` statements | Use `structlog` |
| Never hardcode `http://localhost:8000` in JS | Use `window.RITA_API_BASE` |
| Never call `new Chart(...)` directly | Use `mkChart(id, config)` from `charts.js` |
| Never expose ES module functions without `window.*` | `onclick=""` handlers silently fail |
| Never duplicate existing ops endpoints | Check the Ops Experience API Reference table above first |
| Always update spec when contract changes | Spec drift breaks future agents |
| HTML changes are still required even though full reads are forbidden | "Never read ops.html" = no full-file Read (3,500 lines). For any HTML file in the Architect's files-to-touch list: use Grep to find a sibling element ID, read ±15 lines around it, then use targeted Edit to insert. Skipping an HTML change is a partial implementation (FC-PARTIAL-IMPL). |
| **Alembic migration must be applied, not just created** | After writing a migration file, run `python -m alembic upgrade head` from `riia-jun-release/` and confirm the `Running upgrade` line before committing. Committing the file alone does NOT apply the schema change — the app will crash with `OperationalError: no such column` at runtime. This is a hard DoD gate: migration applied = confirmed upgrade output seen. |

---

## Definition of Done

Before marking this task complete, verify each item:

**FC-004 gate — verify before committing:**
Open the JS module you just wrote or changed. List every `data.field` or `r.field`
access in the file. For each, confirm the exact field name exists in your Pydantic
schema or response dict. A single character difference (underscore vs camelCase,
_pct suffix missing) causes a silent JS render failure. Only after verifying every
field may you proceed to git add.

**FC-IMP gate — JS named-import resolution (verify before committing):**
For every `import { name1, name2 } from './module.js'` line in the new or modified
JS file, open `module.js` and confirm each name appears in an `export` statement.
A missing named export is a **static binding error** — the browser throws a
`SyntaxError` at parse time, which cascades up the import chain and kills the entire
app, not just the new section. This check must be done explicitly; it is not caught
by the FC-004 contract check or by ruff.

**FC-MERGE gate — no leftover conflict markers (run before `git add`):**
Run: `grep -rn "^<<<<<<\|^=======\|^>>>>>>>" dashboard/js/`
Output must be empty. Any `<<<<<<<` / `=======` / `>>>>>>>` left in a JS file is a
`SyntaxError` that kills the entire app module tree — the browser cannot parse these
tokens. This is especially critical after merge conflict resolution sessions.

- [ ] **API contract matches** — Pydantic schema field names match JS `data.field` reads exactly
- [ ] **Experience tier is read-only** — no `db.commit()` calls in the new route
- [ ] **`get_settings()` used, not bare `settings`** — avoids silent NameError
- [ ] **Section loader registered** — `_sectionLoaders['name'] = loadName` in `ops/main.js`
- [ ] **Window bindings set** — all `onclick` handlers on `window.*` in `ops/main.js`
- [ ] **Error handled** — `try/catch` in JS loader; shows `—` on failure
- [ ] **Spec updated** — endpoint added to `Spec_RITA_App.md` Experience/Ops tier; JS module added to `Spec_JS_Code.md` Section 4. **"n/a" is ONLY valid if the Architect's files-to-touch table lists zero spec rows** — any other "n/a" is FC-001 and triggers orchestrator re-invocation.
- [ ] **HTML changes complete** — every HTML file in the Architect's files-to-touch table is edited via Grep → read ±15 lines → targeted Edit. If Architect listed zero HTML files, write "n/a". Skipping = FC-PARTIAL-IMPL.
- [ ] **Ruff passes** — `ruff check src/` returns no errors
- [ ] **No hardcoded values** — no localhost URLs
