# Feature 14 — Dutch and French Language Support (i18n)
**Status:** IN PROGRESS — Phase 2 partial (RITA main sections done); Ops/FnO loaders pending  
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
| Fix: translate main screen labels (b8cc652) — health, market-signals, trades, fno/dashboard.js | `[x]` | b8cc652 | KPIs use t() at render time |
| Fix: performance.js, risk.js, scenarios.js, explainability.js — t() + 30 new locale keys | `[x]` | ba4b905 | perf.bnh, risk.*, scenarios.*, explain.* added to en/nl/fr |

---

## Pending — Next Session

### Defect 2 — Remaining loaders not translating (LOW–MEDIUM)

RITA main sections are now done. Remaining files with hardcoded English strings:

| File | Dashboard | Notes |
|---|---|---|
| `agent-panel.js` | RITA | Long English narrative text; status badges |
| `ai-compliance.js` | RITA | Section labels |
| `technical-analysis.js` | RITA | Section labels |
| `learnings.js` | RITA | Section labels |
| `positions.js`, `margin.js`, others | FnO | Most loaders; only dashboard.js done |
| `overview.js`, `agent-builds.js`, others | Ops | No section loaders have t() |

**Fix approach:** For each file — add `import { t } from '../shared/i18n.js';`, replace hardcoded label strings with `t('key')` calls, add missing keys to en/nl/fr locale files.

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

> "Continue Feature 14 — fix remaining Defect 2 loaders. RITA main sections done (health, market-signals, trades, performance, risk, scenarios, explainability). Remaining: rita/agent-panel.js, ai-compliance.js, technical-analysis.js, learnings.js; all FnO section loaders except dashboard.js; all Ops section loaders. Add import { t } from '../shared/i18n.js' and replace hardcoded label strings with t('key') calls. Add new keys to en/nl/fr locale files. Context: project-office/features/May/14 Support for Dutch and French language/PLAN_STATUS.md"
