# Invest Game — Session Handoff

**Feature folder:** `project-office/features/invest-game/`
**Requirements:** `Invest_Gamification_Requirements.md` (same folder — read this first each session)
**Enterprise approach:** `project-office/agents/Agentic_AI_Enterprise_Approach.md` — governs how agents are orchestrated, how task briefs are structured, and how the improvement loop works. Every session follows this document.
**Current status:** Requirements agreed. Phase 1 not started.

---

## Agent Orchestration — How This Feature Is Built

This feature follows the multi-agent orchestration pattern from `Agentic_AI_Enterprise_Approach.md` Section 4.

Each phase maps to the 5-role agent chain:

| Role | Agent type | Responsibility in this feature |
|---|---|---|
| **PM** | `general-purpose` | Reads `session-handoff.md` + confirms step is in scope before proceeding |
| **Architect** | `Plan` agent | Designs the exact DOM structure / API contract for the current step before any code is written |
| **Engineer** | `general-purpose` | Writes the code for the current step using the Architect's design |
| **QA** | `general-purpose` | Reads new code, checks against Definition of Done, flags gaps |
| **TechWriter** | `general-purpose` | Updates `session-handoff.md` current phase status + spec files if contracts changed |

**Orchestrator rule (from Section 3.2):** The orchestrator (Claude inline) is a router and sequencer only. It does not make design decisions. It reads the task brief section written by the previous agent before spawning the next.

**Task brief:** A running `task-brief-invest-game.md` in this folder accumulates each agent's output section. Each session appends to it — it becomes the audit trail across all sessions.

**Grounding rule (from Section 11.3):** Each step's Definition of Done checklist must be verified before moving to the next step. Token check doubles as the gate.

---

## Build Sequence

```
Phase 1 → HTML + JS frontend (mock data)   → user approves in browser
Phase 2 → Backend API                      → end-to-end test with real data
Phase 3 → Ops Agent Builds feed            → verify in Ops dashboard
```

**Token discipline:** After every step, pause and ask:
> "Token check — continue to Step X?"
Do not proceed until user confirms.

---

## Phase 1 — Frontend (HTML + JS, mock data)
**Session start instruction:** "Continue invest-game Phase 1 — build the HTML frontend."
**First action:** Read `Invest_Gamification_Requirements.md`, then start Step 1.

| Step | Deliverable | What to build |
|---|---|---|
| **1** | `invest-game.html` — shell | DOCTYPE, `<head>`, CSS variables (copy token/color system from `index.html`), topbar with RITA logo, page title, four empty row containers with IDs: `#row-controls`, `#row-performance`, `#row-game-table`, `#row-compliance`. No content inside rows yet. |
| **2** | `invest-game.html` — Row 1 | Controls bar HTML only: ASML/NVIDIA capsule pills, Start Date input, End Date input, "Select 10 Days at Random" button, selection label `<span>`. All wired with IDs. No JS yet. |
| **3** | `invest-game.html` — Row 2 | Performance banner HTML only: three KPI pill `<div>`s (Instrument, Date Range, Your P&L), progress bar `<div>`. Hidden by default (`display:none`). IDs wired. |
| **4** | `invest-game.html` — Row 3 | Game table HTML only: `<table>` with 12 `<tr>` rows pre-rendered. Rows 1–2 marked warm-up class. Rows 3–12 marked active class, locked state. Buy/Sell toggle buttons in col 5 (disabled). AI selection col 6 placeholder. Result card `<div>` below table (hidden). |
| **5** | `invest-game.html` — Row 4 + CSS polish | Compliance Gate panel HTML only: `<table>` with 10 rows (days 3–12), all empty/hidden. Full CSS pass: spacing, badge styles, capsule pill styles, responsive layout, locked/unlocked row states. |
| **6** | `dashboard/js/invest-game/api.js` | Fetch wrapper. `MOCK_MODE = true` flag. When mock: `selectDays()` returns hardcoded 12-day ASML array. `runDay()` returns hardcoded AI action + compliance status. `getResult()` returns hardcoded winner. When mock is off: real fetch to `/api/experience/invest-game/*`. |
| **7** | `dashboard/js/invest-game/main.js` — init + Row 1 | Import api.js. Wire capsule pill clicks (instrument select). Wire date inputs with min/max validation. Wire "Select 10 Days at Random" button → call `selectDays()` → populate `gameState`. Show selection label. Reveal Row 2 with warm-up data. |
| **8** | `dashboard/js/invest-game/main.js` — game loop | Render warm-up rows (1–2) automatically. Unlock Row 3 active day. Wire Buy/Sell buttons → call `runDay()` → reveal AI action in col 6 → update P&L badge → update compliance panel row → unlock next row. Repeat until day 12. |
| **9** | `dashboard/js/invest-game/main.js` — result + reset | After day 12: call `getResult()` → render result card (user vs AI final value, winner badge). Wire "New Game" button → reset all state, hide result card, re-lock rows, clear compliance panel. Wire `<script type="module">` in HTML. |
| **10** | `dashboard/index.html` — topbar nav | Add two nav links to topbar: "Onboarding" (`onboarding.html`) and "Trial Game" (`invest-game.html`). Minimal styling — match existing topbar link style. Smoke test: open `invest-game.html` in browser, play through mock game end-to-end. |

---

## Phase 2 — Backend API
**Session start instruction:** "Continue invest-game Phase 2 — build the backend API."
**First action:** Read `Invest_Gamification_Requirements.md` + `session-handoff.md`, then start Step 1.
**Prerequisite:** Phase 1 approved by user.

| Step | Deliverable | What to build |
|---|---|---|
| **1** | Data audit | Read NVIDIA CSV: confirm columns, date range, verify Jan 2025 data exists. Note column names vs ASML. Write findings as a comment block at top of `invest_game.py`. |
| **2** | Router scaffold | `src/rita/api/experience/invest_game.py` — router setup, imports, `SESSION_DATA` dict, Pydantic request/response models for all 3 endpoints. No logic yet. |
| **3** | Data loader | `_load_game_data(instrument, start_date, end_date)` function — reads correct CSV for instrument, filters by date range, validates ≥12 trading days exist, returns DataFrame. |
| **4** | `select-days` endpoint | `POST /api/experience/invest-game/select-days` — calls data loader, picks random valid start, slices 12 consecutive days, stores in `SESSION_DATA[game_id]`, returns warmup_days + game_days response. |
| **5** | Agent chain adapter | Extract agent chain from `agent_panel.py` into a shared helper or duplicate + adapt in `invest_game.py` for arbitrary instrument/date. Context Agent, Strategy Agent, Probability Agent. |
| **6** | Compliance Gate + Narrator | Portfolio Manager node (1-lot, no HITL), Compliance Gate node, Narrator Agent node — adapted for invest game. Auto-action, no pause. |
| **7** | `run-day` endpoint | `POST /api/experience/invest-game/run-day` — validates `user_action` present, runs agent chain for that day's price data, updates session P&L for user and AI, returns response with `ai_action` only if `user_action` provided. |
| **8** | `result` endpoint | `GET /api/experience/invest-game/{game_id}/result` — reads session, computes winner, builds `day_log`, returns result response. |
| **9** | Run log writer | Inside result endpoint: write `project-office/agent-ops/runs/game-run-{timestamp}.json` in Agent Builds schema. Register router in `src/rita/main.py`. |
| **10** | Wire frontend + smoke test | In `api.js` set `MOCK_MODE = false`. Start API server. Play through full game in browser. Verify compliance panel populates. Verify `agent-ops/runs/` gets a JSON file. Verify Ops Agent Builds shows the run. |

---

## Phase 3 — Ops Agent Builds Verification
**Session start instruction:** "Continue invest-game Phase 3 — verify Ops Agent Builds feed."
**First action:** Read `session-handoff.md`, then start Step 1.
**Prerequisite:** Phase 2 complete and smoke-tested.

| Step | Deliverable | What to build |
|---|---|---|
| **1** | Schema check | Read `dashboard/js/ops/agent-builds.js` — confirm all fields the dashboard reads. Compare against game run log schema. List any field mismatches. |
| **2** | Fix schema gaps | Update run log writer in `invest_game.py` to include any missing fields identified in Step 1. |
| **3** | Multi-run test | Play 3 games end-to-end. Confirm 3 JSON files appear in `agent-ops/runs/`. |
| **4** | Agent Builds display | Open Ops dashboard → Agent Builds section. Confirm all 3 game runs appear in Run History panel with correct app label `invest-game`. |
| **5** | Compliance metrics | Confirm game runs show compliance pass/warn/fail status correctly in Agent Builds scorecards. |
| **6** | Edge case: all pass | Play a game where no compliance flags fire. Confirm `overall_status: "pass"` in JSON and in dashboard. |
| **7** | Edge case: flagged day | Verify a flagged day shows `pass_with_warnings` in JSON and in dashboard. |
| **8** | `ruff check` | Run `ruff check src/` — fix any issues. |
| **9** | Spec update | Update `Spec_RITA_App.md` (or create `Spec_Invest_Game.md` in specs folder) with new endpoints and data flow. |
| **10** | Handoff close | Update this `session-handoff.md` with "Phase 3 complete". Commit all files. Update PLAN_STATUS.md. |

---

## Key Files to Read at Session Start

| File | Why |
|---|---|
| `project-office/agents/Agentic_AI_Enterprise_Approach.md` | Always — governs agent roles, task brief format, grounding rules, improvement loop |
| `project-office/features/invest-game/Invest_Gamification_Requirements.md` | Always — full feature requirements |
| `project-office/features/invest-game/session-handoff.md` | Always — current phase, next step, phase status |
| `project-office/features/invest-game/task-brief-invest-game.md` | Always — running audit trail; append each agent's section here |
| `src/rita/api/experience/agent_panel.py` | Phase 2 only — agent chain reference |
| `dashboard/js/ops/agent-builds.js` | Phase 3 only — run log schema reference |

---

## Current Phase Status

| Phase | Status | Next step |
|---|---|---|
| Phase 1 — Frontend | Complete (2026-05-06) | All 10 steps done incl. v2 redesign (Hold button, €5k capital, P&L breakdown, tx costs, tax). Files: `investgame.html`, `api.js`, `main.js`, `index.html` nav links. |
| Phase 2 — Backend | Complete (2026-05-06) | All 10 steps done. Commits: `a93a916`, `8edf27d`, `5237e2a`. |
| Phase 3 — Ops feed | Complete (2026-05-06) | All 10 steps done. Key additions: auto-regenerate metrics.json on game complete, Game AI Compliance page in Ops dashboard, retrospective build run logs, ruff fixes, spec updates. |
