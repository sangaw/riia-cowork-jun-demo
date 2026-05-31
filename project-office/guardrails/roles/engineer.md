# Role Guardrails — Engineer

**Scope:** Applies to any agent writing application code in `riia-jun-release/src/`.  
**Load order:** Load after `org.md`. Load `project.md` alongside this file.  
**Version:** v1 (2026-05-26)

---

## 1. Worktree Isolation (Mandatory)

- All Engineer agents must work in a git worktree with `isolation: "worktree"`.
- Never commit directly to `master` from an Engineer agent.
- The worktree branch name follows the pattern: `feature/<short-description>`.

## 2. ADR-001 — Tier Compliance

- Every new route must land in the correct tier directory before any other work begins.
- If the correct tier is unclear, re-read the decision tree in `project-office/guardrails/project.md §1` before writing any code.
- System tier: one repository, zero business logic, zero service calls.
- Workflow tier: service calls only — never call a repository directly from the router.
- Experience tier: read-only, no side effects, no writes, no direct repository calls.

## 3. ADR-002 — Repository Pattern

- No direct DB, ORM, or CSV access in routes or services. All data access through `repositories/` classes.
- If the data access you need does not exist in a repository, create or extend the repository — do not shortcut through the route or service.

## 4. FastAPI Dependency Injection

```python
# Correct pattern for all routers since Sprint 2.5
def _get_service(db: Session = Depends(get_db)) -> MyService:
    return MyService(db)

@router.get("/resource")
def get_resource(svc: MyService = Depends(_get_service)):
    return svc.get_resource()
```

For System (CRUD) routers, inject the repository directly (skip the service).

## 5. API ↔ Frontend Contract

- Before writing a handler, open the JS consumer and list every field it reads.
- The handler's `return {}` dict must include every field in that list.
- Never echo a query parameter as a response row field value.
- After writing, paste the JS field list and handler return dict side-by-side and confirm every field is present.

## 6. Code Quality Gates (must pass before PR)

- `ruff check src/` — zero errors.
- No `print()` statements (see `org.md §2`).
- No hardcoded secrets (see `org.md §1`).
- No hardcoded lot sizes (see `project.md §2`).

## 7. Spec Update (Definition of Done)

- If the task changes an API contract, response schema, or architectural pattern — update the relevant `Spec_*.md` file in the same commit.
- Mark `spec_updated: true` in the task brief `[Engineer] Implementation Log` section.

## 8. Bug Diagnosis Protocol

When a defect is reported from manual testing:
1. Read the JS module for the broken section — identify which endpoint it calls.
2. Read the endpoint handler — check return values and conditions.
3. Trace data flow end-to-end: handler → JS → DOM element IDs.
4. Identify root cause from code alone.
5. Make the minimal targeted fix.

**Do not start `uvicorn` or `curl` endpoints to reproduce bugs.** Diagnose from code.

## 9. Auth Token Key — FC-AUTH-KEY (Mandatory)

- The canonical sessionStorage key for the JWT across ALL dashboards is **`auth_token`**.
- Never introduce a new key name (`rita_token`, `fno_token`, etc.) — `shared/api.js` reads `auth_token` exclusively. A mismatched key causes the JWT to never attach to API calls, producing silent 401 failures after Google login.
- Auth gate checks in HTML (`sessionStorage.getItem(...)`) and OAuth token ingest (`sessionStorage.setItem(...)`) in `main.js` must both use `auth_token`.
- On 401, clear `auth_token` (not any other key) before redirecting.
- Prior incident: Feature 26 Phase 4 introduced `rita_token` for the FnO auth overlay; this broke all authenticated API calls in FnO silently. Fixed in commit a999e70.

## 10. Scope Discipline

- Fix only what the task specifies. Do not refactor surrounding code while fixing a bug.
- Do not add error handling for scenarios that cannot happen.
- Do not add features beyond what the architect's design specifies.
