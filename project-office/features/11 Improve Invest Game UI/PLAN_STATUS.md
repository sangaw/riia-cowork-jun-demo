# Feature 11 — Improve Invest Game UI
**Status:** COMPLETE  
**Last updated:** 2026-05-19  
**Requirements:** `requirements.md` (same folder)

---

## Delivered

Built off-cycle (direct edit, not /enhance). Two files changed.

| Task | Status | Notes |
|---|---|---|
| Allow independent fractional buys/sells | `[x]` | Button gating now uses `cash > 0` / `shares > 0` instead of `position !== 'long'/'flat'` — users can BUY up to 4× or SELL up to 4× independently |
| Fix AI SELL display when no shares held | `[x]` | `aiEffective` computed before `calculateDay`; AI SELL with no shares → HOLD; display and budget counter use effective action |
| Budget counter guards | `[x]` | Tranche counters use same cash/shares guards so counts are correct |

**Commit:** `5cde347`  
**Files changed:** `dashboard/investgame.html`, `dashboard/js/invest-game/main.js`

---

## Blockers

None

## Notes

- 2026-05-18: Feature implemented directly. Scope narrowed from original requirements to the fractional game-logic bug and AI action display fix.
