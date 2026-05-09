# Invest Game — Engineering Context Reference
# Pre-compiled from Invest_Gamification_Requirements.md + session-handoff.md
# Agents: read this instead of the full requirements doc.

## What it is
Standalone HTML game page (`dashboard/invest-game.html`). User vs RITA AI over 12 trading days (2 warm-up + 10 active). ASML (EUR) or NVIDIA (USD). Starting capital €10,000 / $10,000. One Buy/Sell per active day. Final P&L compared; winner declared. Compliance gate shown live. Run log feeds Ops Agent Builds.

## New Files
| File | Purpose |
|---|---|
| `dashboard/invest-game.html` | Standalone game page — no sidebar, topbar only |
| `dashboard/js/invest-game/main.js` | Game state, table rendering, controls, result card |
| `dashboard/js/invest-game/api.js` | Fetch wrapper; `MOCK_MODE = true` flag |
| `src/rita/api/experience/invest_game.py` | Experience Layer router — 3 endpoints |

## Nav change
`dashboard/index.html` topbar: add **Onboarding** (`onboarding.html`) and **Trial Game** (`invest-game.html`) links.

## Page Layout — 4 Row IDs
| ID | Content | Initial state |
|---|---|---|
| `#row-controls` | Instrument pills, date inputs, Select Days button, New Game button | Always visible |
| `#row-performance` | 3 KPI pills (Instrument, Date Range, Your P&L) + progress bar | `display:none` until days selected |
| `#row-game-table` | 12-row table + result card | Always visible (rows locked until game starts) |
| `#row-compliance` | Compliance gate table — 10 rows (days 3–12) | `display:none` until first active day completes |

## Row 1 — Controls: Key IDs
- `#instrument-group` — capsule pill group; `#pill-asml` (default active), `#pill-nvidia`
- `#start-date` — min `2025-01-01`, default `2025-01-01`
- `#end-date` — max = today minus 3 months; default = max
- `#btn-select-days` — disabled until valid instrument + date range
- `#btn-new-game` — hidden until game starts
- `#selection-label` — hidden span; shown after days selected

## Row 2 — Performance Banner: Key IDs
- `#kpi-instrument`, `#kpi-daterange`, `#kpi-pnl`
- `#progress-fill` (width %), `#progress-label-text` (e.g. "Day 3 of 10")

## Row 3 — Game Table: Key IDs
Table `#game-table`. 12 `<tr>` rows:
- `#game-row-1`, `#game-row-2` — class `warmup`; both selection cols show `—`
- `#game-row-3` … `#game-row-12` — class `active-day locked`; `data-day` attribute
- Per active row: `#buy-{n}`, `#sell-{n}` (disabled), `#ai-cell-{n}` (hidden until user acts)
- Per row data cells: `#row{n}-date`, `#row{n}-instrument`, `#row{n}-price`
- Result card: `#result-card` (`display:none`) — `#result-user-value`, `#result-ai-value`, `#winner-badge`

## Row 4 — Compliance Table: Key IDs
Per active day (3–12): `#comp-row-{n}`, `#comp-date-{n}`, `#comp-action-{n}`, `#comp-status-{n}`, `#comp-rule-{n}`, `#comp-insight-{n}`

## Game Logic Rules
- Warm-up rows (1–2): display immediately on game load; no user action; AI col shows `—`
- Row 3 unlocks after warm-up shown; each subsequent row unlocks after previous day completes
- User selects Buy/Sell → buttons lock → API called → AI action revealed in col 6 → P&L delta shown → compliance row populated → next row unlocks
- AI action withheld until `user_action` is in request body (Phase 2)

## P&L Rules
- Starting: €10,000 (ASML) / $10,000 (NVIDIA)
- Buy = enter at day's close; Sell = exit at day's close
- P&L delta = (exit − entry) × units; warm-up days: no P&L

## API Endpoints (Phase 2)
```
POST /api/experience/invest-game/select-days
  body: { instrument, start_date, end_date }
  returns: { game_id, instrument, currency, warmup_days[2], game_days[10] }

POST /api/experience/invest-game/run-day
  body: { game_id, day_index, user_action }
  returns: { ai_action, compliance_status, compliance_rule, ai_insight, user_pnl_delta, ai_pnl_delta, user_total, ai_total }

GET /api/experience/invest-game/{game_id}/result
  returns: { user_final_value, ai_final_value, winner, day_log[] }
  also writes: project-office/agent-ops/runs/game-run-{timestamp}.json
```

## Mock Data Contract (Phase 1)
`api.js` `MOCK_MODE = true`:
- `selectDays()` → hardcoded 12-day ASML array (dates + close prices)
- `runDay(dayIndex, userAction)` → hardcoded `{ ai_action, compliance_status, compliance_rule, ai_insight, user_pnl_delta, ai_pnl_delta, user_total, ai_total }`
- `getResult()` → hardcoded winner + final values

## CSS Design System (copy from ops.html/index.html)
Fonts: Epilogue (body), IBM Plex Mono (labels/values), Instrument Serif (headings)
Key vars: `--bg:#F5F3EE`, `--surface:#FFF`, `--text:#1A1814`, `--ok:#1A6B3C`, `--danger:#9B1C1C`
Game accent: amber `--game:#B45309`, `--game-bg:#FEF3C7`, `--game-bd:#FCD34D`
Buy: green (`--ok` family). Sell: red (`--danger` family).
Page layout: topbar (52px sticky) + `.game-main` (max-width 1100px, centered, no sidebar)

## Agent AI Chain (Phase 2 — reuse from agent_panel.py)
6 agents: Context → Strategy → Probability → Portfolio Manager → Compliance Gate → Narrator
Key difference from Agent Panel: no HITL pause; AI acts automatically

## Run Log Schema (Phase 2)
Written to `project-office/agent-ops/runs/game-run-{timestamp}.json`
Fields: run_id, app="invest-game", request, skill_file="n/a", agents[], overall_status, branch="n/a"

## Data Files
- ASML: `data/raw/ASML/asml_2001-2026.csv`
- NVIDIA: `data/raw/NVIDIA/` (verify columns at Phase 2 Step 1)
- Date range for game: min `2025-01-01`, max = today minus 3 months

## Out of Scope
NIFTY/BANKNIFTY, game tab in rita.html, leaderboard, mobile PWA, FnO/DS dashboards
