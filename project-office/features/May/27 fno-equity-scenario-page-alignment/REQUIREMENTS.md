# Feature 27 — fno — Align Equity Scenarios page to FnO app architecture

**Created:** 2026-06-09  
**Owner:** Engineer  
**Status:** `[ ] Not started`  
**Guardrail refs:** org · engineer-role · rita-project  
**Affected specs:** Spec_RITA_App.md, Spec_JS_Code.md, Spec_HTML_Code.md  
**Affected skills:** skill-add-fno-feature.md

---

## Objective

The `equity-scenarios.html` page and its JS module `dashboard/js/scenarios/equity-scenarios.js` were created manually outside the `/enhance` pipeline. This feature aligns the page to the FnO application architecture: registers the section loader and window bindings in `fno.html`'s main JS entry, ensures the JS module structure follows the FnO ES module pattern, verifies the JSON data layer is correctly abstracted (ready for API migration), and confirms the spec files reflect the new page.

---

## Background

The Equity Scenarios page was built directly as a standalone HTML+JS file without going through the Architect → Engineer pipeline. As a result, the JS module may not follow the FnO module conventions (section loader registration, window bindings in main.js, error handling pattern), the spec files do not document the page, and the fno.html nav link points to the page without an integrated section loader path documented anywhere.

Data is sourced from static JSON files (`dashboard/data/scenarios/`). This is acceptable for the initial test; a future feature will replace the JSON layer with database-backed API endpoints.

---

## Scope

### In Scope
- Review `dashboard/js/scenarios/equity-scenarios.js` against FnO JS module conventions
- Register or confirm the module follows the FnO module pattern (self-initialising on page load)
- Verify fno.html nav link to `/dashboard/equity-scenarios.html` is correct
- Update `Spec_RITA_App.md` to document the page and its JSON data sources
- Update `Spec_JS_Code.md` to document the JS module in the FnO module structure table
- Ensure error handling follows the FnO pattern (try/catch, `—` fallback)
- No hardcoded values, no print() statements, ruff passes

### Out of Scope
- Moving JSON data to a database (Phase 2 — separate feature)
- Adding new data fields or UI sections
- Changes to fno.html sidebar nav beyond confirming the existing link is correct

---

## Phases

### Phase 1 — Architecture Alignment

**Goal:** Align the equity-scenarios JS module and HTML to FnO conventions and update spec documentation.

| Deliverable | Description |
|---|---|
| `dashboard/js/scenarios/equity-scenarios.js` | Reviewed and updated to follow FnO module pattern if needed |
| `project-office/specs/Spec_RITA_App.md` | New section documenting equity-scenarios page and JSON data layer |
| `project-office/specs/Spec_JS_Code.md` | equity-scenarios module added to FnO module table |

**Acceptance Criteria:**
- [ ] JS module follows FnO error handling pattern (try/catch, `—` on failure)
- [ ] No hardcoded values in JS
- [ ] Spec files document the page
- [ ] Ruff passes on any Python files if touched

---

## Dependencies

| Phase | Depends on |
|---|---|
| Phase 1 | Equity Scenarios page exists (already done) |

---

## Definition of Done

- [ ] Architecture review complete; JS module conventions verified
- [ ] Spec files updated (Spec_RITA_App.md + Spec_JS_Code.md)
- [ ] Session committed to git
