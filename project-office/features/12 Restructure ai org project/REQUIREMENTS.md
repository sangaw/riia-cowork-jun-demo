# Feature 12 — Restructure ai-org: Relocate Agent-Ops Data and Scripts

**Status:** Complete  
**Date:** 2026-05-19  
**Closed:** 2026-05-19 (commits 7c771aa + d1b5c2d)  
**Owner:** San G  
**Approach:** /enhance multi-agent orchestration

---

## 1. Problem Statement

`riia-ai-org/` is a POC folder that must not be committed to GitHub going forward — it will not be deployed to production. However, the production backend currently hardcodes two paths into it:

```
# In riia-jun-release/src/rita/api/experience/ops.py (lines 453, 577)
Path(__file__).parents[5] / "riia-ai-org" / "agent-ops"
```

This means:
- **`/api/experience/ops/agent-builds`** reads `riia-ai-org/agent-ops/metrics.json` for 7 extended KPI panels (`task_completion`, `quality`, `token_forecasting`, `efficiency`, `reliability`, `hitl`, `agentic`) plus `skill_version_history`
- **`/api/experience/ops/agent-builds`** also reads individual `riia-ai-org/agent-ops/runs/run-{id}.json` files for per-run v2 fields (actual token usage per agent role)
- **`/api/experience/ops/token-forecast`** reads `riia-ai-org/agent-ops/metrics.json` for `per_role_avg_tokens` — raises HTTP 503 if the file is missing

Additionally, the write-side utility scripts that produce those files (`aggregate_metrics.py`, `write_run_to_db.py`, `backfill_metrics.py`, `seed_agent_builds.py`) live in `riia-ai-org/agent-ops/` and write to paths derived from their own `__file__` location, so they break once the source folder is removed from git.

**Goal:** Move all data files into `riia-jun-release/` (so they deploy with the app) and all utility scripts into `project-office/scripts/agent-ops/` (project tooling). Then drop `riia-ai-org/` from git tracking entirely.

---

## 2. Scope

**In scope:**
- Move `metrics.json` and `runs/*.json` data files into `riia-jun-release/data/agent-ops/`
- Update the two hardcoded `riia-ai-org` path references in `ops.py` to point to the new location
- Move the four utility scripts to `project-office/scripts/agent-ops/` and fix their internal path resolutions
- Add `riia-ai-org/` to `.gitignore` and remove it from git index (`git rm --cached -r riia-ai-org/`)
- Verify `ops.py` linting passes (`ruff check`) after changes

**Out of scope:**
- Changes to the Ops dashboard JS or HTML (no user-visible change)
- Database schema or ORM changes (agent_builds DB table is unaffected)
- Moving the `schema.md`, `failure-catalog.md`, `dashboard.html`, or `run-sample.json` reference files (leave in `riia-ai-org/` locally — not needed in production)
- Moving `PROJECT.md` or `ACTIONS-agent-builds.md` (historical docs, not needed in production)

---

## 3. Current Architecture (as-is)

```
riia-cowork-jun/
├── riia-ai-org/                          ← POC folder — MUST NOT deploy
│   └── agent-ops/
│       ├── metrics.json                  ← read by ops.py (7 KPI sections + skill_version_history)
│       ├── runs/
│       │   └── run-YYYYMMDD-HHMM.json   ← read by ops.py (per-run v2 fields)
│       ├── aggregate_metrics.py          ← writes metrics.json from runs/*.json
│       ├── write_run_to_db.py            ← writes run JSON to SQLite DB
│       ├── backfill_metrics.py           ← backfills DB from existing run JSONs
│       └── seed_agent_builds.py          ← seeds initial DB data
└── riia-jun-release/
    └── src/rita/api/experience/ops.py   ← hardcodes path to riia-ai-org
```

---

## 4. Target Architecture (to-be)

```
riia-cowork-jun/
├── .gitignore                            ← add riia-ai-org/ entry
├── riia-ai-org/                          ← still exists locally, ignored by git
├── project-office/scripts/agent-ops/    ← NEW: operational tooling (was riia-ai-org)
│   ├── aggregate_metrics.py             ← moved + paths updated
│   ├── write_run_to_db.py               ← moved + paths updated
│   ├── backfill_metrics.py              ← moved + paths updated
│   └── seed_agent_builds.py             ← moved + paths updated
└── riia-jun-release/
    ├── data/agent-ops/                  ← NEW: app data (deploys with the app)
    │   ├── metrics.json                 ← moved from riia-ai-org
    │   └── runs/
    │       └── run-YYYYMMDD-HHMM.json  ← moved from riia-ai-org
    └── src/rita/api/experience/ops.py   ← 2 path references updated
```

---

## 5. Files to Touch

| File | Action | Change |
|---|---|---|
| `riia-jun-release/data/agent-ops/metrics.json` | **Create (copy)** | Copy from `riia-ai-org/agent-ops/metrics.json` |
| `riia-jun-release/data/agent-ops/runs/*.json` | **Create (copy)** | Copy all run JSONs from `riia-ai-org/agent-ops/runs/` |
| `riia-jun-release/src/rita/api/experience/ops.py` | **Edit** | Update 2 hardcoded path expressions (lines 453 and 577) |
| `project-office/scripts/agent-ops/aggregate_metrics.py` | **Create (copy+fix)** | Copy from `riia-ai-org`; fix `main()` — resolve `runs_dir` and `output_path` to `riia-jun-release/data/agent-ops/` |
| `project-office/scripts/agent-ops/write_run_to_db.py` | **Create (copy+fix)** | Copy from `riia-ai-org`; fix `_repo_root = _script_dir.parents[2]` (was `.parents[1]`) |
| `project-office/scripts/agent-ops/backfill_metrics.py` | **Create (copy+fix)** | Copy from `riia-ai-org`; fix any internal path resolutions |
| `project-office/scripts/agent-ops/seed_agent_builds.py` | **Create (copy+fix)** | Copy from `riia-ai-org`; fix any internal path resolutions |
| `.gitignore` | **Edit** | Add `riia-ai-org/` entry |

---

## 6. Detailed Path Changes

### 6.1 `ops.py` — Two path expressions

**`get_agent_builds` (line 453):**
```python
# BEFORE
_runs_dir = Path(__file__).parents[5] / "riia-ai-org" / "agent-ops"

# AFTER
# __file__ = riia-jun-release/src/rita/api/experience/ops.py
# .parents[4] = riia-jun-release/
_runs_dir = Path(__file__).parents[4] / "data" / "agent-ops"
```

**`get_token_forecast` (line 577):**
```python
# BEFORE
metrics_path = repo_root / "riia-ai-org" / "agent-ops" / "metrics.json"
# where repo_root = Path(__file__).parents[5]

# AFTER
# Resolve directly from __file__ — no repo_root variable needed
metrics_path = Path(__file__).parents[4] / "data" / "agent-ops" / "metrics.json"
```

### 6.2 `aggregate_metrics.py` — `main()` path resolution

```python
# BEFORE (resolves relative to script location in riia-ai-org/agent-ops/)
script_dir = Path(__file__).resolve().parent
runs_dir = script_dir / "runs"
output_path = script_dir / "metrics.json"

# AFTER (resolve data dir relative to repo root, regardless of script location)
# __file__ = project-office/scripts/agent-ops/aggregate_metrics.py
# .parents[3] = riia-cowork-jun/
_data_dir = Path(__file__).resolve().parents[3] / "riia-jun-release" / "data" / "agent-ops"
runs_dir = _data_dir / "runs"
output_path = _data_dir / "metrics.json"
```

### 6.3 `write_run_to_db.py` — `_repo_root` index

```python
# BEFORE (script was in riia-ai-org/agent-ops/ → parents[1] = riia-cowork-jun/)
_repo_root = _script_dir.parents[1]

# AFTER (script is in project-office/scripts/agent-ops/ → parents[2] = riia-cowork-jun/)
_repo_root = _script_dir.parents[2]
```

The `_app_src` and `_DB_PATH` derivations from `_repo_root` remain unchanged.

### 6.4 `backfill_metrics.py` and `seed_agent_builds.py`

Apply the same repo-root depth fix as `write_run_to_db.py` — check each file for `_script_dir.parents[N]` or `Path(__file__).parents[N]` references and adjust depth by +1 (since the script moves one extra folder level up).

---

## 7. Git Cleanup (last step, after all moves verified)

```bash
# 1. Add to .gitignore
echo "" >> .gitignore
echo "# POC folder — local only, not deployed" >> .gitignore
echo "riia-ai-org/" >> .gitignore

# 2. Remove from git index (keeps files on disk)
git rm --cached -r riia-ai-org/

# 3. Commit
git add .gitignore
git commit -m "chore: relocate agent-ops data+scripts; drop riia-ai-org from git"
```

---

## 8. Acceptance Criteria

- [x] `riia-jun-release/data/agent-ops/metrics.json` exists and contains all 7 KPI sections
- [x] `riia-jun-release/data/agent-ops/runs/` contains all run JSON files (count matches `riia-ai-org/agent-ops/runs/`)
- [x] `GET /api/experience/ops/agent-builds` returns 200 with non-empty `per_role` and `metrics_extra` populated
- [x] `GET /api/experience/ops/token-forecast?feature_type=rita&files_to_change=medium&new_endpoint_or_model=one&frontend_scope=panel&integration_type=extends` returns 200 (not 503)
- [x] `ruff check riia-jun-release/src/rita/api/experience/ops.py` passes with no errors
- [x] `project-office/scripts/agent-ops/aggregate_metrics.py` runs without error from any working directory and writes to `riia-jun-release/data/agent-ops/metrics.json`
- [x] `project-office/scripts/agent-ops/write_run_to_db.py <path-to-any-run.json>` runs without import errors
- [x] `riia-ai-org/` is listed in `.gitignore`
- [x] `git status` shows no tracked files under `riia-ai-org/`
- [x] No references to `riia-ai-org` remain in any file under `riia-jun-release/`

---

## 9. Notes

- The `data/agent-ops/` folder in `riia-jun-release` should be committed to git (it contains live operational data). Add a `.gitkeep` to `data/agent-ops/runs/` if the runs folder would otherwise be empty.
- The `riia-ai-org/` folder continues to exist on the local machine after `git rm --cached` — files are not deleted. This is intentional; the folder is just no longer tracked.
- Do not move `schema.md`, `failure-catalog.md`, `run-sample.json`, or `dashboard.html` — these are reference/POC artefacts not needed by the app or scripts.
- The Ops dashboard JS (`agent-builds.js`) does not need any changes — it calls the same API endpoints, which will now resolve data from the new path transparently.
