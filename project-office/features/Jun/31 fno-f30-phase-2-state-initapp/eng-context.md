# Feature NN — {Feature Name}: Engineering Context

**Created by:** Architect agent (filled during `/enhance` Step 3 or manually before Engineer starts)  
**Last updated:** {YYYY-MM-DD}

---

## API Contract

| Field | Value |
|---|---|
| Method | {GET / POST / PUT / DELETE} |
| Path | `/api/...` |
| Tier | {Experience / Workflow / System} — per ADR-001 |
| Query params | {param: type — or "none"} |
| Request body | {field: type — or "none"} |
| Response shape | {list each field: name and type} |
| Auth required | {yes — JWT / no} |

---

## Files to Touch

| File | Action | Notes |
|---|---|---|
| `src/rita/schemas/{name}.py` | Create | Pydantic response schema |
| `src/rita/api/experience/{app}.py` | Edit | Add endpoint |
| `src/rita/services/{name}_service.py` | Create / Edit | Business logic (if Workflow tier) |
| `dashboard/js/{app}/{name}.js` | Create | JS loader module |
| `dashboard/js/{app}/main.js` | Edit | Register section loader |
| `dashboard/{app}.html` | Edit | Add section HTML |
| `project-office/specs/Spec_RITA_App.md` | Edit | Update endpoint inventory |
| `project-office/specs/Spec_JS_Code.md` | Edit | Add module to structure table |

---

## JS Frontend Contract

| Response field | JS reads as | DOM target element ID |
|---|---|---|
| `{field_name}` | `data.{field_name}` | `{element-id}` |

---

## Key Decisions

| Decision | Reason |
|---|---|
| {What was decided} | {Why — constraint, ADR, user requirement} |

---

## Edge Cases to Handle

| Case | Handling |
|---|---|
| Empty API response | {Show "—" or skeleton state} |
| Null field value | {Check before parseFloat/toFixed} |
| API error | {try/catch with console.warn} |

---

## Open Engineering Questions

| # | Question | Status |
|---|---|---|
| Q1 | {Question} | Open / Resolved: {answer} |
