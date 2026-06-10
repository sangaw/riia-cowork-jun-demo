# Confluence Publishing Guide

## Credentials

```python
EMAIL = os.environ.get("CONFLUENCE_EMAIL", "")
TOKEN = os.environ.get("CONFLUENCE_API_TOKEN") or open("confluence-api-key.txt").read().strip()
SPACE = os.environ.get("CONFLUENCE_SPACE_KEY", "RIIAProjec")
```

Run scripts from the project root with `CONFLUENCE_EMAIL` set in the environment.

## Space Structure (last verified 2026-04-29)

Root page: **Data Science Project - RIIA** (`65110332`)

```
Data Science Project - RIIA
├── How We Work              65241125   cowork guides, token budget, skill system
├── Project Management       65273887   master plan, sprint planning
│   └── Sprint Boards        65077274   one sub-page per sprint (Sprint 0–6)
├── Project Summary          76578819   sprint history, milestones, tech stack
├── RIIA App                 76611585   ← product section root
│   ├── Requirements         76644353   features, NFRs, instrument coverage
│   ├── Architecture and Design  65339419   ADRs + current architecture
│   │   └── Architecture     76644368   current-state system architecture
│   ├── Engineering Documentation  65404944   sprint guides + current engineering
│   │   └── Engineering      76611602   current API inventory + slash commands
│   ├── Operations           65339434   runbooks
│   │   └── App Operations   76611617   current startup/config/monitoring runbook
│   └── Quality and Testing  65404959   test strategy, coverage reports
└── Release Notes            65208341
    ├── RITA v1.0 Release Notes  71794689
    └── RITA June 2026 — Release Notes  92274695
```

## Section Parent IDs

```python
SECTION = {
    # Top-level
    "homepage":             "65110332",  # Data Science Project - RIIA
    "how_we_work":          "65241125",
    "project_management":   "65273887",
    "project_summary":      "76578819",
    "release_notes":        "65208341",
    "sprint_boards":        "65077274",
    # RIIA App product section
    "riia_app":             "76611585",
    "requirements":         "76644353",
    "architecture":         "65339419",  # Architecture and Design section
    "engineering":          "65404944",  # Engineering Documentation section
    "operations":           "65339434",
    "quality_testing":      "65404959",
    # Current-state product docs
    "architecture_current": "76644368",  # update when architecture changes
    "engineering_current":  "76611602",  # update when API contract changes
    "ops_current":          "76611617",  # update when runbook changes
}
```

Publisher class: `project-office/confluence/publish.py` (`ConfluenceClient`)

## Publishing Rules

- Use **plain HTML only** — no `ac:structured-macro` tags (returns HTTP 400 on this instance)
- ADR pages → `SECTION["architecture"]`
- Sprint board pages → `SECTION["sprint_boards"]`
- New product feature docs → `SECTION["riia_app"]` or the relevant child section
- Current-state updates (architecture/engineering/ops) → update the `_current` pages, not sprint artefacts
- Do not commit `confluence-api-key.txt` or `.env` files
