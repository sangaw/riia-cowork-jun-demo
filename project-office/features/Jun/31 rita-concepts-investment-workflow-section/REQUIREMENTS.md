# Feature 31 — rita — Concepts Page: Investment Firm Workflow Section

**Created:** 2026-06-17  
**Owner:** Engineer  
**Status:** `[ ] Not started`  
**Guardrail refs:** org · engineer-role · rita-project  
**Affected specs:** Spec_RITA_App.md, Spec_JS_Code.md, Spec_HTML_Code.md  
**Affected skills:** skill-add-rita-feature.md

---

## Objective

Enhance the RITA Concepts page by adding a new section that explains how professional investment firms approach investments — covering the investment workflow from Initiation through Feedback — and then linking each workflow step to the relevant RITA AI agents using a tab structure. This gives retail traders context for why RITA's agentic approach addresses real gaps in professional investment workflows.

---

## Background

The RITA Concepts page already introduces the CRISP-DM data science framework. The user has requested an additional explanatory section that bridges professional investment firm methodology to RITA's AI-agent design. The section should follow a similar tabbed UI pattern as the CRISP-DM page in the Data Science app, mapping each workflow phase to the RITA agents and relevant charts/plots.

---

## Scope

### In Scope
- New HTML/JS section on the RITA Concepts page (`rita.html`) explaining the investment firm workflow
- A structured table/diagram showing all 7 workflow steps (Initiation → Research → Research → Research → Design → Evaluation → Execution → Feedback)
- A tabbed component where each tab corresponds to a workflow step and calls out the relevant RITA agent + links to relevant plots
- Explanatory text blocks: professional firm gap analysis, RIIA approach rationale (Data Science + Agentic AI pillars), 4 ML capability bullets
- No new API endpoint needed — this is a pure frontend/content enhancement

### Out of Scope
- Changes to fno, ops, or ds dashboards
- New backend endpoints or database changes
- Changes to the agent logic or trading model

---

## Phases

### Phase 1 — Investment Firm Workflow Content + Tabbed Agent Mapping

**Goal:** Add the investment firm section with workflow table, explanatory text, and tabbed agent/plot mapping to the RITA Concepts page.

| Deliverable | Description |
|---|---|
| `rita.html` | New section: `sec-concepts-investment-workflow` with workflow table, gap text, RIIA rationale, ML capability bullets |
| `dashboard/js/rita/concepts.js` (or new module) | Tab structure JS — renders tabs per workflow step, agent callout, linked plots |
| `dashboard/js/rita/main.js` | Register new section loader if a new module is created |

**Acceptance Criteria:**
- [ ] Workflow table with all 7 steps (Initiation, Research ×3, Design, Evaluation, Execution, Feedback) is visible on the Concepts page
- [ ] Explanatory text blocks are present and readable
- [ ] Tab component shows one tab per workflow step; clicking a tab reveals the relevant RITA agent name and a linked plot description
- [ ] Section matches visual style of existing Concepts page content
- [ ] No JS console errors on page load

---

## Dependencies

| Phase | Depends on |
|---|---|
| Phase 1 | Existing rita.html Concepts section structure |

---

## Definition of Done

- [ ] All phases complete with acceptance criteria checked
- [ ] Relevant spec files updated (Spec_RITA_App.md, Spec_JS_Code.md)
- [ ] Session committed to git
