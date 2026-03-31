# RITA Production Refactor — Project Guide for Claude

This file is automatically loaded at the start of every Claude Code session.
It gives all agents the essential context they need without re-reading the codebase.

---

## What This Project Is

**RITA** (Risk Informed Investment Approach) — a Nifty 50 Double DQN reinforcement learning trading system + FnO portfolio manager being refactored from POC to production.

- **POC source:** `../poc/rita-cowork-demo` (local — not in this repo)
- **Production target:** `.` (this repo)
- **Assessment:** `rita-cowork-demo/production_ready.md` (v2.0, pre-digested — do NOT re-read in full)
- **Daily status:** `PLAN_STATUS.md` — read this at the start of every session

## The Agent Team

| Role | Invoke as | Scope |
|---|---|---|
| Project Manager | `general-purpose` | Reads PLAN_STATUS.md; outputs task list and risk updates |
| Architect | `Plan` agent | Reads targeted POC files + ADR excerpts; outputs design docs to `docs/` |
| Design & Code Reviewer | `general-purpose` | Reads ADRs + git diffs; outputs review reports |
| Engineer | `general-purpose` + `isolation: "worktree"` | Reads scoped file slice + ADR; writes code to `src/` |
| QA Tester | `general-purpose` | Reads new code; writes tests to `tests/` |
| Ops Engineer | `general-purpose` | Reads pyproject.toml + existing config; writes Dockerfile, CI, k8s/ |
| Technical Writer | `general-purpose` | Reads sprint artifacts; publishes to Confluence via `publish_confluence.py` |

## Token Efficiency Rules (ALL agents must follow)

1. **Never read `production_ready.md` in full.** Pass only the relevant section as an excerpt.
2. **Read large files in slices** — max 400 lines at a time, targeted at the section being modified.
   - `rest_api.py` = 1,533 lines | `rita.html` = 4,000 lines | `fno.html` = 3,500 lines
3. **Read `PLAN_STATUS.md` first** — it tells you what's done and what's next. Don't re-explore.
4. **Engineer agents use worktree isolation** — `isolation: "worktree"` for all code-writing agents.
5. **Max 4 agent invocations per session** to stay within 80% of the Claude Pro quota.
6. **Write outputs to files immediately** — agents must persist artifacts before the session ends.

## Workspace Structure

```
riia-cowork-jun/                    ← project workspace root (this repo)
├── CLAUDE.md                       ← THIS FILE — auto-loaded every session
├── PLAN_STATUS.md                  ← daily status tracker (read first every session)
├── confluence-api-key.txt          ← TEMP: move to env var in Sprint 1
│
├── project-office/                 ← ALL cowork management code (not app code)
│   ├── confluence/
│   │   ├── publish.py              ← reusable ConfluenceClient class
│   │   ├── setup_hierarchy.py      ← one-time hierarchy setup (already run)
│   │   └── pages/                  ← one script per published section
│   ├── sprint-boards/              ← sprint board Confluence scripts (one per sprint)
│   └── scripts/                    ← utility scripts (reporting, cleanup, etc.)
│
└── riia-jun-release/               ← RITA APPLICATION CODE (what engineers build)
    ├── src/rita/
    │   ├── api/v1/system/          ← pure CRUD routers
    │   ├── api/v1/workflow/        ← business process routers
    │   ├── api/experience/                ← Experience Layer routers
    │   ├── services/               ← business logic
    │   ├── repositories/           ← CSV access layer (one class per table)
    │   ├── schemas/                ← Pydantic data contracts
    │   ├── core/                   ← pure calculation/ML logic
    │   └── config.py               ← Pydantic Settings
    ├── config/{base,development,staging,production}.yaml
    ├── tests/{unit,integration,e2e}/
    ├── dashboard/js/{rita,fno,ops}/ ← ES modules
    ├── dashboard/css/responsive.css
    ├── k8s/                        ← Kubernetes manifests
    └── docs/                       ← ADRs (ADR-001 through ADR-005)
```

**Rule for Engineer agents:** All application code goes in `riia-jun-release/`.
**Rule for TechWriter/PM/Ops agents:** All management scripts go in `project-office/`.

## Key Design Decisions (ADRs)

- **ADR-001:** Three-tier API (Experience Layer / Business Process / System). All routes split accordingly.
- **ADR-002:** Repository pattern for all CSV access. No direct file I/O in routes or services.
- **v1 target:** CSV-backed, cloud-native, stateless API, JWT-secured.
- **v2 future:** PostgreSQL replaces CSV (mechanical migration — same schemas).

## Confluence Publishing

```python
# Credentials — set via environment variables (see .env.example)
EMAIL = os.environ.get("CONFLUENCE_EMAIL", "")
TOKEN = os.environ.get("CONFLUENCE_API_TOKEN") or open("confluence-api-key.txt").read().strip()
SPACE = os.environ.get("CONFLUENCE_SPACE_KEY", "RIIAProjec")

# Section parent IDs (hierarchy set up 2026-03-30)
SECTION = {
    "homepage":           "65110332",
    "project_management": "65273887",   # Master Plan, Sprint Planning, Sprint Boards
    "sprint_boards":      "65077274",   # one sub-page per sprint
    "how_we_work":        "65241125",   # Cowork guides, token budget
    "architecture":       "65339419",   # ADRs, schemas (Sprint 0+)
    "engineering":        "65404944",   # API ref, service guide (Sprint 1-3)
    "quality_testing":    "65404959",   # test strategy, coverage reports
    "operations":         "65339434",   # runbooks, k8s, alerting
    "release_notes":      "65208341",   # v1.0 release notes
}

# Publisher: project-office/confluence/publish.py (ConfluenceClient class)
```

**Rule:** Use plain HTML only in Confluence pages — no `ac:structured-macro` tags (returns HTTP 400 on this instance).
**Rule:** New pages for Architecture ADRs go under `SECTION["architecture"]`. New sprint boards go under `SECTION["sprint_boards"]`.

## Daily Commands

| User says | What to do |
|---|---|
| `Start Day N` | Read PLAN_STATUS.md → confirm tasks → launch agents |
| `End day` | 1. Update PLAN_STATUS.md (mark day done) → 2. Update `project-office/program-roadmap.html` (progress bars + badges) → 3. Run `publish_sprint{N}_board.py` to update Confluence sprint board → 4. git commit |
| `What's next?` | Read PLAN_STATUS.md → report current day and tasks |
| `Show blockers` | Read PLAN_STATUS.md → list blocked items |

## Financial Domain Notes

- **Instrument:** Nifty 50 index (NSE)
- **Lot sizes:** NIFTY = 75 (changed from 50 in 2024), BANKNIFTY = 30 — must be config-driven, NOT hardcoded
- **Greeks:** Delta, Gamma, Theta, Vega — test against Black-Scholes reference before and after any core/ changes
- **CSV data:** `rita_input/` is read-only source; `rita_output/` is written by the API
- **Model files:** `.zip` format (stable-baselines3); stored alongside rita_output/

## What NOT to Do

- Do not delete or overwrite files in `rita_input/` (source data)
- Do not modify `core/` modules without QA running Greeks reference tests first
- Do not commit `confluence-api-key.txt` or `.env` files
- Do not add `print()` statements — use `structlog` (Sprint 3+)
- Do not make API calls to external data providers — all data is local CSV
