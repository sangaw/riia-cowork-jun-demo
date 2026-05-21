# Task Brief — Invest Game Feature
# Running audit trail — each agent appends its section; never overwrite prior sections.
# Format follows: project-office/agents/Agentic_AI_Enterprise_Approach.md Section 3.3

**Feature:** Invest Gamification
**Created:** 2026-05-05
**Orchestration approach:** `Agentic_AI_Enterprise_Approach.md`
**Skill reference:** `project-office/skills/skill-add-rita-feature.md` (frontend) / `skill-add-endpoint.md` (backend)

---

## Request
User vs AI investing game. Standalone HTML page (`invest-game.html`). ASML and NVIDIA instruments. 10 consecutive trading days (+ 2 warm-up). User makes Buy/Sell per day; AI auto-responds (no HITL). Compliance Gate shown live. Result card at end. Run log feeds Ops Agent Builds.

## App Target
invest-game (new standalone page) + ops (agent-builds feed)

## Spec Reference
`project-office/features/invest-game/Invest_Gamification_Requirements.md`

---

## [PM] Validation
*(Completed by PM agent — 2026-05-05)*

- Sprint alignment: The main PLAN_STATUS.md shows v1.0 released on Day 42 (2026-04-16). All 42 planned days are complete; the project is post-release. This invest-game feature is a new post-v1.0 standalone build, not part of any numbered sprint. It operates outside the 42-day plan under its own feature folder and PLAN_STATUS.md. No conflict with the main sprint scope.
- Risk flags:
  - NVIDIA data availability not yet verified — Phase 2 Step 1 must confirm CSV columns and that Jan 2025 data exists before Step 2 begins; engineer must not assume NVIDIA CSV matches ASML column names.
  - Phase 2 is fully blocked on Phase 1 user approval in browser; no backend work should begin until smoke test passes.
  - Phase 3 is fully blocked on Phase 2 end-to-end smoke test.
  - Agent chain adapter (Phase 2 Steps 5–6) is the highest-complexity step — it reuses `agent_panel.py` logic for an arbitrary instrument; architect must define the adapter boundary clearly before engineer starts.
- Approved to proceed: yes

---

## [Architect] Design — Phase 1 (Frontend)
*(Completed by Architect agent — 2026-05-06)*

- **Feature summary:** A standalone browser game page (`dashboard/investgame.html`) where the user competes against RITA AI over 12 consecutive trading days (2 warm-up + 10 active) on ASML or NVIDIA, starting with €10k/$10k capital and making one Buy/Sell per active day. Phase 1 delivers the complete HTML/JS frontend running entirely in MOCK_MODE with no backend dependency, so the user can approve the experience in-browser before Phase 2 backend work begins.

- **HTML structure decision:** `investgame.html` is a fully self-contained standalone page — no sidebar, no grid shell, no section-loader architecture. It inherits the same CSS custom properties, font stack (Epilogue / IBM Plex Mono / Instrument Serif), and topbar component from `ops.html` and `index.html`, but strips out all sidebar, nav-item, and shell-grid CSS. The layout is a single-column `<main class="game-main">` with `max-width: 1100px` centered, containing four `<section>` elements with IDs `#row-controls`, `#row-performance`, `#row-game-table`, `#row-compliance`. JS is loaded as a single `<script type="module" src="js/invest-game/main.js">` tag at the bottom of `<body>`, with `main.js` importing `api.js`.

- **JS module breakdown:**

| Module | File | Responsibility | Key functions / exports |
|---|---|---|---|
| `api.js` | `dashboard/js/invest-game/api.js` | All data I/O; single source of truth for MOCK_MODE flag | `MOCK_MODE` (boolean const, `true`); `selectDays(instrument, start_date, end_date)` → Promise; `runDay(game_id, day_index, user_action)` → Promise; `getResult(game_id)` → Promise |
| `main.js` | `dashboard/js/invest-game/main.js` | Game state object, all DOM wiring, game loop, result render, reset. Imports `api.js` | `gameState` (module-level object); `initControls()`; `onDaysSelected(data)`; `unlockRow(n)`; `onUserAction(dayIndex, action)`; `renderComplianceRow(n, data)`; `renderResultCard(result)`; `resetGame()` |

- **Mock data contract:** Exact JS object shapes `api.js` must return in MOCK_MODE.

`selectDays()` return value:
```js
{
  game_id: "mock-game-001",
  instrument: "ASML",
  currency: "EUR",
  warmup_days: [
    { date: "2025-01-06", close: 678.50 },
    { date: "2025-01-07", close: 682.10 }
  ],
  game_days: [
    { date: "2025-01-08",  close: 675.30 },
    { date: "2025-01-09",  close: 671.80 },
    { date: "2025-01-10",  close: 680.00 },
    { date: "2025-01-13",  close: 685.40 },
    { date: "2025-01-14",  close: 679.90 },
    { date: "2025-01-15",  close: 692.20 },
    { date: "2025-01-16",  close: 688.70 },
    { date: "2025-01-17",  close: 695.00 },
    { date: "2025-01-20",  close: 701.50 },
    { date: "2025-01-21",  close: 698.30 }
  ]
}
```

`runDay(game_id, day_index, user_action)` return value — keyed by day_index (0–9). Days 0–5 return `compliance_status: "pass"`, day 6 returns `"flagged"`, days 7–9 return `"pass"`. Example day_index 0:
```js
{ ai_action: "BUY", compliance_status: "pass", compliance_rule: "Position limit check",
  ai_insight: "Bull momentum confirmed — entering long at day close.",
  user_pnl_delta: 0, ai_pnl_delta: 0, user_total: 10000.00, ai_total: 10000.00 }
```
Example day_index 6 (flagged):
```js
{ ai_action: "BUY", compliance_status: "flagged", compliance_rule: "Consecutive loss gate",
  ai_insight: "Signal strength marginal — flagged for review but action recorded.",
  user_pnl_delta: 38.20, ai_pnl_delta: -41.00, user_total: 10210.40, ai_total: 9980.10 }
```

`getResult(game_id)` return value:
```js
{
  user_final_value: 10312.80,
  ai_final_value: 10187.50,
  winner: "user",  // "user" | "ai" | "draw"
  day_log: [
    { date: "2025-01-08", user_action: "BUY",  ai_action: "BUY",  compliance_status: "pass",    user_pnl_delta: 0,      ai_pnl_delta: 0 },
    { date: "2025-01-09", user_action: "BUY",  ai_action: "SELL", compliance_status: "pass",    user_pnl_delta: -52.30, ai_pnl_delta: 55.90 },
    { date: "2025-01-10", user_action: "SELL", ai_action: "BUY",  compliance_status: "pass",    user_pnl_delta: 124.50, ai_pnl_delta: -18.20 },
    { date: "2025-01-13", user_action: "BUY",  ai_action: "BUY",  compliance_status: "pass",    user_pnl_delta: 81.00,  ai_pnl_delta: 81.00 },
    { date: "2025-01-14", user_action: "SELL", ai_action: "SELL", compliance_status: "pass",    user_pnl_delta: -33.10, ai_pnl_delta: -33.10 },
    { date: "2025-01-15", user_action: "BUY",  ai_action: "BUY",  compliance_status: "pass",    user_pnl_delta: 182.50, ai_pnl_delta: 182.50 },
    { date: "2025-01-16", user_action: "SELL", ai_action: "BUY",  compliance_status: "flagged", user_pnl_delta: 38.20,  ai_pnl_delta: -41.00 },
    { date: "2025-01-17", user_action: "BUY",  ai_action: "SELL", compliance_status: "pass",    user_pnl_delta: 92.50,  ai_pnl_delta: -28.60 },
    { date: "2025-01-20", user_action: "SELL", ai_action: "SELL", compliance_status: "pass",    user_pnl_delta: -67.00, ai_pnl_delta: -67.00 },
    { date: "2025-01-21", user_action: "BUY",  ai_action: "SELL", compliance_status: "pass",    user_pnl_delta: -53.50, ai_pnl_delta: 55.00 }
  ]
}
```

- **Files to touch:**

| File | Change | What changes |
|---|---|---|
| `dashboard/investgame.html` | New (exists — verify against spec) | Standalone game page — 4 rows, 12 table rows, compliance table, result card, all CSS vars |
| `dashboard/js/invest-game/api.js` | New | Fetch wrapper; `MOCK_MODE = true`; three exported async functions |
| `dashboard/js/invest-game/main.js` | New | Game state + UI logic; imports api.js |
| `dashboard/index.html` | Modify | Add Onboarding + Trial Game links to topbar |

- **Build sequence — Steps 1–10:**

Steps 1–5 are complete (HTML scaffold confirmed in Engineer log). Engineer continues from Step 6:

1. **invest-game.html shell** — DONE
2. **Row 1 HTML** — DONE
3. **Row 2 HTML** — DONE
4. **Row 3 HTML** — DONE
5. **Row 4 + CSS polish** — DONE
6. **`api.js`** — New file. `export const MOCK_MODE = true`. Three exported async functions: `selectDays()`, `runDay(game_id, day_index, user_action)`, `getResult(game_id)`. In mock mode: return hardcoded objects above. In live mode (Phase 2): `fetch(apiBase() + endpoint)` with method/body.
7. **`main.js` init + Row 1** — Import from `./api.js`. Declare `gameState`. `initControls()`: wire pill clicks; set `#end-date` max; wire date change to enable/disable `#btn-select-days`; wire button click → `selectDays()` → render warm-up rows → show `#row-performance` → disable controls → show `#btn-new-game`; wire `#btn-new-game` → `resetGame()`. Call on `DOMContentLoaded`.
8. **`main.js` game loop** — `renderWarmupRows()`: populate warm-up row cells, call `unlockRow(3)`. `unlockRow(n)`: remove `locked` class, enable Buy/Sell, attach click handler. Handler: disable buttons → call `runDay()` → show AI cell → update P&L deltas → update progress bar → call `renderComplianceRow(n, response)` → if n < 12 call `unlockRow(n+1)` else call `endGame()`.
9. **`main.js` result + reset** — `endGame()`: call `getResult()` → populate `#result-user-value`, `#result-ai-value`, set `#winner-badge` text + class (`you-win` / `ai-wins` / `tie`) → show `#result-card`. `resetGame()`: re-lock all active rows, clear all cells to `—`, hide result card, hide compliance section, re-enable controls, reset `gameState`.
10. **`dashboard/index.html` topbar** — Add two `<a class="t-nav-link">` links: Onboarding → `onboarding.html`, Trial Game → `invest-game.html`. Smoke test: play full mock game end-to-end in browser.

- **Definition of Done — Phase 1:**

- [ ] `investgame.html` opens in browser with zero console errors on load
- [ ] ASML pill active by default; NVIDIA pill click switches selection without page reload
- [ ] `#btn-select-days` disabled on invalid date range; enabled on valid range
- [ ] Clicking Select Days: reveals `#row-performance` with instrument, date range, €0 P&L; disables instrument + date controls; shows `#btn-new-game`; shows `#selection-label`
- [ ] Warm-up rows 1–2 populated (date, instrument, price); row 3 Buy/Sell buttons enabled; rows 4–12 locked
- [ ] Playing all 10 active days: each Buy/Sell click reveals AI action col 6, updates P&L delta cells, updates progress bar, populates compliance panel row; day 7 shows `flagged` badge in compliance panel
- [ ] After day 12: result card appears with formatted currency values and winner badge with correct class
- [ ] `#row-compliance` visible from day 1 completion; all 10 rows shown at game end
- [ ] `#btn-new-game` click fully resets page to initial state (rows locked, cells cleared, result card hidden, controls enabled)
- [ ] `dashboard/index.html` topbar contains Onboarding and Trial Game links styled as `.t-nav-link`

- **Note for Phase 2 Architect:** The Ops Agent Builds dashboard reads run JSON files via `dashboard/js/ops/agent-builds.js`. It consumes `r.run_id`, `r.app`, `r.request`, `r.overall_status`, `r.agents[].status`, `r.agents[].token_estimate`, `r.agents[].role`, `r.duration_minutes`, and `r.branch` from each run. The `token_estimate` and `role` fields are required by the charts but are absent from the requirements schema — Phase 2 Architect must read `agent-builds.js` in full before designing the run log writer, and must reconcile the file path (`project-office/agent-ops/runs/`) vs the static-file route the dashboard fetches from.

---

## [Engineer] Implementation Log — Phase 1
*(Append one entry per completed step)*

**Phase 1 v2 — JS rewrite for Hold + P&L breakdown** *(2026-05-06)*
- Rewrote `api.js` — simplified mock returns only AI action + compliance fields; `starting_capital: 5000` added to selectDays mock; 10-day AI array includes HOLD on days 3 and 6 (day 6 flagged).
- Rewrote `main.js` — new gameState with user/ai actor objects; `calculateDay()` pure position state machine (flat↔long, tx cost 0.1%, tax 30% on profit); `renderPnLCards()` updates all 10 P&L card IDs; `handleUserAction()` wires Hold button, computes deltas, updates all Row 2 IDs; `endGame()` shows #winner-section in Row 2; `resetGame()` clears all 45+ IDs including hold-{n} buttons; no reference to removed IDs (kpi-instrument, kpi-daterange, kpi-pnl, result-card).
- Added `.ai-cell.ai-hold { color: var(--t2); }` CSS to `investgame.html`.
- Ready for user browser smoke test.

**Steps 6–10 — api.js + main.js + nav** *(2026-05-06)*
- Created `dashboard/js/invest-game/api.js` — MOCK_MODE=true, three exported async functions, full mock data for 10 days (day index 6 = flagged compliance).
- Created `dashboard/js/invest-game/main.js` — gameState, initControls, renderWarmupRows, unlockRow, handleUserAction, renderComplianceRow, endGame, resetGame all implemented.
- Modified `dashboard/index.html` — added Onboarding and Trial Game nav links to topbar.
- Fixed `dashboard/investgame.html` — compliance-table header "Your Action" corrected to "AI Action".
- Phase 1 Steps 6–10 complete. Ready for user browser smoke test.

**Step 1–5 — invest-game.html scaffold** *(2026-05-05)*
- Created `dashboard/invest-game.html` — standalone page, no sidebar, topbar only.
- All 4 row IDs present: `#row-controls`, `#row-performance`, `#row-game-table`, `#row-compliance`.
- CSS vars copied from ops.html; game amber accent added (`--game`, `--game-bg`, `--game-bd`, `--game-light`).
- Row 1: instrument pill group (`#pill-asml` active, `#pill-nvidia`), date inputs (`#start-date`, `#end-date`), `#btn-select-days` (disabled), `#btn-new-game` (hidden), `#selection-label` (hidden).
- Row 2: `#kpi-instrument`, `#kpi-daterange`, `#kpi-pnl`; `#progress-fill`, `#progress-label-text`; section hidden.
- Row 3: `#game-table` with 12 rows — rows 1–2 class `warmup`, rows 3–12 class `active-day locked` with `data-day` attr; `#buy-{n}`, `#sell-{n}`, `#ai-cell-{n}`, `#row{n}-date`, `#row{n}-instrument`, `#row{n}-price`, `#row{n}-user-delta`, `#row{n}-ai-delta`; `#result-card` hidden with `#result-user-value`, `#result-ai-value`, `#winner-badge`.
- Row 4: `#compliance-table` 10 rows (3–12) all `display:none`; `#comp-row-{n}`, `#comp-date-{n}`, `#comp-action-{n}`, `#comp-status-{n}`, `#comp-rule-{n}`, `#comp-insight-{n}`; section hidden.
- Script tag: `js/invest-game/main.js` (module).
- **Next:** Steps 6–7 (`api.js` + `main.js`) — token check passed?

---

## [QA] Test Results — Phase 1
*(Recorded 2026-05-06)*

- Steps verified: Steps 1–10 complete including v2 redesign (Hold button, €5k capital, tx costs, tax, P&L cards)
- Browser smoke test: **pass** — user confirmed 2026-05-06
- Console errors: none reported
- Mock game playable end-to-end: yes

---

## [TechWriter] Documentation — Phase 1
*(To be completed after QA sign-off)*

- `session-handoff.md` Phase 1 status updated:
- Spec files updated:

---

## [Architect] Design — Phase 2 (Backend)
*(Completed by Architect agent — 2026-05-06)*

### 1. Data Audit Findings

- **ASML:** `data/raw/ASML/asml_2001-2026.csv` — columns: `date, Open, High, Low, Close, Volume` (lowercase `date`)
- **NVIDIA:** `data/raw/NVIDIA/nvda_daily_25yr_rounded.csv` — columns: `Date, Open, High, Low, Close, Volume` (capital `Date`)
- **Critical diff:** ASML=`date`, NVIDIA=`Date`. Normalize with `df.columns = [c.lower() for c in df.columns]` (same pattern as `agent_panel.py`).
- **Jan 2025 data:** Present in both. ASML: ~20 trading days. NVIDIA: 19–20 days (2025-01-09 absent — market gap, not a data error).
- **Game columns needed:** `date` and `close` (both available after normalization).

### 2. Router Scaffold

**File:** `src/rita/api/experience/invest_game.py`

```python
from __future__ import annotations
import json, uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Literal
import pandas as pd
import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

log = structlog.get_logger()
router = APIRouter(prefix="/api/experience/invest-game", tags=["invest-game"])
SESSION_DATA: dict[str, dict] = {}
```

SESSION_DATA per game_id:
```python
{
    "instrument": str, "currency": str,
    "warmup_days": list[{"date": str, "close": float}],  # len=2
    "game_days":   list[{"date": str, "close": float}],  # len=10
    "day_log":     list[dict],   # grows as run-day called
    "started_at":  str,          # ISO UTC timestamp
}
```

**Pydantic models:**

| Model | Fields |
|---|---|
| `SelectDaysRequest` | `instrument: Literal["ASML","NVIDIA"]`, `start_date: str`, `end_date: str` |
| `DayEntry` | `date: str`, `close: float` |
| `SelectDaysResponse` | `game_id: str`, `instrument: str`, `currency: str`, `starting_capital: float`, `warmup_days: List[DayEntry]`, `game_days: List[DayEntry]` |
| `RunDayRequest` | `game_id: str`, `day_index: int` (0–9), `user_action: Literal["BUY","SELL","HOLD"]` |
| `RunDayResponse` | `ai_action: Literal["BUY","SELL","HOLD"]`, `compliance_status: Literal["pass","flagged"]`, `compliance_rule: str`, `ai_insight: str` |
| `DayLogEntry` | `date: str`, `user_action: str`, `ai_action: str`, `compliance_status: str` |
| `ResultResponse` | `winner: str`, `day_log: List[DayLogEntry]` |

### 3. Data Loader

```python
_DATA_ROOT = Path(__file__).parent.parent.parent.parent.parent / "data" / "raw"
_CSV_PATHS = {
    "ASML":   _DATA_ROOT / "ASML"   / "asml_2001-2026.csv",
    "NVIDIA": _DATA_ROOT / "NVIDIA" / "nvda_daily_25yr_rounded.csv",
}

def _load_game_data(instrument: str, start_date: str, end_date: str) -> pd.DataFrame:
    df = pd.read_csv(_CSV_PATHS[instrument])
    df.columns = [c.lower() for c in df.columns]
    df["date"] = pd.to_datetime(df["date"])
    df = df[(df["date"] >= pd.to_datetime(start_date)) &
            (df["date"] <= pd.to_datetime(end_date))].reset_index(drop=True)
    if len(df) < 12:
        raise HTTPException(422, "Fewer than 12 trading days in selected range.")
    return df[["date", "close"]].copy()
```

### 4. select-days Endpoint

- `POST /api/experience/invest-game/select-days`
- Calls `_load_game_data()`; picks `random.randint(0, len(df)-12)` as start index; slices 12 rows.
- Rows 0–1 → `warmup_days`; rows 2–11 → `game_days`.
- Stores full session in `SESSION_DATA[game_id]`.
- Returns `SelectDaysResponse` with `starting_capital=5000.0` (fixed per Phase 1 v2 design).

### 5. Agent Chain Adapter (Steps 5–6)

**Design decision:** No LangGraph, no MemorySaver, no HITL. Six agents run as plain synchronous Python functions chained sequentially inside `async def run_agent_chain(...)`.

**GameAgentState (TypedDict):**
`instrument, close_price, prev_close, user_action, regime, policy, probability, proposal (dict), compliance_status, compliance_rule, ai_insight, logs`

**Agent responsibilities:**

| Agent | Reads | Writes |
|---|---|---|
| `game_context_agent` | `close_price`, `prev_close` | `regime` (same 4 labels as agent_panel.py) |
| `game_strategy_agent` | `regime` | `policy` (same mapping) |
| `game_probability_agent` | `regime` | `probability` (same thresholds: 0.65/0.35/0.82) |
| `game_portfolio_manager_agent` | `probability` | `proposal = {"action": BUY/SELL/HOLD}` — if >0.70: BUY; <0.40: SELL; else HOLD |
| `game_compliance_gate` | `regime`, `probability` | `compliance_status` ("pass"/"flagged"), `compliance_rule` — flag if High Volatility AND prob<0.40 |
| `game_narrator_agent` | `regime`, `probability`, `proposal`, `compliance_status` | `ai_insight` (1–2 sentence string) |

**prev_close source:**
- `day_index == 0`: `SESSION_DATA[game_id]["warmup_days"][-1]["close"]`
- `day_index > 0`: `SESSION_DATA[game_id]["game_days"][day_index-1]["close"]`

**Returns:** `{ ai_action, compliance_status, compliance_rule, ai_insight }`

### 6. run-day Endpoint

- `POST /api/experience/invest-game/run-day`
- Validates: `game_id` in SESSION_DATA (404); `day_index` 0–9 (400); sequence check: `len(day_log) == day_index` (409 if mismatch).
- Calls `await run_agent_chain(...)`.
- Appends `{ date, user_action, ai_action, compliance_status }` to `SESSION_DATA[game_id]["day_log"]`.
- Returns `RunDayResponse` — **no financial fields** (main.js owns all P&L via `calculateDay()`).

### 7. result Endpoint

- `GET /api/experience/invest-game/{game_id}/result`
- Returns `{ winner: "draw", day_log: [...] }` — `winner` is a placeholder; main.js determines winner from `gameState`.
- Side effect: calls `_write_run_log(game_id, session)` before returning.

### 8. Run Log Writer

**CRITICAL path correction:** eng-context.md says `project-office/agent-ops/runs/` — this is WRONG. The Ops dashboard static mount serves `/agent-ops-data` → `riia-ai-org/agent-ops`. Files must go to:
```
riia-ai-org/agent-ops/runs/run-{timestamp}.json
```
File naming: `run-{YYYYMMDD-HHMM}.json` (matches `agent-builds.js` fetch pattern `/agent-ops-data/runs/run-{id}.json`).

**Required fields (from agent-builds.js audit):**

| Field | Value |
|---|---|
| `run_id` | `datetime.now().strftime("%Y%m%d-%H%M")` |
| `app` | `"invest-game"` |
| `request` | `f"Invest game: {instrument} over {len(day_log)} days"` |
| `skill_file` | `"n/a"` |
| `overall_status` | `"pass"` if no flagged days; `"pass_with_warnings"` if any day flagged |
| `total_tokens_estimated` | sum of agent token_estimates |
| `duration_minutes` | computed from `started_at` to now |
| `branch` | `"n/a"` |
| `merge_status` | `"n/a"` |
| `merge_commit` | `null` |
| `agents` | Array — 5 entries mapping to dashboard ROLES (pm/architect/engineer/qa/techwriter) with synthetic token estimates (800/600/500/700/400); techwriter status = `pass_with_warnings` if any day flagged |

Write is synchronous, wrapped in try/except — log error with structlog on failure but do NOT raise HTTPException (game result must still return to user).

### 9. main.py Registration

```python
# import (after agent_panel_router import):
from rita.api.experience.invest_game import router as invest_game_router
# include_router (after agent_panel_router include):
app.include_router(invest_game_router)
```

No auth dependency — consistent with `agent_panel_router`.

### 10. Files to Create/Modify

| File | Create or Modify | Description |
|---|---|---|
| `src/rita/api/experience/invest_game.py` | Create | Full router: all imports, SESSION_DATA, Pydantic models, data loader, agent chain, 3 endpoints, run log writer |
| `src/rita/main.py` | Modify | Add import + include_router for invest_game_router |
| `dashboard/js/invest-game/api.js` | Modify (Step 10 only) | Set MOCK_MODE = false for live wiring |

### 11. Edge Cases

1. **Date range < 12 trading days** — `_load_game_data` raises 422; `api.js` must show error to user (not leave button in loading state).
2. **Stale game_id after server restart** — SESSION_DATA is in-memory only; returns 404; `main.js` must call `resetGame()` on 404.
3. **run-day called out of sequence** — sequence guard: `len(day_log) != day_index` → 409 Conflict.
4. **NVIDIA 2025-01-09 gap** — not a real gap; CSV simply has no row for that calendar date (trading holiday); DataFrame only contains actual trading days; no handling needed.
5. **Run log write failure** — wrap in try/except; log with structlog; never raise HTTPException.

### 12. Definition of Done — Phase 2

- [ ] Step 1: Data audit complete — findings as comment block at top of `invest_game.py`
- [ ] Step 2: Router scaffold — models, SESSION_DATA, imports, no logic yet
- [ ] Step 3: Data loader — reads correct CSV, normalizes, filters, validates ≥12 days
- [ ] Step 4: select-days endpoint — random 12-day block, SESSION_DATA stored, response matches contract
- [ ] Step 5: Agent chain (Context, Strategy, Probability) — sequential pipeline, no LangGraph
- [ ] Step 6: Agent chain (Portfolio Manager, Compliance Gate, Narrator) — PM returns BUY/SELL/HOLD; compliance uses volatility rule; narrator produces ai_insight
- [ ] Step 7: run-day endpoint — validates game_id + sequence + user_action; calls chain; stores day_log; returns 4 fields only
- [ ] Step 8: result endpoint — returns winner + day_log; triggers run log write
- [ ] Step 9: Run log to `riia-ai-org/agent-ops/runs/run-{ts}.json`; all required fields; router in main.py
- [ ] Step 10: MOCK_MODE=false; full browser smoke test; run JSON in correct dir; Ops Agent Builds shows run

---

## [Architect] Design — Phase 1 v2 (JS Redesign for Hold + P&L Breakdown)
*(Completed by Architect agent — 2026-05-06)*

**Trigger:** User approved Phase 1 layout, then added requirements: Hold button, €5k starting capital, transaction costs (0.1%), capital gains tax (30%), two-column P&L breakdown replacing KPI pills, winner in Row 2.

- **Calculation responsibility:** Option A — main.js calculates ALL financials for both user and AI. api.js mock returns only `ai_action`, `compliance_status`, `compliance_rule`, `ai_insight`. Reason: mock cannot pre-bake user financials since user action is variable. Phase 2 backend will return full breakdown; main.js switches from computing to rendering.

- **gameState object:**
```
gameState = {
  gameId: null, instrument: 'ASML', currency: 'EUR', startingCapital: 5000,
  warmupDays: [], gameDays: [], currentDayIndex: 0, started: false,
  user: { position:'flat', cash:5000, shares:0, entryPrice:0, portfolio:0, cumCosts:0, cumTax:0, netValue:5000, prevNetValue:5000 },
  ai:   { position:'flat', cash:5000, shares:0, entryPrice:0, portfolio:0, cumCosts:0, cumTax:0, netValue:5000, prevNetValue:5000 }
}
```

- **calculateDay(actor, action, closePrice) — pure function, mutates actor:**
  - BUY (flat→long): txCost = cash×0.001; cumCosts+=txCost; shares=(cash−txCost)/close; cash=0; entryPrice=close; position='long'
  - BUY (already long): treat as HOLD
  - SELL (long→flat): proceeds=shares×close; txCost=proceeds×0.001; cumCosts+=txCost; grossProfit=shares×(close−entryPrice); if grossProfit>0: tax=grossProfit×0.30; cumTax+=tax; cash=proceeds−txCost−tax; shares=0; entryPrice=0; position='flat'
  - SELL (already flat): treat as HOLD
  - HOLD (any): no changes to cash/shares/costs/tax
  - After all branches: portfolio=shares×close; netValue=cash+portfolio−cumCosts−cumTax

- **api.js mock contract — selectDays() return:** Same shape as before + `starting_capital: 5000` field added.

- **api.js mock — 10-day AI action array (day_index 0–9):**
  - 0:BUY/pass, 1:SELL/pass, 2:BUY/pass, 3:HOLD/pass, 4:SELL/pass, 5:BUY/pass, 6:HOLD/flagged, 7:SELL/pass, 8:SELL/pass, 9:SELL/pass
  - Days 3 and 6 test HOLD path; day 6 tests flagged compliance on HOLD

- **api.js mock contract — runDay() return:** `{ ai_action, compliance_status, compliance_rule, ai_insight }` only. No financial fields — main.js computes all.

- **api.js mock contract — getResult() return:** `{ winner: 'user' }` stub only — main.js determines winner from gameState.

- **unlockRow(n):** Wire `hold-{n}.onclick = () => handleUserAction(n, 'HOLD')`. Hold follows identical lock+selected pattern as Buy/Sell.

- **handleUserAction(n, action) steps:** (1) lock all 3 buttons; (2) mark selected; (3) save prevNetValue for user+ai; (4) calculateDay(user, action, close); (5) await runDay(); (6) calculateDay(ai, result.ai_action, close); (7) update ai-cell (BUY/SELL/HOLD + class ai-buy/ai-sell/ai-hold); (8) compute deltas, show "—" for flat+HOLD+zero-delta; (9) renderPnLCards(); (10) update progress; (11) renderComplianceRow(); (12) unlockRow(n+1) or endGame().

- **renderPnLCards():** Update #user-cash, #user-portfolio, #user-costs (−€X), #user-tax (−€X), #user-net (+ pos/neg class). Same for #ai-*. Read directly from gameState. Call once on game start to show initial €5,000.

- **endGame():** await getResult(); compare gameState.user.netValue vs gameState.ai.netValue; set #winner-badge text+class; show #winner-section. No reference to #result-card.

- **resetGame() — IDs to clear:** gameState reset + Row1 controls + #selection-label div + 3 inner span IDs + Row2 all pnl IDs + #winner-section + #progress-* + #row-performance + warmup rows 1–2 + active rows 3–12 (buy/sell/hold buttons + ai-cell + data cells + delta cells) + compliance section + all comp-row-{n} + comp-cell IDs.

- **New CSS rule needed in investgame.html:** `.ai-cell.ai-hold { color: var(--t2); }` — neutral color for Hold action.

- **fmtSigned(value, currency):** +€X.XX / −€X.XX (Unicode minus U+2212) / €0.00. Used for delta cells.

- **Definition of Done — v2:** Zero console errors; selection label shows 3 inner spans; P&L cards initialise at €5,000; Hold button wires and locks correctly; ai-cell shows HOLD with ai-hold class; delta shows "—" for flat+HOLD; tx cost 0.1% accumulates correctly; tax 30% on profitable sell only; winner in #winner-section after day 12; full reset including hold-{n} buttons.

---

## [Engineer] Implementation Log — Phase 2
*(Append one entry per completed step)*

**Phase 2 — Backend implementation** *(2026-05-06)*
- Branch: worktree-agent-a7c7112115ff85c39
- Worktree: C:/Users/Sandeep/Documents/Work/code/riia-cowork-jun/.claude/worktrees/agent-a7c7112115ff85c39
- Commit: a93a916
- Files created: src/rita/api/experience/invest_game.py
- Files modified: src/rita/main.py
- Ruff: passed
- DoD checklist:
  - [x] Step 1: Data audit comment block present
  - [x] Step 2: Router scaffold with all models
  - [x] Step 3: _load_game_data() implemented
  - [x] Step 4: select-days endpoint
  - [x] Step 5: Agent chain (Context, Strategy, Probability)
  - [x] Step 6: Agent chain (PM, Compliance Gate, Narrator)
  - [x] Step 7: run-day endpoint
  - [x] Step 8: result endpoint
  - [x] Step 9: Run log writer + main.py registration
  - [ ] Step 10: Frontend wire + smoke test (deferred — requires running server)

---

## [QA] Test Results — Phase 2

---

## [TechWriter] Documentation — Phase 2

---

## [QA] Test Results — Phase 3 (Ops feed)

---

## [TechWriter] Documentation — Phase 3 (Close)
