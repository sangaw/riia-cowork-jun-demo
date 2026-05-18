# Feature 10 — Restructure JS as Modular
**Status:** Draft — pending user approval  
**Date:** 2026-05-18  
**Scope:** `riia-jun-release/dashboard/js/`

---

## 1. Problem Statement

The JS codebase has grown organically across 4 dashboard apps (RITA, FnO, Ops, DS) with no shared layer. As of today it has **64 JS files (~7,858 lines)** across 5 module subtrees. Adding any new feature requires reading and editing multiple near-identical files across apps, and the DS app has **zero module structure** (all logic inline in `ds.html`).

### 1.1 Duplication Inventory

| File | Copies | Divergence |
|---|---|---|
| `api.js` | 4 (rita, fno, ops, invest-game) | Different error contracts: rita **throws**; ops **returns null**; fno mixes HTTP + app init |
| `utils.js` | 3 (rita, fno, ops) | `fmt()` has 3 different signatures; `badge()` has 2 different signatures; `setEl()` missing in fno |
| `nav.js` | 3 (rita, fno, ops) | 3 completely different nav patterns |
| `charts.js` | 1 (rita only) | FnO and Ops render charts without the registry/destroy-recreate pattern |

### 1.2 God Modules (files that do too many things)

| File | Lines | Problem |
|---|---|---|
| `fno/api.js` | 109 | HTTP client + app init + side effects + `fetchPositions()` all in one file |
| `fno/manoeuvre.js` | 703 | Single section module; should be split into renderer + state |
| `ops/agent-builds.js` | 699 | Mixes KPI rendering, chart mounting, trend panels, token widget |
| `rita/main.js` | 147 | Growing catch-all for all `window.*` bindings |

### 1.3 Ops Internal Duplication

`ops/utils.js` (17 lines) and `ops/utilities.js` (79 lines) coexist with overlapping helpers. Some ops modules import from one, some from the other.

### 1.4 DS App Has No Module Structure

`dashboard/ds.html` contains 13 sections with all JS as inline `<script>` blocks. There is no `dashboard/js/ds/` directory. Every change to DS logic requires opening and editing a 3,500+ line HTML file. This is the highest maintenance risk in the codebase.

### 1.5 `apiFetch()` Is Inconsistently Implemented

The spec says all new fetch calls should use `apiFetch()` (adds `X-Request-ID` header for tracing). But:
- `rita/main.js`, `fno/main.js`, `ops/main.js` each have their own `apiFetch()` implementation
- `ops/api.js` also exports an `apiFetch()` — potentially conflicting
- There is no single source of truth

---

## 2. Goals

1. **Single source of truth for shared utilities** — `api.js`, `utils.js`, `charts.js` live once in `shared/` and are imported by all apps.
2. **Consistent API contract** — one error-handling convention across all apps.
3. **DS gets a real module structure** — `dashboard/js/ds/` directory, sections split into files.
4. **No God modules** — FnO `api.js` split; manoeuvre/agent-builds reviewed for split.
5. **`shared/nav.js` base pattern** — one lazy-loader registry pattern for all apps to follow.
6. **No breaking changes to HTML** — all `window.*` bindings and `onclick=""` handlers preserved; no HTML files are changed unless unavoidable.
7. **No bundler, no TypeScript** — pure ES modules throughout; constraint unchanged.

---

## 3. Non-Goals

- No React/Vue/Svelte migration.
- No TypeScript introduction.
- No build pipeline or bundler.
- No UI/feature changes — this is a pure structural refactor.
- No changes to the Python backend or API contracts.
- `invest-game` app is out of scope — it is standalone and not part of the 4-app suite.

---

## 4. Proposed Structure

### 4.1 Target Directory Layout

```
dashboard/js/
├── shared/                     ← canonical shared layer (new files)
│   ├── api.js                  ← single api() + apiFetch() + apiBase()
│   ├── utils.js                ← setEl(), badge(), fmt(), fmtPct(), fmtMs()
│   ├── charts.js               ← Chart.js registry (moved from rita/)
│   ├── nav-base.js             ← base lazy-loader pattern
│   └── api-cache.js            ← existing
├── rita/                       ← thin wrappers + app-specific modules
│   ├── api.js                  → re-exports from shared/api.js (or deleted)
│   ├── utils.js                → re-exports from shared/utils.js (or deleted)
│   ├── charts.js               → deleted; all imports updated to shared/charts.js
│   ├── nav.js                  ← keep (rita-specific: chat warmup, MCP poll timer)
│   └── [all other modules]     ← unchanged; imports updated to shared/
├── fno/
│   ├── api.js                  ← SPLIT: thin HTTP wrapper only; re-export from shared/api.js
│   ├── app-init.js             ← NEW: extracted app init + fetchPositions() from fno/api.js
│   ├── utils.js                → re-exports from shared/utils.js + fno-specific formatters
│   └── [all other modules]     ← unchanged
├── ops/
│   ├── api.js                  → re-exports from shared/api.js
│   ├── utils.js                ← MERGED: ops/utils.js + ops/utilities.js → one file
│   └── [all other modules]     ← unchanged
└── ds/                         ← NEW directory (Phase 3)
    ├── api.js                  ← re-exports from shared/api.js
    ├── nav.js                  ← section nav (extracted from ds.html inline script)
    ├── main.js                 ← entry point, wires all loaders
    └── [one file per section]  ← understand.js, dashboard.js, pipeline.js, etc.
```

### 4.2 Shared API Contract (canonical)

```js
// shared/api.js
export const apiBase = () => (window.RITA_API_BASE || '').replace(/\/$/, '');

export async function api(path, method = 'GET', body = null) {
  const opts = { method, headers: { 'Content-Type': 'application/json' } };
  if (body) opts.body = JSON.stringify(body);
  const r = await fetch(apiBase() + path, opts);
  if (!r.ok) {
    const err = await r.json().catch(() => ({ detail: r.statusText }));
    throw new Error(err.detail || r.statusText);
  }
  return r.json();
}

export async function apiFetch(url, options = {}) {
  // Adds X-Request-ID for distributed tracing (from spec §8)
  const traceId = window.SESSION_TRACE_ID || Math.random().toString(16).slice(2);
  try {
    const r = await fetch(apiBase() + url, {
      ...options,
      headers: { 'X-Request-ID': traceId, ...(options.headers || {}) }
    });
    if (!r.ok) { console.warn(`[api] ${url} → ${r.status}`, traceId); return null; }
    return await r.json();
  } catch (e) {
    console.warn(`[api] ${url} fetch error`, e, traceId);
    return null;
  }
}
```

**Convention:** `api()` throws on error (use for actions — POST/PUT). `apiFetch()` returns null on error (use for reads).

### 4.3 Shared Utils Contract

```js
// shared/utils.js
export const fmt = (v, d = 2) => v == null || v === '' ? '—' : parseFloat(v).toFixed(d);
export const fmtPct = v => v == null ? '—' : parseFloat(v).toFixed(2) + '%';
export const fmtMs = v => v == null ? '—' : Math.round(v) + ' ms';
export const setEl = (id, html) => { const el = document.getElementById(id); if (el) el.innerHTML = html; };
export function badge(status) {
  const map = { ok: 'ok', warn: 'warn', alert: 'err', error: 'err', run: 'run', running: 'run' };
  const cls = map[(status || '').toLowerCase()] || 'neu';
  return `<span class="badge ${cls}">${status || '—'}</span>`;
}
```

Note: FnO-specific formatters (`fmtPnl`, `pnlClass`, Indian locale `fmt`) stay in `fno/utils.js` — they extend shared, not replace it.

---

## 5. Phased Delivery Plan

### Phase 1 — Shared Layer (foundation)
**Effort:** ~1 day  
**Risk:** Low — additive only, no existing file modified

- Create `shared/api.js` — canonical api + apiFetch + apiBase
- Create `shared/utils.js` — canonical setEl, badge, fmt, fmtPct, fmtMs
- Move `rita/charts.js` → `shared/charts.js`
- Create `shared/nav-base.js` — lazy-loader registry pattern

### Phase 2 — Migrate RITA and Ops to shared imports
**Effort:** ~1 day  
**Risk:** Medium — imports change; window bindings must be tested

- Update `rita/`: all modules import from `../shared/`; delete local `api.js`, `utils.js`, `charts.js` or replace with re-exports
- Update `ops/`: merge `utils.js` + `utilities.js` → one file importing from shared; update `api.js`
- Update Spec_JS_Code.md — shared module table

### Phase 3 — FnO God Module Split
**Effort:** ~1 day  
**Risk:** Medium — `fno/api.js` is deeply imported; split must be clean

- Extract `fno/api.js` init logic → `fno/app-init.js`
- `fno/api.js` becomes thin: re-export `api`, `apiFetch`, `apiBase` from `../shared/api.js`
- Update all `fno/` modules to import from `app-init.js` as needed
- `fno/utils.js` — keep fno-specific formatters, import shared setEl/badge

### Phase 4 — DS Module Extraction
**Effort:** ~2 days  
**Risk:** High — requires coordinated changes to `ds.html` (script tags removed, module script added) and creating 13+ new files

- Create `dashboard/js/ds/` directory
- Extract inline scripts section by section into module files
- Replace inline `<script>` blocks in `ds.html` with `<script type="module" src="js/ds/main.js">`
- All existing `show()` / nav calls preserved; exposed on `window.*` where needed by HTML onclick

### Phase 5 — Large Module Audit (optional / ongoing)
**Effort:** ~1 day  
**Risk:** Low if done carefully

- `fno/manoeuvre.js` (703 lines) → review for renderer/state split
- `ops/agent-builds.js` (699 lines) → review for sub-module split
- No forced splits unless the module has clear, separable concerns

---

## 6. Migration Rules (for all phases)

1. **Re-export over delete** — if an app-local file (`rita/api.js`) is being replaced by shared, keep the file as a thin re-export for 1 sprint to avoid hunting down all import paths at once.
2. **No bundler** — all imports must use relative paths (e.g. `'../shared/api.js'`).
3. **No HTML changes unless Phase 4** — don't touch `rita.html`, `fno.html`, `ops.html` in Phases 1–3.
4. **window.* bindings unchanged** — all existing onclick handlers continue to work unchanged.
5. **One phase per /enhance run** — each phase is a separate Engineer agent task with its own QA run.
6. **ruff check equivalent** — after each phase, manually verify the app loads in browser (no console errors on page load).

---

## 7. Acceptance Criteria

- [ ] `shared/api.js`, `shared/utils.js`, `shared/charts.js` exist and are imported by all 3 apps (rita, fno, ops)
- [ ] No duplicate `api()` function across app-local files — all route through `shared/api.js`
- [ ] `fmt()` signature is consistent: `fmt(v, decimals=2)` returning `'—'` on null
- [ ] `badge()` signature is consistent: `badge(status)` with CSS class map
- [ ] `fno/api.js` contains only HTTP-layer code (≤ 20 lines)
- [ ] `ops/utils.js` and `ops/utilities.js` are merged into one file
- [ ] `dashboard/js/ds/` directory exists with at least `main.js`, `nav.js`, `api.js`
- [ ] `ds.html` loads via `<script type="module" src="js/ds/main.js">` with no inline `<script>` blocks
- [ ] All 4 apps load in browser without console errors after each phase
- [ ] `Spec_JS_Code.md` updated to reflect new shared module table

---

## 8. What Is NOT Changing

- All API endpoint URLs — unchanged
- All HTML element IDs — unchanged
- All `window.*` bindings — unchanged (apps still call `window.loadTrades()` etc.)
- Chart.js library — unchanged
- Section loader pattern — preserved, just sourced from `shared/nav-base.js`
- `invest-game/` — out of scope
