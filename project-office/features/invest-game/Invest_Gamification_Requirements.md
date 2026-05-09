# Invest Gamification Feature — Requirements

**Created:** 2026-05-05
**Status:** Requirements Agreed — ready for agent flow
**Owner:** Project Office
**Feature folder:** `project-office/features/invest-game/`

---

## 1. Feature Summary

Add a **Trial Game** experience as a standalone HTML page where users compete against a RITA AI agent making Buy/Sell decisions on a real instrument (ASML or NVIDIA) over 10 randomly selected consecutive trading days. Starting with €10,000 / $10,000, the user makes one Buy/Sell decision per active day; the AI does the same (auto, no HITL confirmation). At the end of 12 days (2 warm-up + 10 active), the final P&L of user vs AI is compared and a winner is declared. Compliance gate status for each AI decision feeds into the Ops Agent Builds dashboard.

---

## 2. Architecture — Separate HTML, New Nav Entries

### 2.1 New Files

| File | Purpose |
|---|---|
| `dashboard/invest-game.html` | Standalone Trial Game page — self-contained HTML |
| `dashboard/js/invest-game/main.js` | Game state, table rendering, controls, result card |
| `dashboard/js/invest-game/api.js` | Fetch wrapper pointing to Experience Layer endpoints |
| `src/rita/api/experience/invest_game.py` | New Experience Layer router — 3 endpoints |

### 2.2 Navigation Changes — `dashboard/index.html`

Add two new entries to the topbar navigation:

| Label | Link |
|---|---|
| **Onboarding** | `onboarding.html` (existing) |
| **Trial Game** | `invest-game.html` (new) |

The "Try Investing Game" button at the end of the onboarding questionnaire also links to `invest-game.html`.

### 2.3 What Does NOT Change

- `dashboard/rita.html` — no new sections, no game tab
- `dashboard/js/rita/ai-compliance.js` — no game tab added
- FnO, Ops, DS dashboards — unchanged

---

## 3. Instruments

First iteration: **ASML (EUR)** and **NVIDIA (USD)** only.

| Instrument | Currency | Data file |
|---|---|---|
| ASML | EUR | `data/raw/ASML/asml_2001-2026.csv` |
| NVIDIA | USD | `data/raw/NVIDIA/` |

NIFTY and BANKNIFTY excluded from this iteration.

The instrument selector on the game page shows only these two options as capsule pills.

---

## 4. Game Page Layout (`invest-game.html`) — Four Rows

---

### Row 1 — Controls Bar

A single horizontal toolbar:

| Element | Detail |
|---|---|
| **Instrument Capsule** | Two pill buttons: `ASML` and `NVIDIA`. Default: ASML |
| **Start Date** | Date input. Minimum: `2025-01-01`. Default: `2025-01-01` |
| **End Date** | Date input. Maximum: today minus 3 months (`2025-02-05` as of 2026-05-05). Default: maximum allowed. Must be at least 10 working days after Start Date |
| **Select Days Button** | Label: `Select 10 Days at Random`. Disabled until instrument and valid date range are set |
| **Selection Label** | Appears after button click: `10 working days selected` |
| **New Game Button** | Appears after game starts. Resets all state |

**Interaction rules:**
- Instrument and date inputs lock (disabled) once days are selected.
- Days are **consecutive** — the API picks a random valid start within the filtered dataset and returns the next 12 available trading days from that point (2 warm-up + 10 active).

---

### Row 2 — Performance Banner

Hidden until days are selected. Shows three KPI pills horizontally:

| Pill | Content |
|---|---|
| **Instrument** | Instrument name + open price of first game day |
| **Date Range** | First game day — Last game day |
| **Your P&L** | Initialised `€0.00` / `$0.00`. Updates after each completed active day |

Thin progress bar below the pills: `Day X of 10`.

---

### Row 3 — Game Table

12-row table. Rows 1–2: warm-up (observe only). Rows 3–12: active game.

#### Columns

| # | Header | Notes |
|---|---|---|
| 1 | **Day** | 1–12 |
| 2 | **Date** | Trading date |
| 3 | **Instrument** | Symbol |
| 4 | **Close Price** | Day's close price |
| 5 | **Your Selection** | Buy / Sell toggle. Disabled for warm-up rows (days 1–2). Locks after selection |
| 6 | **AI Selection** | Hidden until user submits for that day. Warm-up days show `—` automatically |

#### Warm-up Days (Rows 1–2)

- Display immediately when game loads. Both selection columns show `—`.
- No user interaction. Purpose: give price context before the game starts.

#### Active Days (Rows 3–12)

- Row 3 unlocks after warm-up is shown.
- User must select Buy or Sell → submits → API reveals AI action for that day.
- AI never pauses for HITL confirmation (auto action, unlike Agent Panel flow).
- After AI action is revealed: mini P&L delta badge appears in the row. Next row unlocks.
- Continue until all 10 active days complete.

#### Final Result Card (after Row 12)

Appears below the table:

| Field | Content |
|---|---|
| Your final value | Starting capital + cumulative P&L |
| AI final value | Starting capital + AI cumulative P&L |
| Winner | `You Win!` / `AI Wins` / `It's a Draw` badge |

`New Game` button resets to Row 1 state.

---

### Row 4 — Compliance Gate Panel

Live compliance status for each active day as the game progresses.

| Column | Content |
|---|---|
| **Day** | Active day number (3–12) |
| **Date** | Trading date |
| **AI Action** | Buy / Sell (revealed together with Row 3 Col 6) |
| **Compliance Status** | `PASS` or `FLAGGED — [reason]` badge |
| **Rule Evaluated** | Which compliance rule ran (e.g. drawdown gate, position limit) |
| **AI Insight** | One-sentence narrator output for that day |

Uses same badge styles as Agent Panel audit table (`badge ok` / `badge danger`).

---

## 5. AI Decision Logic

Reuses the same 6-agent chain as `src/rita/api/experience/agent_panel.py`, adapted for the selected instrument and game dates:

1. **Context Agent** — reads price regime (Bull / Neutral / Bear) from prior price history
2. **Strategy Agent** — selects stop-loss / target policy
3. **Probability Agent** — filters for statistical edge; returns Buy or Sell signal
4. **Portfolio Manager** — confirms action (no position sizing — simple 1-lot)
5. **Compliance Gate** — passes or flags; records compliance status and rule
6. **Narrator Agent** — one-sentence insight for the compliance panel

**Key difference from Agent Panel:** No HITL pause. The AI takes its action automatically. The compliance gate can flag but the game records the intended action regardless.

**AI concealment:** The `run-day` API response includes `ai_action` only when the request body contains `user_action`. The field is absent if `user_action` is missing.

---

## 6. Starting Capital & P&L Rules

| Rule | Value |
|---|---|
| Starting capital | €10,000 (ASML) / $10,000 (NVIDIA) |
| Position sizing | 1 lot per trade (whole capital in on Buy, all out on Sell) |
| Buy | Enter at day's close price; hold until next Sell |
| Sell | Exit at day's close price |
| P&L delta per row | (Exit price − Entry price) × units held |
| Warm-up days (1–2) | No P&L calculated — observe only |

---

## 7. New API Endpoints

Experience Layer (`/api/experience/invest-game/`, ADR-001 Tier 3, read-only composition).

### 7.1 Select Game Days

```
POST /api/experience/invest-game/select-days
Body:    { instrument: "ASML"|"NVIDIA", start_date: "YYYY-MM-DD", end_date: "YYYY-MM-DD" }
Returns: {
  game_id: str,
  instrument: str,
  currency: "EUR"|"USD",
  warmup_days: [{ date: str, close: float }] × 2,
  game_days:   [{ date: str, close: float }] × 10
}
```

Picks a random valid start within the filtered dataset; returns 12 consecutive trading days. Returns 422 if fewer than 12 trading days exist in the chosen range.

### 7.2 Run Game Day

```
POST /api/experience/invest-game/run-day
Body:    { game_id: str, day_index: int, user_action: "BUY"|"SELL" }
Returns: {
  ai_action:         "BUY"|"SELL",
  compliance_status: str,
  compliance_rule:   str,
  ai_insight:        str,
  user_pnl_delta:    float,
  ai_pnl_delta:      float,
  user_total:        float,
  ai_total:          float
}
```

`ai_action` is absent from the response if `user_action` is not provided in the body.

### 7.3 Get Final Result

```
GET /api/experience/invest-game/{game_id}/result
Returns: {
  user_final_value: float,
  ai_final_value:   float,
  winner:           "user"|"ai"|"draw",
  day_log: [{ date, user_action, ai_action, compliance_status, user_pnl_delta, ai_pnl_delta }]
}
```

Also writes run log JSON to `project-office/agent-ops/runs/game-run-{timestamp}.json`.

---

## 8. Agent Builds Feed (Ops)

At game completion the API writes a run log JSON to `project-office/agent-ops/runs/game-run-{timestamp}.json` following the existing Agent Builds schema. The Ops Agent Builds dashboard picks this up automatically via the existing run-log reader.

```json
{
  "run_id": "game-{timestamp}",
  "app": "invest-game",
  "request": "User vs AI — ASML 2025-01-06 to 2025-01-17",
  "skill_file": "n/a",
  "agents": [
    {
      "role": "compliance-gate",
      "status": "pass_with_warnings",
      "steps_required": 10,
      "steps_completed": 10,
      "adherence_score": 0.9,
      "failure_modes": ["flagged_day_7"]
    }
  ],
  "overall_status": "pass_with_warnings",
  "branch": "n/a"
}
```

---

## 9. Files to Touch

| File | Change |
|---|---|
| `dashboard/index.html` | Add Onboarding + Trial Game links to topbar nav |
| `dashboard/invest-game.html` | **New** — standalone game page |
| `dashboard/js/invest-game/main.js` | **New** — game state, UI, table, result card |
| `dashboard/js/invest-game/api.js` | **New** — fetch wrapper |
| `src/rita/api/experience/invest_game.py` | **New** — Experience Layer router (3 endpoints) |
| `src/rita/main.py` | Register new router |
| `project-office/agent-ops/runs/` | Game run logs written here at session end |

---

## 10. Out of Scope (this iteration)

- NIFTY / BANKNIFTY instruments
- Game tab in RITA app (`rita.html`)
- Game tab in AI Compliance page
- Persistent leaderboard or user accounts
- Mobile PWA changes
- FnO / Ops / DS dashboard changes

---

---

## 12. Requirements Amendment — v2 (2026-05-06)

Post Phase-1 smoke test. The following changes supersede or extend the original requirements.

### 12.1 Hold Action (new)

Add a third action button: **Hold** (do nothing for that day). All three — Buy, Sell, Hold — apply to both user and AI.

- Hold = maintain current position; no transaction; no cost; no tax.
- AI may select Hold in addition to Buy / Sell.
- The compliance gate still runs on AI Hold actions.

### 12.2 Starting Capital

Starting capital changed from €10,000 / $10,000 to **€5,000 / $5,000**.

### 12.3 Transaction Costs and Tax

Apply to every Buy or Sell action (not Hold):

| Parameter | Rate |
|---|---|
| Transaction cost | 0.1% of trade value |
| Capital gains tax | 30% of realised gain (profit on Sell only; only applied if gain > 0) |

Both are deducted from net value at time of the triggering action.

### 12.4 P&L Display — Row 2 Redesign

Replace the three KPI pills (Instrument, Date Range, Your P&L) with two side-by-side P&L cards — one for User, one for AI Agent. Each card shows:

| Field | Description |
|---|---|
| **Cash** | Uninvested cash balance |
| **Portfolio** | Current market value of shares held (shares × current close price) |
| **Transaction Costs** | Cumulative costs paid so far (running total) |
| **Tax** | Cumulative capital gains tax paid so far |
| **Net Value** | Cash + Portfolio − cumulative costs − cumulative tax |

Starting state: Cash = €5,000, Portfolio = €0, Costs = €0, Tax = €0, Net = €5,000.

Updated live after every completed active day. Final values remain displayed when game ends (no separate result card needed — winner declared inside Row 2).

### 12.5 Position Mechanics (long-only model)

| Action | State transition |
|---|---|
| **Buy** | Enter long: spend all cash on shares at day's close price. Deduct transaction cost. |
| **Sell** | Exit long: convert all shares to cash at day's close price. Deduct transaction cost. Apply 30% tax on profit if gain > 0. |
| **Hold** | No transaction. If long: portfolio value = shares × today's close. If flat: cash unchanged. |

Position starts FLAT. Player can only Buy when FLAT; can only Sell when LONG; can Hold in any state.

### 12.6 Row 1 — Selected Date Range Label

After "Select Days" is clicked, display the randomly selected date range (`warmup_day[0].date — game_day[9].date`) inline in Row 1, replacing the `#selection-label` span. Remove the Instrument and Date Range KPI pills from Row 2 (they are now shown in Row 1).

### 12.7 Compliance Panel — Remove Redundant Columns

The compliance table currently has an "AI Action" column header (fixed in Step 10b). No other redundant columns exist — the per-row date is useful. No column removal required beyond what was already fixed.

### 12.8 Navigation Changes

| Page | Change |
|---|---|
| `dashboard/index.html` | **Remove** Trial Game link from topbar. Keep Onboarding only. |
| `dashboard/onboarding.html` | Add Trial Game link (absolute URL using `window.location.origin`). Set via JS on load, not hardcoded `href`. |
| `dashboard/investgame.html` | Onboarding link in topbar also converted to absolute URL via JS. |

Rationale: the game is only offered as a next step from the onboarding flow, not a general dashboard nav item. Absolute URLs ensure links work when served via FastAPI (not opened as local files).

### 12.9 Updated Definition of Done (replaces Section 11)

- [ ] Buy / Sell / Hold buttons present in every active row; Hold locks row and reveals AI action without P&L delta
- [ ] Starting capital €5,000 (EUR or USD depending on instrument)
- [ ] Transaction cost (0.1%) deducted from net value on every Buy or Sell
- [ ] Capital gains tax (30%) deducted from net value on Sell if profit > 0
- [ ] Row 2 shows two P&L cards (User | AI), each with Cash, Portfolio, Costs, Tax, Net Value — updated each day
- [ ] Winner declared in Row 2 after day 12 (no separate result card required)
- [ ] Selected date range displayed in Row 1 after days selected
- [ ] `index.html` topbar has Onboarding link only (Trial Game removed)
- [ ] `onboarding.html` has Trial Game link using absolute server URL (set via JS)
- [ ] Topbar nav links in `investgame.html` use absolute URLs for Onboarding

---

## 11. Definition of Done

- [ ] `index.html` topbar shows Onboarding and Trial Game links
- [ ] "Try Investing Game" button on onboarding page links to `invest-game.html`
- [ ] Instrument capsule shows ASML and NVIDIA only; defaults to ASML
- [ ] Date range: min `2025-01-01`, max ≤ 3 months from today
- [ ] "Select 10 Days at Random" returns 2 warm-up + 10 active consecutive days from real dataset
- [ ] Warm-up rows (1–2) display automatically; both selection columns show `—`
- [ ] Active rows unlock sequentially; user must select before AI is revealed
- [ ] AI acts automatically (no HITL pause)
- [ ] API withholds `ai_action` until `user_action` is in the request body
- [ ] Compliance Gate panel (Row 4) updates after each active day
- [ ] Final result card shows P&L for user and AI; winner declared
- [ ] Run log JSON written to `agent-ops/runs/` at game end; visible in Ops Agent Builds
- [ ] `ruff check` passes; no new JS console errors
- [ ] Spec files updated if API contracts change
