"""
TechWriter update: Engineering Confluence page (76611602)
Run ID: 20260515-0859
Changes: Agent Builds defect fixes + Actual Token Tracking feature
"""
import sys, importlib.util

spec = importlib.util.spec_from_file_location(
    "publish",
    "C:/Users/Sandeep/Documents/Work/code/riia-cowork-jun/project-office/confluence/publish.py"
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
ConfluenceClient = mod.ConfluenceClient
SECTION = mod.SECTION

PAGE_ID = SECTION["engineering_current"]

# ── Fetch current page ──────────────────────────────────────────────────────
client = ConfluenceClient()
page = client.get_page(PAGE_ID, expand="version,body.storage")
current_body = page["body"]["storage"]["value"]
title = page["title"]
print(f"Fetched '{title}' — version {page['version']['number']}, {len(current_body)} chars")

# ── Patch the agent-builds endpoint row to add the new fields ──────────────
OLD_AGENT_BUILDS_ROW = (
    "<tr><td>/api/experience/ops/agent-builds</td><td>GET</td>"
    "<td>Returns agent build pipeline runs and aggregated metrics from the database "
    "(replaces static JSON reads). Query params: <code>limit</code> (int, default 20, max 200), "
    "<code>app</code> (str, optional filter). Auth: none.</td></tr>"
)

NEW_AGENT_BUILDS_ROW = (
    "<tr><td>/api/experience/ops/agent-builds</td><td>GET</td>"
    "<td>Returns agent build pipeline runs and aggregated metrics from the database "
    "(replaces static JSON reads). Query params: <code>limit</code> (int, default 20, max 200), "
    "<code>app</code> (str, optional filter). Auth: none. "
    "<strong>New fields (2026-05-15):</strong> "
    "<code>human_score_csat</code> (Optional[float]) added to each run; "
    "<code>agents[].actual_tokens</code> (Optional[dict] — input_tokens, output_tokens, "
    "cache_read_input_tokens, cache_creation_input_tokens, total_tokens) added per agent. "
    "<code>SkillVersion.recent_commits</code> type corrected from <code>list[str]</code> "
    "to <code>list[dict]</code> (fields: hash, message).</td></tr>"
)

if OLD_AGENT_BUILDS_ROW in current_body:
    updated_body = current_body.replace(OLD_AGENT_BUILDS_ROW, NEW_AGENT_BUILDS_ROW)
    print("Patched agent-builds endpoint row.")
else:
    # Row may already be updated; append note at end instead
    updated_body = current_body
    print("WARNING: agent-builds row not found verbatim — will append section only.")

# ── New section to append ──────────────────────────────────────────────────
NEW_SECTION = """
<hr />

<h2>Agent Builds Defect Fixes &amp; Actual Token Tracking (2026-05-15)</h2>
<p>Run ID: <strong>20260515-0859</strong> &mdash; Ops Agent Builds page updated with four defect fixes and a new Actual Token Tracking feature.</p>

<h3>Defect Fixes</h3>
<table>
  <thead><tr><th>Priority</th><th>Defect</th><th>Fix</th></tr></thead>
  <tbody>
    <tr>
      <td>P1</td>
      <td>Metric Trend Lines not rendering</td>
      <td>
        <code>AgentBuildRunOut</code> gained <code>human_score_csat: Optional[float]</code> from per-run JSON.
        <code>mountTrendChart(m, runs)</code> and <code>renderTrendPanel(m, runs)</code> signatures updated to
        derive TSR, CSAT, and adherence from <code>runs</code> array rather than grounding_trend items.
      </td>
    </tr>
    <tr>
      <td>P1</td>
      <td>Skill Version History empty</td>
      <td>
        <code>get_agent_builds</code> endpoint now joins skill files against <code>metrics.json</code>
        <code>skill_version_history</code> by <code>skill_file</code> name, populating
        <code>last_updated</code>, <code>improvement_applied</code>, <code>before_first_pass_rate</code>,
        <code>after_first_pass_rate</code>, and <code>recent_commits</code>.
        JS <code>renderSkillVersions</code> gains Improvement and Rate &Delta; columns.
      </td>
    </tr>
    <tr>
      <td>P2</td>
      <td>Token Estimate result cards blank</td>
      <td>
        <code>submitTokenEstimate</code> now populates <code>#ab-res-complexity</code>,
        <code>#ab-res-total</code>, and <code>#ab-res-confidence</code> with null guards.
      </td>
    </tr>
    <tr>
      <td>P3</td>
      <td>recent_commits showing &ldquo;[object Object]&rdquo;</td>
      <td>
        <code>SkillVersion.recent_commits</code> type changed from <code>list[str]</code> to
        <code>list[dict]</code>. JS now renders <code>${hash} &mdash; ${message}</code> per commit.
      </td>
    </tr>
  </tbody>
</table>

<h3>New Feature: Actual Token Tracking</h3>
<table>
  <thead><tr><th>Component</th><th>Change</th></tr></thead>
  <tbody>
    <tr>
      <td>Schema</td>
      <td><code>AgentOut.actual_tokens: Optional[dict]</code> &mdash; fields: input_tokens, output_tokens, cache_read_input_tokens, cache_creation_input_tokens, total_tokens.</td>
    </tr>
    <tr>
      <td>ORM Model</td>
      <td><code>AgentBuildAgentModel.actual_tokens_total = Column(Integer, nullable=True)</code> added; migration <code>a3f9c1e82b5d</code> adds the column with an idempotent column-exists guard.</td>
    </tr>
    <tr>
      <td>API</td>
      <td><code>actual_tokens</code> read from per-run JSON <code>agents[].actual_tokens</code> by role match in <code>src/rita/api/experience/ops.py</code>.</td>
    </tr>
    <tr>
      <td>Run History Table</td>
      <td>&ldquo;Est / Actual&rdquo; column replaces &ldquo;Forecast &Delta;&rdquo; column, colour-coded green/amber/red.</td>
    </tr>
    <tr>
      <td>Token Chart</td>
      <td>Dashed actual datasets appended per role alongside solid estimate datasets in the token breakdown chart.</td>
    </tr>
    <tr>
      <td>Forecast Chart</td>
      <td>Actual bar now sums <code>actual_tokens.total_tokens</code> per run (not <code>total_tokens_estimated</code>).</td>
    </tr>
    <tr>
      <td>Cache Hit Rate KPI</td>
      <td>New KPI card <code>ab-kpi-cache-hit</code> added to the Agent Builds KPI row.</td>
    </tr>
    <tr>
      <td>aggregate_metrics.py</td>
      <td><code>by_feature_type</code> average now prefers actual token sum over estimated when actual data is present.</td>
    </tr>
  </tbody>
</table>

<h3>Files Changed</h3>
<table>
  <thead><tr><th>File</th><th>Change</th></tr></thead>
  <tbody>
    <tr><td><code>src/rita/schemas/agent_builds.py</code></td><td>Added <code>actual_tokens</code> to <code>AgentOut</code>, <code>human_score_csat</code> to <code>AgentBuildRunOut</code>, <code>SkillVersion.recent_commits</code> changed to <code>list[dict]</code></td></tr>
    <tr><td><code>src/rita/models/agent_builds.py</code></td><td>Added <code>actual_tokens_total</code> column</td></tr>
    <tr><td><code>alembic/versions/a3f9c1e82b5d_add_actual_tokens_total.py</code></td><td>New migration</td></tr>
    <tr><td><code>src/rita/api/experience/ops.py</code></td><td>Skill version history join; human_score_csat; actual_tokens per agent</td></tr>
    <tr><td><code>dashboard/js/ops/agent-builds.js</code></td><td>All four defect fixes + actual token tracking features</td></tr>
    <tr><td><code>dashboard/ops.html</code></td><td>Added <code>ab-kpi-cache-hit</code> KPI card</td></tr>
    <tr><td><code>riia-ai-org/agent-ops/aggregate_metrics.py</code></td><td>Prefer actual tokens in by_feature_type avg</td></tr>
    <tr><td><code>project-office/specs/Spec_RITA_App.md</code></td><td>Updated agent-builds endpoint entry</td></tr>
    <tr><td><code>project-office/specs/Spec_JS_Code.md</code></td><td>Updated agent-builds.js module entry</td></tr>
  </tbody>
</table>
<p><strong>Commit:</strong> fd8d45a &mdash; Branch: worktree-agent-a97a304a7739f9ca0</p>
"""

final_body = updated_body + NEW_SECTION

# ── Publish ─────────────────────────────────────────────────────────────────
result_id, url = client.update_page(PAGE_ID, title, final_body)
print(f"Updated page: {url}")
print(f"Page ID: {result_id}")
