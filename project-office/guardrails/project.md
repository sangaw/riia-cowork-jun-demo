# Project Guardrails — RITA

**Scope:** RITA-specific — applies to all agents working on `riia-jun-release/` code.  
**Load order:** Load after `org.md` and after the relevant role guardrail.  
**Version:** v1 (2026-05-26)

---

## 1. API Tier Routing (ADR-001)

Dashboard JS **must only call** Experience or Workflow tier endpoints. Calling system-tier routes directly from JS is a compliance violation.

| Path pattern | Status | Notes |
|---|---|---|
| `/api/v1/experience/*` | ✅ Allowed | Experience tier — all dashboards |
| `/api/experience/*` | ✅ Allowed | Experience tier (ops prefix variant) |
| `/api/v1/portfolio/*` | ✅ Allowed | Portfolio / FnO tier |
| `/api/v1/chat*`, `/api/v1/commentary`, `/api/v1/instrument/*` | ✅ Allowed | Workflow/chat operations |
| `/api/v1/train`, `/api/v1/backtest`, `/api/v1/pipeline`, `/api/v1/goal`, `/api/v1/market`, `/api/v1/strategy` | ✅ Allowed | Pipeline workflow operations |
| `/api/v1/agent-panel/*`, `/api/v1/mcp-calls` | ✅ Allowed | Agent/MCP read |
| `/health`, `/progress`, `/reset` | ✅ Allowed | App-root routes |
| `/api/v1/market-signals`, `/api/v1/shap` | ✅ Allowed | Raw indicators/ML artifacts |
| `/api/experience/ops/drift` | ✅ Allowed | Experience-tier drift/health checks (use this, not `/api/v1/drift`) |
| `/api/v1/drift` | ❌ Never from JS | System tier — use `/api/experience/ops/drift` (Feature 18 gap-close) |
| `/api/v1/backtest-daily` | ❌ Never from JS | System tier — use `/api/v1/experience/rita/backtest-daily` |
| `/api/v1/risk-timeline` | ❌ Never from JS | System tier — use `/api/v1/experience/rita/risk-timeline` |
| `/api/v1/training-history` | ❌ Never from JS | System tier — use `/api/v1/experience/rita/training-history` |

**Tier decision tree — use the first rule that matches:**

| If the endpoint... | Tier | Directory |
|---|---|---|
| Reads or writes exactly ONE table, no logic | System | `src/rita/api/v1/system/<resource>.py` |
| Orchestrates a multi-step or ML workflow | Workflow | `src/rita/api/v1/workflow/<process>.py` |
| Composes a read-only UI payload from multiple sources | Experience | `src/rita/api/experience/<section>.py` |

## 2. Lot Sizes

- **NIFTY lot size = 75, BANKNIFTY lot size = 30.**
- These values must never be hardcoded in application code.
- Always read from `settings.instruments.nifty.lot_size` and `settings.instruments.banknifty.lot_size`.
- Any ADR or design document that touches lot sizes must include this note explicitly.

## 3. Protected Modules

- `core/` modules must not be modified unless QA has run the Greeks reference tests first.
  - Greeks reference tests validate Delta/Gamma/Theta/Vega against Black-Scholes reference values.
  - If tests are not available, flag to the user and do not proceed.

## 4. Workspace Paths

| Path | Status | Rule |
|---|---|---|
| `riia-jun-release/rita_input/` | Read-only | Never write, delete, or modify |
| `riia-jun-release/rita_output/` | Writable | Models, results, trade logs |
| `riia-jun-release/dashboard/` | App frontend | HTML + JS; read via spec, not directly for large files |
| `project-office/` | Project meta | Specs, skills, agent cards, scripts — not application code |

## 5. HTML File Conventions

- `rita.html` (~4,000 lines), `fno.html` (~3,500 lines), `mobileapp/index.html` — never read directly.
- Use the corresponding Spec file (`Spec_HTML_Code.md`, `Spec_Mobile_App.md`) for structure reference.
- When adding a new section: read only the nav block and the immediately adjacent section (~100 lines), not the whole file.

## 6. Spec Maintenance (Definition of Done)

- Any change to an API contract, data schema, or architectural pattern **must** update the relevant `Spec_*.md` file in the same commit.
- Closing a task without updating the spec is a quality gate failure.
- Skill files derived from specs must also have their `Last validated against spec` date updated.

## 7. Two-Repo Deployment

- The outer repo (`riia-cowork-jun-demo`) does **not** deploy to production.
- Production deploys require pushing from `riia-jun-release/` (remote: `riia-jun-release-prod`).
- Full deploy procedure: `project-office/specs/SPEC_Prod_Deploy.md`.

## 8. SQLAlchemy Session Rules

- All repository constructors take `db: Session` — no default constructor.
- Background threads must open their own session via `SessionLocal()` and close it in a `finally` block.
- Never pass a request-scoped `db` into a background thread — sessions are not thread-safe.
- `SqlRepository.upsert()` already calls `db.commit()` — do not commit again after calling it.
