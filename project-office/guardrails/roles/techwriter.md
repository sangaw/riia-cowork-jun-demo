# Role Guardrails — Technical Writer

**Scope:** Applies to any agent publishing documentation to Confluence or updating spec files.  
**Load order:** Load after `org.md`.  
**Version:** v1 (2026-05-26)

---

## 1. Output Scope

- TechWriter agents publish Confluence pages and update `Spec_*.md` files.
- TechWriter agents do not write application code or tests.
- Content must reflect actual code, not assumptions — read source files or spec files before writing.

## 2. Confluence Rules

- **Plain HTML only** — no `ac:structured-macro` tags (returns HTTP 400 on this Confluence instance).
- `PAGE_ID` must be hardcoded after the first run — first run creates the page and prints the ID; paste it in before the session ends.
- Run scripts from project root: `CONFLUENCE_EMAIL=contact@ravionics.nl python project-office/confluence/pages/<script>.py`
- Never commit `confluence-api-key.txt` — token comes from file or `CONFLUENCE_API_TOKEN` env var.
- One script per sprint section — do not combine unrelated sections in one script.

## 3. Confluence Section Routing

| Content type | Parent section ID |
|---|---|
| ADRs | `architecture` → 65339419 |
| Sprint boards | `sprint_boards` → 65077274 |
| Config / API / service guides | `engineering` → 65404944 |
| Test strategy / coverage reports | `quality_testing` → 65404959 |
| Runbooks / k8s / alerting | `operations` → 65339434 |
| Release notes | `release_notes` → 65208341 |

## 4. Spec Staleness Check

Before publishing, verify the sprint's code changes against the relevant spec files. If a spec describes old field names, old endpoints, or removed patterns — update the spec before publishing to Confluence. Publishing stale documentation is a quality gate failure.

## 5. Task Brief TechWriter Section

When completing the `[TechWriter]` section in a task brief:
- Confirm Confluence page URL is recorded
- Confirm spec file was checked for staleness
- Mark `spec_updated: yes / no / N/A (no contract change)` explicitly
