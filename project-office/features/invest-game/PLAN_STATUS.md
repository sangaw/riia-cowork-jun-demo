# Invest Game — Feature Plan Status
**Last updated:** 2026-05-06

---

## Feature Goal
Build a standalone User vs RITA AI investing game (`invest-game.html`) where the user makes Buy/Sell decisions over 10 active trading days on ASML or NVIDIA, with live compliance gate and final P&L result card.

---

## Build Sequence

```
Phase 1 → HTML + JS frontend (mock data)   → user approves in browser
Phase 2 → Backend API                      → end-to-end test with real data
Phase 3 → Ops Agent Builds feed            → verify in Ops dashboard
```

---

## Phase 1 — Frontend (HTML + JS, mock data)

| Step | Deliverable | Status |
|---|---|---|
| 1 | `invest-game.html` — shell (DOCTYPE, head, CSS vars, topbar, 4 empty row containers) | Done (2026-05-05) |
| 2 | `invest-game.html` — Row 1 (Controls bar HTML: pills, date inputs, Select Days button, selection label) | Done (2026-05-05) |
| 3 | `invest-game.html` — Row 2 (Performance banner HTML: 3 KPI pills, progress bar; hidden by default) | Done (2026-05-05) |
| 4 | `invest-game.html` — Row 3 (Game table HTML: 12 pre-rendered rows, warm-up + active classes, Buy/Sell buttons, result card) | Done (2026-05-05) |
| 5 | `invest-game.html` — Row 4 + CSS polish (Compliance Gate panel: 10 rows; full CSS: spacing, badges, capsule pills, locked/unlocked states) | Done (2026-05-05) |
| 6 | `dashboard/js/invest-game/api.js` (Fetch wrapper; `MOCK_MODE = true`; `selectDays()`, `runDay()`, `getResult()` mock + real branches) | Done (2026-05-06) |
| 7 | `dashboard/js/invest-game/main.js` — init + Row 1 (pill clicks, date validation, Select Days → `selectDays()`, reveal Row 2) | Done (2026-05-06) |
| 8 | `dashboard/js/invest-game/main.js` — game loop (warm-up rows, unlock active rows, Buy/Sell → `runDay()`, reveal AI action, update P&L + compliance) | Done (2026-05-06) |
| 9 | `dashboard/js/invest-game/main.js` — result + reset (`getResult()` → result card, New Game reset, `<script type="module">` wired) | Done (2026-05-06) |
| 10 | `dashboard/index.html` — topbar nav (add Onboarding + Trial Game links; smoke test mock game end-to-end) | Done (2026-05-06) |

---

## Phase 2 — Backend API

| Step | Deliverable | Status |
|---|---|---|
| 1 | Data audit (read NVIDIA CSV, confirm columns + date range, verify Jan 2025 data, note vs ASML; write findings as comment block in `invest_game.py`) | Done (2026-05-06) |
| 2 | Router scaffold (`src/rita/api/experience/invest_game.py` — router, imports, `SESSION_DATA` dict, Pydantic models for 3 endpoints) | Done (2026-05-06) |
| 3 | Data loader (`_load_game_data(instrument, start_date, end_date)` — reads CSV, filters dates, validates ≥12 days, returns DataFrame) | Done (2026-05-06) |
| 4 | `select-days` endpoint (`POST /api/experience/invest-game/select-days` — data loader, random valid start, 12-day slice, `SESSION_DATA` store, response) | Done (2026-05-06) |
| 5 | Agent chain adapter (Context, Strategy, Probability agents — sequential pipeline, no LangGraph) | Done (2026-05-06) |
| 6 | Compliance Gate + Narrator (Portfolio Manager, Compliance Gate, Narrator — auto-action, no HITL) | Done (2026-05-06) |
| 7 | `run-day` endpoint (`POST /api/experience/invest-game/run-day` — validates user_action + sequence, runs agent chain, returns ai_action + compliance) | Done (2026-05-06) |
| 8 | `result` endpoint (`GET /api/experience/invest-game/{game_id}/result` — reads session day_log, triggers run log write, returns winner + day_log) | Done (2026-05-06) |
| 9 | Run log writer (`riia-ai-org/agent-ops/runs/run-{ts}.json` in Agent Builds schema; router registered in `main.py`; commit 8edf27d) | Done (2026-05-06) |
| 10 | Wire frontend + smoke test (`MOCK_MODE = false`, start API, play full game, verify compliance panel + run log JSON + Ops Agent Builds display) | Done (2026-05-06) |

---

## Phase 3 — Ops Agent Builds Verification

| Step | Deliverable | Status |
|---|---|---|
| 1 | Schema check (read `agent-builds.js`, confirm all fields dashboard reads, compare against game run log schema, list mismatches) | Done (2026-05-06) — no gaps found |
| 2 | Fix schema gaps (update run log writer in `invest_game.py` to include any missing fields) | Done (2026-05-06) — no gaps; `day_log` + `compliance_rule` + `ai_insight` added proactively |
| 3 | Multi-run test (play 3 games, confirm 3 JSON files appear in `agent-ops/runs/`) | Done (user verified) |
| 4 | Agent Builds display (open Ops dashboard → Agent Builds, confirm 3 game runs appear with `invest-game` app label) | Done (2026-05-06) — metrics.json regenerated; game sessions filtered out of pipeline scorecards |
| 5 | Compliance metrics (confirm game runs show compliance pass/warn/fail status correctly in Agent Builds scorecards) | Done (2026-05-06) — defect fixed: auto-regenerate metrics.json after each game |
| 6 | Edge case: all pass (play game with no compliance flags; confirm `overall_status: "pass"` in JSON + dashboard) | Done (user verified) |
| 7 | Edge case: flagged day (verify flagged day shows `pass_with_warnings` in JSON + dashboard) | Done (user verified) |
| 8 | `ruff check` (run `ruff check src/` — fix any issues) | Done (2026-05-06) — 18 errors fixed across 5 files |
| 9 | Spec update (update `Spec_RITA_App.md` or create `Spec_Invest_Game.md` with new endpoints and data flow) | Done (2026-05-06) — `Spec_RITA_App.md` + `Spec_JS_Code.md` updated |
| 10 | Handoff close (update `session-handoff.md` with "Phase 3 complete"; commit all files; update PLAN_STATUS.md) | Done (2026-05-06) |

---

## Current Blockers

_None_

---

## Session Log

| Date | Note |
|---|---|
| 2026-05-05 | Phase 1 starting |
| 2026-05-06 | Phase 1 Steps 6–10 complete — api.js, main.js, index.html nav, investgame.html compliance header fix |
| 2026-05-06 | Phase 2 complete — backend API, agent chain, run log writer, MOCK_MODE=false |
| 2026-05-06 | Phase 3 complete — schema check, ruff fixes, spec updates, retrospective run logs, Game AI Compliance page added to Ops dashboard |
