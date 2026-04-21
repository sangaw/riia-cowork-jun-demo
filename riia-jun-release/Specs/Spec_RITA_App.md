 Flow: Instrument Tab Click ? Metrics

  Entry point: rita.html ? buttons NIFTY 50 / BANKNIFTY / ASML / NVIDIA each call onclick="selectInstrumentTab('NIFTY')" etc.

  Call chain (main.js:84):
  selectInstrumentTab(id)
    1. POST /api/v1/instrument/select      ? sets _active_instrument_id in-memory on server
    2. GET  /api/v1/instrument/active      ? updates topbar pill (name/flag)
    3. GET  /api/v1/performance-summary    ? this is what drives the KPI metrics cards
    4. GET  /health                        ? model status card only
    5. GET  /api/v1/drift                  ? alert strip
    6. GET  /progress                      ? pipeline step bar

  ---
  Why Metrics Don't Load

  The key is in loadPerfSummary() (health.js:88). It reads the response and does a stale check:

  const stale = d._run_instrument_id !== d._active_instrument_id;
  if (stale) {
    // blanks ALL KPIs: kpi-return, kpi-sharpe, kpi-mdd, etc. ? shows "—"
    // sets kpi-days to "Run pipeline"
    return;
  }
  if (d.portfolio_total_return_pct == null) return;  // no data at all ? silent skip

  On the backend (observability.py:383), performance_summary returns:
  - _active_instrument_id = whatever is in-memory (just set by POST /instrument/select)
  - _run_instrument_id = instrument of the globally latest training run in the DB
  
  
  
  The APIs read entirely from SQLite (rita.db). No model folder files are read by the performance API. The model folders store only the .zip weights and
    training_history.csv.
  
    ---
    What a Model Run Actually Writes
  
    Pipeline run (training) ? WorkflowService
      ? models/NIFTY/pipeline-{id}.zip          ? model weights (file)
      ? models/NIFTY/training_history.csv       ? CSV written by TrainingTracker (file)
      ? DB: training_runs table                 ? has instrument column ?
      ? DB: training_metrics table              ? episode-level rewards/loss ?
  
    Pipeline run (backtest) ? BacktestService
      ? DB: backtest_runs table                 ? NO instrument column ?
    ? DB: backtest_results table              ? NO instrument column ?