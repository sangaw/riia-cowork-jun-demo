import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from confluence.publish import ConfluenceClient, SECTION

TITLE = "Sprint 6 — Model Building, Performance Analytics & Drift Detection"
PAGE_ID = "71761921"

BODY = """
<h2>1. Overview</h2>
<p>
  Sprint 6 ported the remaining production-quality model-building components from the
  POC into <code>riia-jun-release</code>. Prior to Sprint 6, the backtest engine was a
  stub, the training tracker did not exist, and drift detection returned hard-coded values.
  All four gaps are now closed.
</p>
<ul>
  <li><strong>Day 35</strong> — Real DoubleDQN training engine with multi-seed support and a true backtest dispatch.</li>
  <li><strong>Day 36</strong> — TrainingTracker: per-round JSON records with val/backtest metrics and constraints.</li>
  <li><strong>Day 37</strong> — Performance analytics: portfolio comparison, qualitative feedback, stress scenarios.</li>
  <li><strong>Day 38</strong> — DriftDetector: 5 DB-backed health checks replacing the stub <code>/api/v1/drift</code>.</li>
</ul>

<h2>2. Day 35 — Training Engine &amp; Backtest Dispatch</h2>

<h3>2.1 train_best_of_n (core/trading_env.py)</h3>
<p>
  Runs <code>N</code> independent training seeds, evaluates each on a validation
  DataFrame, and returns the model with the highest Sharpe ratio. This makes training
  outcomes more reproducible and reduces the effect of random initialisation.
</p>
<pre>
best_model, best_sharpe = train_best_of_n(
    env_factory, train_df, val_df,
    timesteps=200_000, n_seeds=3
)
</pre>

<h3>2.2 Real Backtest Dispatch (core/backtest_dispatch.py)</h3>
<p>
  Replaced the previous stub with a deterministic <code>run_episode()</code> engine that:
</p>
<ul>
  <li>Loads the trained <code>.zip</code> model from the instrument model directory.</li>
  <li>Runs the agent step-by-step over the test period.</li>
  <li>Builds a <code>DailyResult</code> list with <code>portfolio_value</code>, <code>benchmark_value</code>,
      <code>allocation</code>, and <code>close_price</code> per day.</li>
  <li>Computes Sharpe, MDD, and return and writes them to the <code>backtest_results</code> table.</li>
</ul>
<table>
  <thead><tr><th>BacktestConfig field</th><th>Type</th><th>Description</th></tr></thead>
  <tbody>
    <tr><td>run_id</td><td>str</td><td>UUID matching the backtest_runs row</td></tr>
    <tr><td>start_date / end_date</td><td>date</td><td>Backtest window</td></tr>
    <tr><td>model_version</td><td>str</td><td>Stem of the .zip model file to load</td></tr>
    <tr><td>instrument</td><td>str</td><td>Instrument ID (default NIFTY)</td></tr>
  </tbody>
</table>

<h3>2.3 ml_dispatch n_seeds (core/ml_dispatch.py)</h3>
<p>
  <code>TrainingConfig</code> gained an <code>n_seeds</code> field (default 1).
  When <code>n_seeds &gt; 1</code>, dispatch calls <code>train_best_of_n</code>
  instead of a single training run. All structlog events now include
  <code>instrument</code>, <code>seed</code>, and <code>sharpe</code> for observability.
</p>

<h2>3. Day 36 — TrainingTracker</h2>

<h3>3.1 core/training_tracker.py</h3>
<p>
  Appends a JSON record to <code>{output_dir}/{instrument}/training_history.json</code>
  after every completed training round. Fields:
</p>
<table>
  <thead><tr><th>Field</th><th>Type</th><th>Description</th></tr></thead>
  <tbody>
    <tr><td>round</td><td>int</td><td>Monotonically increasing round number</td></tr>
    <tr><td>timestamp</td><td>ISO 8601</td><td>UTC time the round completed</td></tr>
    <tr><td>timesteps_trained</td><td>int</td><td>Total environment steps this round</td></tr>
    <tr><td>source</td><td>str</td><td>"trained" or "reused"</td></tr>
    <tr><td>seed</td><td>int | null</td><td>Random seed used (best seed when n_seeds &gt; 1)</td></tr>
    <tr><td>val_metrics</td><td>dict</td><td>sharpe, mdd, return on validation split</td></tr>
    <tr><td>backtest_metrics</td><td>dict</td><td>sharpe, mdd, return on backtest window</td></tr>
    <tr><td>constraints_met</td><td>bool</td><td>Sharpe &ge; 1.0 AND MDD &lt; 10%</td></tr>
    <tr><td>notes</td><td>str</td><td>Free text (risk tolerance, target, pipeline ID)</td></tr>
  </tbody>
</table>

<h3>3.2 Integration</h3>
<p>
  <code>workflow_service._run_training_job()</code> calls
  <code>TrainingTracker.record_round()</code> at the end of each run inside a
  <code>try/except</code> block so tracker failures never block training.
  <code>GET /api/v1/training-history</code> reads these records and returns them
  newest-first for the Training History table in the dashboard.
</p>

<h2>4. Day 37 — Performance Analytics</h2>

<h3>4.1 core/performance.py — New Functions</h3>
<table>
  <thead><tr><th>Function</th><th>Returns</th><th>Used by</th></tr></thead>
  <tbody>
    <tr>
      <td><code>build_performance_feedback(backtest_df, perf_metrics, training_rounds)</code></td>
      <td>Structured qualitative feedback: return metrics, risk metrics, trade activity, constraint status, forward expectations.</td>
      <td><code>GET /api/v1/performance-feedback</code></td>
    </tr>
    <tr>
      <td><code>build_portfolio_comparison(backtest_df, portfolio_inr)</code></td>
      <td>RITA model vs Conservative / Moderate / Aggressive fixed-allocation profiles over the same backtest window.</td>
      <td><code>GET /api/v1/portfolio-comparison</code></td>
    </tr>
    <tr>
      <td><code>simulate_stress_scenarios(portfolio_inr, market_moves, rita_allocation_pct)</code></td>
      <td>Point-in-time P&amp;L impact for each market move across all four profiles.</td>
      <td><code>GET /api/v1/stress-scenarios</code></td>
    </tr>
  </tbody>
</table>

<h3>4.2 New API Endpoints (observability.py)</h3>
<table>
  <thead><tr><th>Endpoint</th><th>Auth</th><th>Description</th></tr></thead>
  <tbody>
    <tr><td><code>GET /api/v1/performance-feedback</code></td><td>None</td><td>Qualitative feedback on latest backtest — classifies result as passing / marginal / failing with recommended next steps.</td></tr>
    <tr><td><code>GET /api/v1/portfolio-comparison</code></td><td>None</td><td>RITA vs fixed profiles: final value, CAGR, Sharpe, MDD per profile.</td></tr>
    <tr><td><code>GET /api/v1/stress-scenarios</code></td><td>None</td><td>Stress test across market moves: -20%, -10%, -5%, +5%, +10%, +20%.</td></tr>
  </tbody>
</table>

<h2>5. Day 38 — Drift Detection</h2>

<h3>5.1 core/drift_detector.py — DriftDetector</h3>
<p>
  Replaces the hard-coded drift stub with a DB-backed class running 5 independent checks:
</p>
<table>
  <thead><tr><th>Check</th><th>Data Source</th><th>Warn Threshold</th><th>Alert Threshold</th></tr></thead>
  <tbody>
    <tr><td>sharpe_drift</td><td>training_runs (last 3 completed)</td><td>Sharpe &lt; 1.0</td><td>Sharpe &lt; 0.5</td></tr>
    <tr><td>return_degradation</td><td>training_runs (last 3 completed)</td><td>Declining trend</td><td>Negative return</td></tr>
    <tr><td>data_freshness</td><td>market_data_cache</td><td>&gt; 7 days old</td><td>&gt; 30 days old</td></tr>
    <tr><td>pipeline_health</td><td>training_runs + backtest_runs</td><td>Any failed runs</td><td>All runs failed</td></tr>
    <tr><td>constraint_breach</td><td>training_runs</td><td>Latest run fails constraints</td><td>Last 3 all fail</td></tr>
  </tbody>
</table>

<h3>5.2 API Response Shape</h3>
<pre>
GET /api/v1/drift
{
  "summary": {
    "overall": "ok" | "warn" | "alert",
    "checks": { "sharpe_drift": "ok", "data_freshness": "warn", ... }
  },
  "checks": {
    "sharpe_drift":       { "status": "ok",   "message": "Sharpe 1.23 is healthy", "last_sharpe": 1.23 },
    "return_degradation": { "status": "ok",   "message": "Return trend stable" },
    "data_freshness":     { "status": "warn", "message": "Data is 12 days old", "days_old": 12 },
    "pipeline_health":    { "status": "ok",   "message": "All runs healthy (3 completed)" },
    "constraint_breach":  { "status": "ok",   "message": "Latest run meets constraints" }
  }
}
</pre>

<h2>6. Post-Sprint 6 Fixes (Days 39–40)</h2>
<table>
  <thead><tr><th>Day</th><th>Fix</th></tr></thead>
  <tbody>
    <tr>
      <td>Day 39</td>
      <td>RITA scenario e2e suite (20 tests) fixed: drift test updated to check <code>summary/checks</code>; training test now sends JWT via <code>auth_token</code> fixture. All 20 pass.</td>
    </tr>
    <tr>
      <td>Day 40</td>
      <td>FnO scenario suite (11 tests) and Ops scenario suite (16 tests) fixed: 8 missing portfolio endpoints added (<code>/summary</code>, <code>/price-history</code>, <code>/hedge-history</code>, <code>/man-groups</code>, <code>/man-snapshot</code>, <code>/man-pnl-history</code>, <code>/man-daily-status</code>, <code>/man-daily-snapshot</code>); <code>/api/v1/data-prep/status</code> added to observability. Both suites pass 100%.</td>
    </tr>
  </tbody>
</table>

<h2>7. Test Results</h2>
<table>
  <thead><tr><th>Suite</th><th>Pass</th><th>Fail</th><th>Note</th></tr></thead>
  <tbody>
    <tr><td>Unit + Integration</td><td>121</td><td>1</td><td>1 pre-existing JWT env-var test (pydantic-settings conflict)</td></tr>
    <tr><td>RITA e2e scenarios</td><td>20</td><td>0</td><td>All 20 RITA dashboard scenarios pass</td></tr>
    <tr><td>FnO e2e scenarios</td><td>11</td><td>0</td><td>All 11 FnO dashboard scenarios pass</td></tr>
    <tr><td>Ops e2e scenarios</td><td>16</td><td>0</td><td>All 16 Ops dashboard scenarios pass</td></tr>
    <tr><td><strong>Total</strong></td><td><strong>168</strong></td><td><strong>1</strong></td><td>1 pre-existing failure not introduced by Sprint 6</td></tr>
  </tbody>
</table>
"""


if __name__ == "__main__":
    client = ConfluenceClient()

    if PAGE_ID:
        page_id, url = client.update_page(PAGE_ID, TITLE, BODY)
        print(f"Sprint 6 technical page updated: {url}")
    else:
        page_id, url = client.create_page(TITLE, BODY, parent_id=SECTION["engineering"])
        print(f"Sprint 6 technical page created: {url}")
        print(f"Page ID: {page_id}")
        print(f'\nPaste into PAGE_ID: "{page_id}"')
