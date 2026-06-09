# Feature 27 — fno Equity Scenarios Architecture Alignment: Engineering Context

**Created by:** Architect agent  
**Last updated:** 2026-06-09

---

## API Contract

| Field | Value |
|---|---|
| Method | N/A (static JSON) |
| Path | `/dashboard/data/scenarios/{file}.json` |
| Tier | N/A — JSON data layer (pre-API) |
| Query params | none |
| Request body | none |
| Response shape | see JSON files: alerts.json, portfolio.json, tradebook.json |
| Auth required | no |

---

## Files to Touch

| File | Action | Notes |
|---|---|---|
| `dashboard/js/scenarios/equity-scenarios.js` | Review / Edit | Verify FnO error handling pattern |
| `project-office/specs/Spec_RITA_App.md` | Edit | Add equity-scenarios page entry |
| `project-office/specs/Spec_JS_Code.md` | Edit | Add module to FnO section |

---

## JS Frontend Contract

| JSON field | JS reads as | DOM target element ID |
|---|---|---|
| `portfolio.holdings[].invested` | `h.invested` | `kpi-invested` |
| `portfolio.holdings[].cur_val` | `h.cur_val` | `kpi-value` |
| `portfolio.holdings[].pnl` | `h.pnl` | `kpi-pnl` |
| `alerts.instruments[].sl` | `a.sl` | range bar (renderBar) |
| `alerts.instruments[].target` | `a.target` | range bar (renderBar) |

---

## Key Decisions

| Decision | Reason |
|---|---|
| JSON layer retained for now | User explicitly approved; DB migration is a separate feature |
| Module stays in `dashboard/js/scenarios/` | Separate folder keeps it distinct from fno-specific modules |

---

## Edge Cases to Handle

| Case | Handling |
|---|---|
| JSON file missing / 404 | try/catch in init(); shows `.load-err` div |
| holding with no alert entry | `alerts.find()` returns undefined → `alert?.sl ?? null` |
| empty holdings array | renders empty grid |

---

## Open Engineering Questions

| # | Question | Status |
|---|---|---|
| Q1 | Should module move to dashboard/js/fno/? | Resolved: No — keep in dashboard/js/scenarios/ for clarity |
