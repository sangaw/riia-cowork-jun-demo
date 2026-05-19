# Feature 12B — Restructure UI Screens: Relocate Mobile PWA

**Status:** Complete  
**Date:** 2026-05-19  
**Closed:** 2026-05-19 (commits df905db, 84b5d22)

---

## Original Requirement

Mobile device screens are under `rita-build-portfolio`. Pick up the screens that are used and move them under `riia-jun-release/mobileapp`.

---

## What Was Done

All UI files from `rita-build-portfolio/` relocated to `riia-jun-release/mobileapp/`. No files deleted — `rita-build-portfolio/` remains on disk but is no longer tracked by git.

### Files Moved

| Source | Destination |
|---|---|
| `rita-build-portfolio/android-mobile-app/` | `riia-jun-release/mobileapp/` (PWA: index.html, manifest.json, sw.js, icons/) |
| `rita-build-portfolio/investor-flow/` | `riia-jun-release/mobileapp/investor-flow/` (onboarding flow v1 + v2) |
| `rita-build-portfolio/treatments/` | `riia-jun-release/mobileapp/treatments/` |
| Root HTML mockups (5 files) | `riia-jun-release/mobileapp/` |
| Root JSX design tools (4 files) | `riia-jun-release/mobileapp/` |
| `android-deploy-steps.md` | `riia-jun-release/mobileapp/` |

### Code Changes

| File | Change |
|---|---|
| `riia-jun-release/src/rita/main.py` | Added `/mobileapp` StaticFiles mount (html=True); fixed `/onboarding` route path from `rita-build-portfolio/investor-flow/v2/` to `mobileapp/investor-flow/v2/` |
| `project-office/specs/Spec_Mobile_App.md` | File path updated to `riia-jun-release/mobileapp/index.html` |
| `CLAUDE.md` | Spec table + "never read" rule updated to new path |
| `.gitignore` | `rita-build-portfolio/` added (alongside `riia-ai-org/`) |

### Serving URLs (server at localhost:8000)

| Screen | URL |
|---|---|
| Live PWA | `http://localhost:8000/mobileapp/` |
| Onboarding flow | `http://localhost:8000/onboarding` |
| Investor flow v2 direct | `http://localhost:8000/mobileapp/investor-flow/v2/invest-dashboard.html` |
| Design mockups | `http://localhost:8000/mobileapp/RITA%20Mobile-v%201.html` etc. |

---

## Acceptance Criteria

- [x] All files from `rita-build-portfolio/android-mobile-app/` present in `riia-jun-release/mobileapp/`
- [x] All design mockups, investor-flow/, treatments/ present in `riia-jun-release/mobileapp/`
- [x] `/mobileapp` StaticFiles mount added to `main.py`
- [x] `/onboarding` route resolves from new path (ruff: clean)
- [x] `rita-build-portfolio/` added to `.gitignore`
- [x] `git status` shows no tracked files under `rita-build-portfolio/`
- [x] `Spec_Mobile_App.md` and `CLAUDE.md` references updated
