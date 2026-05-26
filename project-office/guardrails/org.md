# Org Guardrails

**Scope:** Universal — apply to every agent, every role, every session.  
**Load order:** Load this file first, before any role guardrail or skill file.  
**Version:** v1 (2026-05-26)

---

## 1. Secrets & Credentials

- Never place `jwt_secret`, API keys, passwords, or tokens in any YAML, source file, or commit message.
- `SecretStr` must be used for all secret Pydantic fields — the value must never be logged or printed.
- Never commit `.env`, `confluence-api-key.txt`, or any file whose name contains `secret`, `token`, or `key`.
- The `RITA_JWT_SECRET` value comes exclusively from the environment variable of that name — never from a default, config file, or fallback string.

## 2. Logging

- Never use `print()` for output in application code — use `structlog`.
- This applies to all new code and to any file touched during a task.
- Exception: standalone scripts in `project-office/scripts/` may use `print()` for CLI output.

## 3. Data & External Calls

- Never call external data providers (Yahoo Finance, Bloomberg, REST APIs, etc.) from application code.
- All market data is local CSV in `rita_input/`. Data refresh runs through the dedicated `/refresh-all-instruments-data` skill only.
- Never send telemetry, run logs, or task briefs to external SaaS tools. All observability data stays in the project repo (JSON files, HTML dashboard).

## 4. Source Data Protection

- Never delete, overwrite, or modify any file under `rita_input/`. It is a read-only volume.
- Never write output files to `rita_input/`. Outputs go to `rita_output/`.

## 5. File-Reading Discipline

- Large files must be read in slices — max 400 lines per read. Known large files:
  - `rest_api.py` — 1,533 lines
  - `rita.html` — ~4,000 lines
  - `fno.html` — ~3,500 lines
- Never read `rita.html`, `fno.html`, or `mobileapp/index.html` directly — use the relevant Spec file instead.
- Never read `production_ready.md` in full — extract only the section relevant to the current decision.

## 6. Agent Quota

- Maximum 4 subagent spawns per session (preserves 80% of Claude Pro quota).
- Orchestrator agents count against this limit. Inline work (reads, edits) does not.
- If quota is at risk, complete the highest-priority agent task first and surface remaining work for the next session.

## 7. Data Residency

- All agent run logs, task briefs, and monitoring data stay in the project repo.
- No agent output is uploaded to third-party services (LangSmith, Arize, Datadog, etc.) without explicit user instruction.
- Confluence is the only approved external destination for published documentation.
