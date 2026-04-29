# Confluence Publishing Guide

## Credentials

```python
EMAIL = os.environ.get("CONFLUENCE_EMAIL", "")
TOKEN = os.environ.get("CONFLUENCE_API_TOKEN") or open("confluence-api-key.txt").read().strip()
SPACE = os.environ.get("CONFLUENCE_SPACE_KEY", "RIIAProjec")
```

Run scripts from the project root with `CONFLUENCE_EMAIL` set in the environment.

## Section Parent IDs (hierarchy set up 2026-03-30)

```python
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
```

Publisher class: `project-office/confluence/publish.py` (`ConfluenceClient`)

## Rules

- Use **plain HTML only** — no `ac:structured-macro` tags (returns HTTP 400 on this instance)
- ADR pages → `SECTION["architecture"]`
- Sprint board pages → `SECTION["sprint_boards"]`
- Do not commit `confluence-api-key.txt` or `.env` files
