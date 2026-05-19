# Feature 14 — Dutch and French Language Support (i18n)
**Status:** IN PROGRESS — Phase 1 merged, defects under testing  
**Last updated:** 2026-05-19  
**Requirements:** `REQUIREMENTS.md` (same folder)  
**Task brief:** `project-office/task-briefs/task-brief-20260519-1001.md`

---

## Delivered (2026-05-19)

Run via `/enhance rita`. Four commits merged to master and pushed to remote.

| Task | Status | Commit | Notes |
|---|---|---|---|
| shared/i18n.js module (t, setLanguage, getLanguage, applyTranslations, initI18n) | `[x]` | 6871240 | dashboard/js/shared/i18n.js |
| Locale files — en.js, nl.js, fr.js (105 keys each) | `[x]` | 6871240 | dashboard/js/locales/ |
| .lang-capsule + .lang-btn CSS | `[x]` | 6871240 | dashboard/css/responsive.css |
| Language capsule on index.html (landing page only) | `[x]` | 6871240 | EN/NL/FR pill buttons in topbar |
| data-i18n attrs on nav items — all 5 HTML pages | `[x]` | 6871240 | 5 nav labels per page |
| main.js wiring — initI18n + applyTranslations + window.setLanguage | `[x]` | 6871240 | rita, fno, ops, ds main.js |
| Mobile PWA inline i18n + capsule on home screen | `[x]` | 6871240 | mobileapp/index.html |
| Spec_JS_Code.md — i18n.js row in shared modules table | `[x]` | 6871240 | line 104 confirmed |
| Fix: remove capsule from app pages (rita/fno/ops/ds) | `[x]` | ee10cd5 | capsule on index.html only; flows via localStorage |
| Fix: capsule styling — inline CSS in index.html | `[x]` | 1b116de | matches topbar .status-pill design |

---

## Pending — Next Session

### Defect 2 — Main screen labels not translating (HIGH)

**Symptom:** Switching language changes left nav items but main content area stays in English — section headings, KPI card labels, button text within sections, table column headers all remain English.

**Root cause:** JS section loaders (health.js, trades.js, market-signals.js, etc.) build HTML strings dynamically via `setEl(id, html)`. Those strings contain hardcoded English text. They need to call `t(key)` at render time. The `data-i18n` approach only works for static HTML elements already in the DOM — dynamic renders bypass it.

**Fix approach (Phase 2 from Requirements.md §7):**
1. Import `{ t }` into each section loader that renders HTML strings with static labels
2. Replace hardcoded English strings with `t('key')` calls — e.g. `'Sharpe Ratio'` → `t('kpi.sharpe_ratio')`
3. Priority modules (most visible labels): `health.js`, `market-signals.js`, `trades.js`, `risk.js`, `performance.js`
4. FnO: `dashboard.js`, `positions.js`, `margin.js`
5. Ops: `overview.js`, `agent-builds.js`
6. Test by switching language AFTER a section has loaded — labels should update on next section load

**Scope note:** This is a large change — ~10 JS files across rita/fno/ops need t() call substitution. Best run as a focused engineer task, not a full /enhance cycle.

---

### QA Tests — deferred (LOW)

Session hit 92% quota before QA agent ran. No unit tests written for i18n module.

**What to test:**
- `t(key)` with missing key → returns English fallback, not undefined/blank
- `setLanguage('nl')` → localStorage set + applyTranslations called
- `getLanguage()` with localStorage unavailable → returns 'en' without throwing
- `applyTranslations()` → all [data-i18n] elements updated
- Capsule active state syncs to stored language on page load

**Test file location:** `tests/unit/test_i18n.js` — note: i18n is pure JS, not Python; tests should be browser-side or use jsdom/vitest if available. If no JS test framework exists, skip and note as deferred.

---

### Confluence / TechWriter — deferred (LOW)

Engineering page (ID 76611602) not updated. Add a row for the i18n module and language capsule feature in the next TechWriter pass.

---

### Further user testing — in progress

User is testing label coverage, capsule position, and language persistence across page navigation. Any new defects to be filed here.

---

## Blockers

None

## Key Files

| File | Purpose |
|---|---|
| `riia-jun-release/dashboard/js/shared/i18n.js` | Core module — all i18n functions |
| `riia-jun-release/dashboard/js/locales/en.js` | Canonical key registry |
| `riia-jun-release/dashboard/js/locales/nl.js` | Dutch translations |
| `riia-jun-release/dashboard/js/locales/fr.js` | French translations |
| `riia-jun-release/dashboard/index.html` | Only page with the capsule selector |

## Resume Prompt (next session)

> "Continue Feature 14 — fix Defect 2: main screen labels not translating. JS section loaders in rita/fno/ops use hardcoded English strings in setEl() calls. Import t() into each and replace static label strings with t('key') calls. Start with rita/health.js, market-signals.js, trades.js. Context: project-office/features/14 Support for Dutch and French language/PLAN_STATUS.md"
