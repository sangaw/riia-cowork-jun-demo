"""
Publishes (or updates) the Sprint 6 board page under Sprint Boards in Confluence.
Run at end of each Sprint 6 day to reflect progress.

First run:  PAGE_ID = None  → creates the page, prints the ID → paste it below
Subsequent: PAGE_ID = "..."  → updates the existing page in-place
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from confluence.publish import ConfluenceClient, SECTION

TITLE = "Sprint 6 — Model Building, Logging & Performance Metrics"

# After first run, paste the returned page ID here so subsequent runs update in-place.
PAGE_ID = "70909953"

BODY = """
<h1>Sprint 6 &mdash; Model Building, Logging &amp; Performance Metrics</h1>
<p><strong>Duration:</strong> Days 35&ndash;38 &nbsp;|&nbsp; <strong>Theme:</strong> Port real DoubleDQN training engine, multi-seed training, TrainingTracker, performance analytics, and drift detection from POC. Replaces all stubs with production-quality implementations.</p>
<p><strong>Decision (2026-04-12):</strong> Sprint 6 added to address remaining model-building gaps. Backtest dispatch was still a stub; TrainingTracker and drift detection were missing. All 4 days complete as of 2026-04-13.</p>

<table>
  <thead>
    <tr>
      <th>Day</th>
      <th>Role</th>
      <th>Task</th>
      <th>Status</th>
      <th>Notes</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Day 35</td>
      <td>Engineer</td>
      <td>train_best_of_n + real backtest_dispatch + ml_dispatch n_seeds</td>
      <td><strong style="color:#1a6b3c">&#10003; Done</strong></td>
      <td>train_best_of_n added to trading_env.py; backtest_dispatch replaced with real run_episode() engine (no more stubs); ml_dispatch extended with n_seeds support + structlog step events throughout.</td>
    </tr>
    <tr>
      <td>Day 36</td>
      <td>Engineer</td>
      <td>TrainingTracker + structlog step events in ml_dispatch</td>
      <td><strong style="color:#1a6b3c">&#10003; Done</strong></td>
      <td>core/training_tracker.py created. Records each training round with val_metrics, backtest_metrics, constraints_met, seed, notes. Wired into workflow_service inside try/except so tracker failure never blocks training. structlog events added to all ml_dispatch steps.</td>
    </tr>
    <tr>
      <td>Day 37</td>
      <td>Engineer</td>
      <td>Performance analytics (portfolio comparison, feedback, stress) + 2 new API endpoints</td>
      <td><strong style="color:#1a6b3c">&#10003; Done</strong></td>
      <td>core/performance.py: build_portfolio_comparison(), build_performance_feedback(), simulate_stress_scenarios(). New endpoints: /api/v1/performance-feedback, /api/v1/portfolio-comparison, /api/v1/stress-scenarios. Added to observability.py router.</td>
    </tr>
    <tr>
      <td>Day 38</td>
      <td>Engineer</td>
      <td>DriftDetector rebased on DB + /api/v1/drift upgrade</td>
      <td><strong style="color:#1a6b3c">&#10003; Done</strong></td>
      <td>core/drift_detector.py created with 5 DB-backed checks: Sharpe drift, return degradation, data freshness, pipeline health, constraint breach. /api/v1/drift endpoint upgraded to use DriftDetector. 121/122 tests pass (1 pre-existing config failure).</td>
    </tr>
  </tbody>
</table>

<h2>Sprint 6 Deliverables</h2>

<h3>Day 35 &mdash; DoubleDQN Training Engine</h3>
<h4>New / Modified Files</h4>
<table>
  <thead><tr><th>File</th><th>Change</th></tr></thead>
  <tbody>
    <tr><td><code>src/rita/core/trading_env.py</code></td><td>Added <code>train_best_of_n()</code> — runs N training seeds, evaluates each on val_df, returns best model by Sharpe. Added <code>load_agent()</code> for backtest reuse.</td></tr>
    <tr><td><code>src/rita/core/backtest_dispatch.py</code></td><td>Replaced stub with real implementation: loads model zip, runs deterministic <code>run_episode()</code>, builds DailyResult list with portfolio + benchmark + allocation values.</td></tr>
    <tr><td><code>src/rita/core/ml_dispatch.py</code></td><td>Added <code>n_seeds</code> to TrainingConfig; routes to <code>train_best_of_n</code> when n_seeds &gt; 1. structlog events at each pipeline step.</td></tr>
  </tbody>
</table>

<h3>Day 36 &mdash; TrainingTracker</h3>
<h4>New Files</h4>
<table>
  <thead><tr><th>File</th><th>Purpose</th></tr></thead>
  <tbody>
    <tr><td><code>src/rita/core/training_tracker.py</code></td><td>Appends a JSON record per training round to <code>training_history.json</code> in the model output directory. Fields: round, timestamp, timesteps_trained, source, seed, val_metrics, backtest_metrics, constraints_met, notes.</td></tr>
  </tbody>
</table>

<h4>Integration</h4>
<ul>
  <li><code>workflow_service._run_training_job()</code> calls <code>TrainingTracker.record_round()</code> after each completed training run inside a try/except block.</li>
  <li><code>/api/v1/training-history</code> endpoint reads the JSON file and returns rounds for the Training Progress chart in the dashboard.</li>
</ul>

<h3>Day 37 &mdash; Performance Analytics</h3>
<h4>New API Endpoints</h4>
<table>
  <thead><tr><th>Endpoint</th><th>Description</th></tr></thead>
  <tbody>
    <tr><td><code>GET /api/v1/performance-feedback</code></td><td>Returns qualitative performance feedback based on Sharpe, MDD, CAGR constraints. Classifies result as passing/marginal/failing with recommended next steps.</td></tr>
    <tr><td><code>GET /api/v1/portfolio-comparison</code></td><td>Returns RITA portfolio vs Nifty Buy-and-Hold comparison metrics from the latest backtest run.</td></tr>
    <tr><td><code>GET /api/v1/stress-scenarios</code></td><td>Simulates 4 stress scenarios (2020 crash, 2022 bear, sideways chop, rally) against the trained model. Returns scenario-by-scenario return and Sharpe estimates.</td></tr>
  </tbody>
</table>

<h3>Day 38 &mdash; Drift Detection</h3>
<h4>New Files</h4>
<table>
  <thead><tr><th>File</th><th>Purpose</th></tr></thead>
  <tbody>
    <tr><td><code>src/rita/core/drift_detector.py</code></td><td>DriftDetector class with 5 checks: (1) Sharpe drift across last 3 rounds, (2) return degradation trend, (3) data freshness (days since latest CSV), (4) pipeline health (recent training/backtest failures), (5) constraint breach history.</td></tr>
  </tbody>
</table>

<h4>API Change</h4>
<p><code>GET /api/v1/drift</code> now delegates to <code>DriftDetector</code> (DB-backed) instead of returning static stubs. Returns <code>health</code> (ok/warn/err) + per-check <code>report</code> dict. Powers the Drift section of the ops dashboard.</p>

<h2>Also Fixed in Sprint 6 (Defect)</h2>
<p><strong>Bug: force_retrain flag ignored in pipeline endpoint.</strong><br/>
<code>POST /api/v1/pipeline</code> accepted <code>force_retrain: false</code> but never checked it — always rebuilt the model. Fixed in <code>_run_pipeline_job()</code>: when <code>force_retrain=False</code> and a <code>.zip</code> exists in <code>model_dir</code>, the existing model is reused and training is skipped. Both <code>BacktestRunCreate</code> and <code>BacktestConfig</code> receive the existing model's filename stem as <code>model_version</code>.</p>

<h2>Test Results</h2>
<table>
  <thead><tr><th>Suite</th><th>Pass</th><th>Fail</th><th>Note</th></tr></thead>
  <tbody>
    <tr><td>Unit + Integration (all)</td><td>121</td><td>1</td><td>Pre-existing: test_jwt_secret_from_env_var (pydantic-settings validation_alias + env_prefix conflict)</td></tr>
    <tr><td><strong>Total</strong></td><td><strong>121</strong></td><td><strong>1</strong></td><td>1 pre-existing failure carried from Sprint 5 — not introduced by Sprint 6</td></tr>
  </tbody>
</table>

<h2>Sprint 6 Definition of Done</h2>
<ul>
  <li>&#10003; Real DoubleDQN training engine (no stubs)</li>
  <li>&#10003; Multi-seed training support</li>
  <li>&#10003; TrainingTracker records each round to JSON</li>
  <li>&#10003; Performance analytics (comparison, feedback, stress)</li>
  <li>&#10003; DriftDetector with 5 DB-backed checks</li>
  <li>&#10003; Pipeline model-reuse bug fixed</li>
  <li>&#10003; 121/122 tests pass</li>
</ul>
"""


if __name__ == "__main__":
    client = ConfluenceClient()

    if PAGE_ID:
        page_id, url = client.update_page(PAGE_ID, TITLE, BODY)
        print(f"Sprint 6 board updated: {url}")
    else:
        page_id, url = client.create_page(TITLE, BODY, parent_id=SECTION["sprint_boards"])
        print(f"Sprint 6 board created: {url}")
        print(f"Page ID: {page_id}")
        print(f"\nPaste this into PAGE_ID at the top of this script for future updates:")
        print(f'PAGE_ID = "{page_id}"')
