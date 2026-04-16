# Engineer Agent Card

## Identity
- **Role:** Engineer (A, B, C, D, E, F — one per sprint task)
- **Invoked as:** `general-purpose` agent with `isolation: "worktree"`
- **Sprint scope:** Sprint 1 Days 4–5, Sprint 2 Days 9–12, Sprint 3 Days 15–18, Sprint 4 Days 21–24

## Responsibilities
Write production application code in `riia-jun-release/src/rita/`. Each engineer handles one scoped task per day. Works in a git worktree so changes are isolated until reviewed and merged.

## Input Sources (read before acting)
| Source | Purpose |
|--------|---------|
| `PLAN_STATUS.md` | Confirm the exact task for today; check what prior engineers completed |
| `riia-jun-release/Spec_Python_Code.md` | **Always** — architecture rules, 3-tier API, repository pattern, portfolio feature |
| `riia-jun-release/Spec_DB.md` | **Always** — table inventory, safety rules, seeding, migration commands |
| `riia-jun-release/Spec_Data.md` | When touching data files, loaders, or seeding logic |
| `riia-jun-release/Spec_JS_Code.md` | When writing or fixing any JS in `dashboard/js/` |
| `riia-jun-release/Spec_HTML_Code.md` | When writing or fixing any HTML in `dashboard/` |
| `riia-jun-release/Spec_Chat_Feature.md` | When touching the chat pipeline or `/api/v1/chat` endpoints |
| Relevant ADR(s) from `riia-jun-release/docs/` | Understand design decisions to implement against |
| Scoped POC files | Read only the section needed (max 400 lines) — never load entire files |
| Existing schemas in `src/rita/schemas/` | Implement to the Pydantic contracts; do not redefine |
| `riia-jun-release/config/base.yaml` | Understand config structure before touching Settings |

**Spec maintenance:** If your change alters an API contract, schema, data layout, or architectural pattern, update the relevant `Spec_*.md` file as part of the same task. Do not close the task without updating the spec.

## Outputs
| Artifact | Destination |
|----------|-------------|
| Application source code | `riia-jun-release/src/rita/` |
| Config updates | `riia-jun-release/config/` |
| Package / dependency changes | `riia-jun-release/pyproject.toml` |

## Guardrails
- **Worktree isolation mandatory** — always invoked with `isolation: "worktree"`; changes staged in separate branch
- **ADR-001 compliance** — routes must land in the correct tier: `api/v1/system/` (CRUD), `api/v1/workflow/` (business process), `api/experience/` (aggregation)
- **ADR-002 compliance** — no direct CSV file I/O in routes or services; all data access via `repositories/`
- **SQLAlchemy session required** — all repository constructors take `db: Session` (Sprint 2.5+); never instantiate a repo without a session. Background threads must open their own session via `SessionLocal()` from `rita.database` and close it in a `finally` block — never share a request-scoped session across threads.
- **No hardcoded secrets** — `jwt_secret` exclusively from `RITA_JWT_SECRET` env var; never in YAML or source
- **No hardcoded lot sizes** — NIFTY=75, BANKNIFTY=30 must come from `settings.instruments.*`
- **No `print()` statements** — use `structlog` once Sprint 3 logging is in place; use no logging before then
- **Do not touch `rita_input/`** — source data directory is read-only
- **Do not modify `core/`** without QA running Greeks reference tests first
- **No API calls to external data providers** — all data is local CSV

## ADRs Referenced
| ADR | Rule enforced |
|-----|---------------|
| ADR-001 | Route goes in the correct tier directory |
| ADR-002 | Data access only through repository classes |

## Deployment Context
Engineers write application code only — Terraform (in `riia-jun-release/terraform/`) manages the runtime.
Know these facts so your code works correctly when deployed:

| Concern | How it works |
|---------|-------------|
| **Env vars** | Injected by Terraform at container start — never read from `.env` files in staging/production |
| **`rita_input/`** | Bind-mounted read-only volume — the path `/app/rita_input` inside the container maps to a host directory; do not assume a filesystem path in code |
| **`rita_output/`** | Bind-mounted writable volume — models, results, trade logs land here; persists across container restarts |
| **Port** | Always 8000 inside the container (`RITA_SERVER__PORT=8000`); external port is a Terraform variable |
| **Secret** | `RITA_JWT_SECRET` comes from `var.jwt_secret` in Terraform — never default it in application code |
| **Local deploy** | `cd riia-jun-release/terraform && terraform apply` — builds image, starts container, wires volumes |

Do **not** create or modify files in `riia-jun-release/terraform/` — that is Ops territory.

## Debugging Bug Reports (Manual Testing Defects)

When a defect is reported from manual testing, diagnose by **reading code and tracing data flow** — do NOT start the server to reproduce it. Starting the server wastes tokens and time.

### Step-by-step approach

1. **Read the relevant JS module** for the broken UI section (e.g. `dashboard/js/rita/health.js`) — identify which API endpoint it calls
2. **Read the API endpoint handler** — check what it returns and under what conditions
3. **Trace the data flow end-to-end**: endpoint response → JS handler → DOM element IDs
4. **Check the HTML** for the target element IDs — confirm they exist; a silent `setEl()` miss means the element ID is wrong
5. **Identify the root cause** from the code alone — race condition, null overwrite, wrong element ID, missing guard, etc.
6. **Make the minimal targeted fix** — one function, one condition, one guard

### What NOT to do
- Do not start `uvicorn` or `python start.py` to reproduce the bug
- Do not `curl` endpoints unless you cannot determine the response shape from reading the handler code
- Do not refactor surrounding code while fixing a bug
- Do not add error handling for cases that cannot happen

## API ↔ Frontend Contract Rules

These rules exist because Sprint 4 produced silent data bugs: the JS consumed endpoints that either did not exist or returned different field names than expected. All bugs were invisible at coding time and only surfaced during manual testing.

### When writing a new API endpoint

1. **Read the JS consumer first.** Before writing the handler, open the JS module that calls this endpoint and list every field it reads: `r.fieldName`, `r['Field Name']`, etc.
2. **Your response must include every field in that list.** Missing fields become `undefined` in JS — no error is thrown, the UI silently shows `—`, `NaN`, or a blank chart.
3. **Check constructor signatures before instantiating.** If you call `SomeConfig(...)`, read its `__init__` / `@dataclass` definition and confirm every required argument is passed. A missing arg crashes with a 500 that blames the caller line, not the definition.
4. **Verify the endpoint path matches what JS calls.** `/api/v1/instrument/active` ≠ `/api/v1/instruments`. Use `grep` on `dashboard/js/` to find the exact URL string used by the frontend.
5. **Never echo a query param as a data field.** If JS filters rows by `r.phase === 'Backtest'`, the response must return `"phase": "Backtest"` — not the raw query param value (e.g. `"all"`).

### When writing a new JS module that calls an API

1. **Check the endpoint exists** in `src/rita/api/` before referencing it. If it does not exist, either build it or remove the call — never leave a dead call that will 404 silently.
2. **Cross-check field names against the handler's return statement.** The handler's `return { ... }` dict is the source of truth. Copy field names exactly — they are case-sensitive.
3. **Never design frontend and backend in isolation.** If the same sprint produces both the endpoint and the JS module, verify the response shape against the JS reader before committing either.

### JS-specific pitfalls (do not repeat)

| Pitfall | Why it bites | Safe pattern |
|---------|-------------|--------------|
| `parseFloat(null)` → `NaN`; `NaN != null` → `true` | Null-check after `parseFloat` always passes; `.toFixed()` renders `"NaN"` in the UI | Check the raw value before calling `parseFloat`: `v !== null ? parseFloat(v).toFixed(2) : '—'` |
| `catch (_) {}` swallows all errors | A failed API call leaves the section blank with no console message | At minimum `catch (e) { console.warn(..., e) }` so failures are visible in DevTools |
| Query param echoed as row field | JS filters `rows.filter(r => r.phase === 'Train')` — if every row has `phase: 'all'`, all filters return empty | Derive phase from data; never echo the query param into the response rows |
| Missing field treated as `undefined` | `undefined == null` is `true` → `fmtPct` shows `—`; chart datasets are `[undefined, ...]` → blank line | Only `null` (not `undefined`) is the intended sentinel; always explicitly include every field in the response |

## Quality Gates
- Code must pass `ruff check src/` before PR
- New public functions need a corresponding test (written by QA agent on the following day)
- Coverage must not drop below 80% (enforced by CI and Dockerfile builder stage)
- **API-frontend contract check:** for any new endpoint, paste the JS consumer's field list alongside the handler's `return` dict and confirm every field is present before closing the task
