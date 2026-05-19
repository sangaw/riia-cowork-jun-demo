# Feature 10 — Restructure JS as Modular
**Status:** Requirements approved — not yet started  
**Last updated:** 2026-05-18  
**Requirements:** `REQUIREMENTS.md` (same folder)

---

## Overview

Restructure the dashboard JS codebase from 4 siloed app directories with duplicated utilities into a shared-layer modular architecture. No bundler, no TypeScript, no API or HTML contract changes.

**Scope:** `riia-jun-release/dashboard/js/`  
**Total files today:** 64 JS files (~7,858 lines) across rita/, fno/, ops/, ds (inline), invest-game/

---

## Phase Breakdown

### Phase 1 — Shared Layer Foundation
**Status:** `[x] Complete — merged 2026-05-18, commit 24102af`  
**Effort:** ~1 day  
**Risk:** Low — additive only

| Task | Status | Notes |
|---|---|---|
| Create `shared/api.js` — canonical api(), apiFetch(), apiBase() | `[x]` | commit 2d9d92e |
| Create `shared/utils.js` — setEl(), badge(), fmt(), fmtPct(), fmtMs() | `[x]` | badge() String() coercion (EC-5) |
| Move `rita/charts.js` → `shared/charts.js` | `[x]` | import path updated to ../rita/chart-modal.js |
| Create `shared/nav-base.js` — lazy-loader registry base | `[x]` | load() no-ops for unregistered keys (EC-6) |
| Update `Spec_JS_Code.md` — add shared/ module table | `[x]` | 4 rows added; Confluence Engineering v20 |

---

### Phase 2 — Migrate RITA + Ops to Shared Imports
**Status:** `[x] Complete — merged 2026-05-18, commit 2d8df86`  
**Effort:** ~1 day  
**Risk:** Medium — import paths change across ~25 files; window bindings must be preserved

| Task | Status | Notes |
|---|---|---|
| Update `rita/` — all modules import from `../shared/` | `[x]` | Replace or re-export local api.js, utils.js, charts.js |
| Update `ops/` — modules import from `../shared/` | `[x]` | ops/api.js → thin re-export from shared/ |
| Merge `ops/utils.js` + `ops/utilities.js` → one file | `[x]` | ops/utilities.js deleted; content merged into ops/utils.js |
| Browser verify: rita.html + ops.html load with zero console errors | `[x]` | Verified manually 2026-05-18 — zero console errors |
| Update `Spec_JS_Code.md` | `[x]` | commit 2b7fa51, branch worktree-agent-af1025d550695762c |

---

### Phase 3 — FnO God Module Split
**Status:** `[x] Complete — merged 2026-05-18, commit cb79df2`  
**Effort:** ~1 day  
**Risk:** Medium — fno/api.js is deeply imported; must not break fno.html load

| Task | Status | Notes |
|---|---|---|
| Extract `fno/api.js` init logic → `fno/app-init.js` (new file) | `[x]` | fetchPositions(), initApp(), checkStatus() — commit 198348b |
| Rewrite `fno/api.js` → thin re-export from `../shared/api.js` (≤20 lines) | `[x]` | 9 lines — commit 198348b |
| Update `fno/main.js` to import from `app-init.js` | `[x]` | One-line import change — commit 198348b |
| `fno/utils.js` — keep fno-specific formatters (fmt, fmtPnl, pnlClass) | `[x]` | No changes needed — all 3 already fno-specific |
| Browser verify: fno.html loads with zero console errors | `[x]` | Verified manually 2026-05-18 — zero console errors |
| Update `Spec_JS_Code.md` | `[x]` | app-init.js row added; api.js + utils.js rows updated — Confluence Engineering v22 |

---

### Phase 4 — DS Module Extraction
**Status:** `[x] Complete — merged 2026-05-18, commit 9c59fdb; browser verified 2026-05-18`  
**Effort:** ~2 days  
**Risk:** High — requires coordinated changes to ds.html (remove inline scripts, add module script tag)

| Task | Status | Notes |
|---|---|---|
| Create `dashboard/js/ds/` directory | `[x]` | 24 JS modules created |
| Create `ds/api.js` — re-export from `../shared/api.js` | `[x]` | commit 763b465 |
| Create `ds/nav.js` — extract inline show(section, el) + section switching | `[x]` | createShow(loaders) factory pattern |
| Create `ds/main.js` — entry point, wire all section loaders | `[x]` | 19 sections + window.* bindings at module scope |
| Extract each section into a module file | `[x]` | 19 sections (13 original + 6 model-* planned); state.js for cross-section state |
| Replace inline `<script>` blocks in `ds.html` with `<script type="module" src="js/ds/main.js">` | `[x]` | ~2500 lines of inline script removed |
| Browser verify: ds.html loads all sections with zero console errors | `[x]` | Verified 2026-05-18; 2 path bugs fixed (changelog 404 + step-log prefix) — commit c04441d |
| Update `Spec_JS_Code.md` — ds/ module table | `[x]` | 24-file table added — Confluence Engineering v23 |

---

### Phase 5 — Large Module Audit (optional)
**Status:** `[x] Complete — audited 2026-05-18, no splits warranted`  
**Effort:** ~0.5 day (audit only)  
**Risk:** Low

| Task | Status | Notes |
|---|---|---|
| Review `fno/manoeuvre.js` (703 lines) for renderer/state split | `[x]` | **No split.** 8 module-scoped state variables (`manGroupState`, `manAssign`, `manActiveTab`, etc.) shared implicitly across every render function. Split would require passing state objects everywhere — adds complexity, not reduces it. Coupling is intentional. |
| Review `ops/agent-builds.js` (699 lines) for sub-module split | `[x]` | **No split.** Already organized by comment blocks (Panel 1, Panel 2, etc.). All panels share helpers (`esc`, `panel`, `chartOpts`, `statusBadge`). A split would just create a third shared-helpers file with no functional gain. |
| Review `fno/hedge.js` (401 lines) | `[x]` | **No split.** Two named sections (`loadHedgeHistory` + `renderHedgeRadar`) read different state properties and don't call each other — split is technically clean. But at 401 lines it causes no real pain. Risk not worth the gain. |
| Review `fno/rr.js` (311 lines) | `[x]` | **No split.** Has a data layer (`computeScen`, `loadHistory`, `getBullBear`) and render layer (`renderScenarios` etc.) but render functions call data functions directly. Split would create a circular dep. Too small. |

**Design decision:** All 4 files audited. None meet the split threshold — state coupling or shared helpers prevent clean separation, and the files that could technically be split are not large enough to cause maintenance pain. No code changes made. Feature 10 closed.

---

## Acceptance Criteria (from REQUIREMENTS.md)

- [x] `shared/api.js`, `shared/utils.js`, `shared/charts.js` exist and imported by rita, fno, ops
- [x] No duplicate `api()` function in app-local files
- [x] `fmt()` signature consistent: `fmt(v, decimals=2)` returning `'—'` on null
- [x] `badge()` signature consistent: `badge(status)` with CSS class map
- [x] `fno/api.js` ≤ 20 lines (HTTP wrapper only)
- [x] `ops/utils.js` + `ops/utilities.js` merged into one file
- [x] `dashboard/js/ds/` directory exists with at least `main.js`, `nav.js`, `api.js`
- [x] `ds.html` uses `<script type="module">` — no inline `<script>` blocks
- [x] All 4 apps load in browser without console errors after each phase
- [x] `Spec_JS_Code.md` updated to reflect shared module table

---

## Blockers

None

## Notes

- 2026-05-18: Requirements approved by user. Feature folder created. Phased delivery plan confirmed. Each phase to be run as a separate /enhance engineer task.
- Phases 1–3 can run in order without touching HTML files.
- Phase 4 (DS) is the highest-risk phase — ds.html inline script removal requires careful coordination.
- Phase 5 is optional; only proceed if Phase 4 is complete with no regressions.

