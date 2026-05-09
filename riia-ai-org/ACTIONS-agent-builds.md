# Actions — Add Agent Builds Section to Ops Dashboard

**Goal:** Embed the AgentOps 6-panel 2×3 grid into the Ops dashboard under Build menu > Agent Builds.
**Constraint:** Only HTML/JS moves into Ops. Python code and JSON data stay in `riia-ai-org/agent-ops/`.

---

## Step 1 — Static mount in main.py
**File:** `riia-jun-release/src/rita/main.py`
**What:** Add `app.mount("/agent-ops-data", StaticFiles(directory=...), name="agent-ops-data")` after the `/dashboard` mount (line 330). Path resolves to `riia-ai-org/agent-ops/` relative to main.py location.
**Why:** JS in Ops dashboard fetches metrics.json and run JSONs via RITA server — no CORS issues.

---

## Step 2 — CSS rule in ops.html
**File:** `riia-jun-release/dashboard/ops.html` (line 77 area)
**What:** Add `.ni.on.n-agent-builds{border-left-color:var(--accelerate);color:var(--accelerate);}` after the `.ni.on.n-users` rule.
**Why:** Active state styling for the new nav item — uses Build group accent colour.

---

## Step 3 — Nav item in ops.html
**File:** `riia-jun-release/dashboard/ops.html` (after line 320 — after CI/CD nav item closes)
**What:** Add `<div class="ni n-agent-builds" onclick="nav(this,'agent-builds')">` with a network/graph SVG icon and "Agent Builds" label.
**Why:** Makes the section reachable from the Build sidebar group.

---

## Step 4 — Section skeleton in ops.html
**File:** `riia-jun-release/dashboard/ops.html` (after line 662 — after sec-cicd closes)
**What:** Add `<section class="sec" id="sec-agent-builds">` with a page header and a `<div id="ab-grid">` placeholder that the JS will populate.
**Why:** The nav system toggles `.on` class on this section when selected.

---

## Step 5 — Grid CSS in ops.html
**File:** `riia-jun-release/dashboard/ops.html` (inline `<style>` block)
**What:** Add `.ab-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;}` and `.ab-panel{background:var(--surface);border:1.5px solid var(--border);border-radius:var(--r);padding:16px;}` styles.
**Why:** Defines the 2×3 grid layout using Ops CSS variables — no external stylesheet needed.

---

## Step 6 — Create agent-builds.js
**File:** `riia-jun-release/dashboard/js/ops/agent-builds.js` (new file)
**What:** JS module that fetches `/agent-ops-data/metrics.json` + individual run logs via `apiFetch`, then renders all 6 panels into `#ab-grid` using Ops CSS classes (`.tbl`, badges, etc).
**Panels:** Run History | Agent Scorecards | Grounding Trend | Failure Heatmap | Token Trend | Skill Versions
**Why:** Separates data loading and rendering from the section skeleton in ops.html.

---

## Step 7 — Register in nav.js
**File:** `riia-jun-release/dashboard/js/ops/nav.js`
**What:** Add `'agent-builds'` to the `SECTIONS` array.
**Why:** The nav show/hide logic iterates over SECTIONS — without this the section never toggles.

---

## Step 8 — Register in main.js
**File:** `riia-jun-release/dashboard/js/ops/main.js`
**What:** Import `loadAgentBuilds` from `./agent-builds.js`, add to `sectionLoaders['agent-builds']`, add `window.loadAgentBuilds = loadAgentBuilds`.
**Why:** Wires the nav click to the data loader and exposes it for any inline onclick handlers.

---

## Step 9 — Verify ruff
**Command:** `ruff check riia-jun-release/src/rita/main.py`
**What:** Confirm the static mount addition introduced no lint errors.
**Why:** Mandatory quality gate per project rules.

---

## Step 10 — Smoke check
**What:** Grep that all new IDs and function names are consistent: `sec-agent-builds`, `n-agent-builds`, `loadAgentBuilds`, `agent-builds` in sectionLoaders, `ab-grid` in HTML and JS.
**Why:** Mismatched IDs are the most common cause of silent failures in this dashboard pattern.
