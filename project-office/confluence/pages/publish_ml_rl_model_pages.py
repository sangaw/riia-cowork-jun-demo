"""
Create two engineering documentation pages under Engineering Documentation (65404944):
  1. RL Trading Model  — agent design, environment, DQN config, training
  2. ML Training Pipeline — orchestration, indicators, performance metrics, drift

Style follows: User Chat Feature (74940444) and User Chat Feature Build (74973219).

Run from any directory:
  CONFLUENCE_EMAIL=contact@ravionics.nl python project-office/confluence/pages/publish_ml_rl_model_pages.py
"""

import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from confluence.publish import ConfluenceClient, SECTION

PARENT_ID = SECTION["engineering"]  # 65404944 — Engineering Documentation section

# ─────────────────────────────────────────────────────────────────────────────
# PAGE 1 — RL Trading Model
# ─────────────────────────────────────────────────────────────────────────────

RL_MODEL_HTML = """
<h1>RL Trading Model</h1>
<p><strong>Version:</strong> v1.0 &nbsp;|&nbsp; <strong>Date:</strong> 2026-04-29</p>
<p>The RITA RL Trading Model is a <strong>Double Deep Q-Network (DDQN)</strong> agent that learns
to allocate capital across three positions (0%, 50%, 100% invested) by training on 25+ years of
NIFTY 50 OHLCV data. The goal is a Sharpe ratio &gt; 1.0 with maximum drawdown &lt; 10%.</p>

<p>Source files:</p>
<ul>
  <li><code>src/rita/core/trading_env.py</code> — environment, training, inference</li>
  <li><code>src/rita/core/ml_dispatch.py</code> — training orchestration entry point</li>
</ul>

<hr/>

<h2>Design Goals</h2>
<table>
  <thead><tr><th>Constraint</th><th>Target</th><th>Why</th></tr></thead>
  <tbody>
    <tr><td>Sharpe ratio</td><td>&gt; 1.0</td><td>Risk-adjusted return must exceed Buy &amp; Hold on an annualised basis</td></tr>
    <tr><td>Max drawdown</td><td>&lt; &minus;10%</td><td>Capital preservation — a 10% loss triggers the drawdown penalty in the reward function</td></tr>
    <tr><td>Action space</td><td>Discrete (3)</td><td>Keeps the policy stable and interpretable; continuous allocation is unnecessary for daily rebalancing</td></tr>
    <tr><td>No lookahead</td><td>Today's observation only</td><td>Only data available at the close of day t is used to decide allocation for day t+1</td></tr>
  </tbody>
</table>

<hr/>

<h2>Environment — <code>RIIATradingEnv</code></h2>
<p>A custom <strong>Gymnasium</strong> environment. Each episode covers a random
252-day (~1 year) window drawn from the training DataFrame.</p>

<h3>Observation Space (8 or 9 features)</h3>
<table>
  <thead><tr><th>Index</th><th>Feature</th><th>Source column</th><th>Scaling</th></tr></thead>
  <tbody>
    <tr><td>0</td><td>Daily return</td><td><code>daily_return</code></td><td>× 10, clipped to [−3, 3]</td></tr>
    <tr><td>1</td><td>RSI-14 normalised</td><td><code>rsi_14</code></td><td>÷ 100, clipped to [0, 1]</td></tr>
    <tr><td>2</td><td>MACD / price</td><td><code>macd / Close</code></td><td>× 1000, clipped to [−3, 3]</td></tr>
    <tr><td>3</td><td>Bollinger %B</td><td><code>bb_pct_b</code></td><td>clipped to [−0.5, 1.5]</td></tr>
    <tr><td>4</td><td>Trend score</td><td><code>trend_score</code></td><td>clipped to [−1, 1]</td></tr>
    <tr><td>5</td><td>Current allocation</td><td>internal state</td><td>0.0, 0.5, or 1.0</td></tr>
    <tr><td>6</td><td>Days remaining</td><td>internal state</td><td>1 − step / episode_length</td></tr>
    <tr><td>7</td><td>ATR / price</td><td><code>atr_14 / Close</code></td><td>× 100, clipped to [0, 3]</td></tr>
    <tr><td>8*</td><td>EMA ratio</td><td><code>ema_26 / ema_50</code></td><td>clipped to [0.5, 1.5], then (ratio − 1) × 20; only present when column exists</td></tr>
  </tbody>
</table>
<p>* Feature 8 is added automatically when <code>ema_ratio</code> is present in the DataFrame, giving a 9-feature observation for instruments with sufficient history.</p>

<h3>Action Space (Discrete 3)</h3>
<table>
  <thead><tr><th>Action</th><th>Allocation</th><th>Meaning</th></tr></thead>
  <tbody>
    <tr><td>0</td><td>0%</td><td>Cash — no market exposure</td></tr>
    <tr><td>1</td><td>50%</td><td>Half invested</td></tr>
    <tr><td>2</td><td>100%</td><td>Fully invested</td></tr>
  </tbody>
</table>

<h3>Reward Function</h3>
<pre>
reward = portfolio_return_for_step
if cumulative_drawdown &lt; -10%:
    reward -= 0.005   # flat penalty per step below the drawdown threshold
</pre>
<p>The drawdown penalty (<code>DRAWDOWN_THRESHOLD = -0.10</code>) discourages the agent from staying
invested through prolonged losing streaks. The penalty is applied every step until the drawdown
recovers above −10%, not just at the moment of breach.</p>

<h3>Episode Mechanics</h3>
<ul>
  <li>Each reset samples a random 252-day start index from the available DataFrame.</li>
  <li>Portfolio value is initialised at 1.0 (normalised). Peak value tracks the running maximum for drawdown calculation.</li>
  <li>The episode terminates when <code>step_idx &gt;= episode_length</code>.</li>
  <li>Observation space bounds are <code>Box(low=-3.0, high=3.0, shape=(n_features,))</code>. All features are pre-scaled to fit well within these bounds.</li>
</ul>

<hr/>

<h2>DQN Configuration</h2>
<table>
  <thead><tr><th>Hyperparameter</th><th>Value</th><th>Notes</th></tr></thead>
  <tbody>
    <tr><td>Algorithm</td><td>DQN (stable-baselines3)</td><td>Uses Double DQN internally via SB3 defaults</td></tr>
    <tr><td>Policy</td><td>MlpPolicy</td><td>Two hidden layers, 256 units each</td></tr>
    <tr><td>Net arch</td><td>[256, 256]</td><td>Configured via <code>policy_kwargs={"net_arch": [256, 256]}</code></td></tr>
    <tr><td>Learning rate</td><td>1e-4 (default)</td><td>Per-instrument override available in <code>config/instruments/{instrument}.yaml</code></td></tr>
    <tr><td>Buffer size</td><td>100,000</td><td>Replay buffer capacity</td></tr>
    <tr><td>Learning starts</td><td>2,000 steps</td><td>Random exploration before gradient updates begin</td></tr>
    <tr><td>Batch size</td><td>64</td><td>Mini-batch drawn from replay buffer per update</td></tr>
    <tr><td>Gamma (discount)</td><td>0.99</td><td>Long-horizon preference — daily trading horizon is 252 steps</td></tr>
    <tr><td>Tau (soft update)</td><td>0.005</td><td>Target network update rate — stabilises training</td></tr>
    <tr><td>Train frequency</td><td>every 4 steps</td><td>Gradient step after every 4 environment steps</td></tr>
    <tr><td>Target update interval</td><td>1</td><td>Target network synced every gradient step (soft update via tau)</td></tr>
    <tr><td>Exploration fraction</td><td>0.5 (default)</td><td>Fraction of total timesteps over which epsilon decays 1.0 → 0.05</td></tr>
    <tr><td>Exploration final eps</td><td>0.05</td><td>Minimum epsilon — 5% random exploration throughout inference warm-up</td></tr>
  </tbody>
</table>

<hr/>

<h2>Training — Single Seed</h2>
<p>Function: <code>train_agent(train_df, output_dir, timesteps, ...)</code> in <code>trading_env.py</code></p>
<pre>
env = Monitor(RIIATradingEnv(train_df))
model = DQN("MlpPolicy", env, learning_rate=lr, buffer_size=buf, ...)
progress_cb = TrainingProgressCallback(log_interval=1_000)
model.learn(total_timesteps=timesteps, callback=progress_cb)
model.save(output_dir / model_name)
</pre>
<ul>
  <li><code>TrainingProgressCallback</code> records <code>{timestep, loss, ep_rew_mean}</code> every 1,000 steps.</li>
  <li>Records are forwarded to <code>progress_fn(record)</code> if provided — used by WorkflowService for live polling via <code>GET /api/v1/training-history</code>.</li>
  <li>Model is saved as <code>{model_name}.zip</code> using SB3's <code>model.save()</code>.</li>
</ul>

<hr/>

<h2>Training — Multi-Seed (<code>train_best_of_n</code>)</h2>
<p>When <code>n_seeds &gt; 1</code>, the dispatcher runs N independent training seeds and selects the winner by validation Sharpe ratio.</p>
<pre>
for seed in range(n_seeds):
    model, cb = train_agent(..., seed=seed)
    val_result = validate_agent(model, val_df)   # run deterministic episode on held-out data
    seed_results.append({"seed": seed, "val_sharpe": val_result["sharpe_ratio"]})

best_model = the seed with highest val_sharpe
best_model.save(output_dir / model_name)        # overwrites the canonical model path
</pre>
<p>The <code>TrainingOutcome.seed_results</code> dict carries <code>{best_seed, n_seeds_tried, seed_results}</code>
back to WorkflowService and is stored in the training_runs table.</p>

<hr/>

<h2>Validation &amp; Inference — <code>run_episode</code></h2>
<p>Used for both validation (held-out period) and backtest (arbitrary date range).
Runs the model <strong>deterministically</strong> (<code>model.predict(obs, deterministic=True)</code>)
through the full DataFrame — no random start offset, no epsilon exploration.</p>
<pre>
portfolio_value = 1.0
for each row in df:
    obs = build_observation(row, current_allocation)
    action, _ = model.predict(obs, deterministic=True)
    allocation = {0: 0.0, 1: 0.5, 2: 1.0}[action]
    portfolio_value *= (1 + allocation * next_row["daily_return"])

perf = compute_all_metrics(portfolio_values, benchmark_values)
</pre>
<p>Returns: <code>portfolio_values, benchmark_values, allocations, daily_returns, dates, close_prices, performance</code></p>

<hr/>

<h2>Instrument Configuration</h2>
<p>Per-instrument training defaults live in <code>config/instruments/{instrument}.yaml</code>
under the <code>training:</code> key. Loaded once and cached in <code>_INSTRUMENT_DEFAULTS_CACHE</code>.</p>
<table>
  <thead><tr><th>Key</th><th>Description</th></tr></thead>
  <tbody>
    <tr><td><code>timesteps</code></td><td>Total SB3 training steps for this instrument</td></tr>
    <tr><td><code>learning_rate</code></td><td>Override the default 1e-4</td></tr>
    <tr><td><code>buffer_size</code></td><td>Override the default 100,000</td></tr>
    <tr><td><code>exploration_pct</code></td><td>Override the exploration fraction</td></tr>
    <tr><td><code>n_seeds</code></td><td>Number of seeds for <code>train_best_of_n</code></td></tr>
    <tr><td><code>episode_length</code></td><td>Override the default 252-day episode window</td></tr>
  </tbody>
</table>
<p>If no config file exists for an instrument, all defaults from <code>train_agent()</code> apply and a
<code>instrument_defaults.not_found</code> warning is logged via structlog.</p>

<hr/>

<h2>Data Split</h2>
<table>
  <thead><tr><th>Split</th><th>Fraction</th><th>Use</th></tr></thead>
  <tbody>
    <tr><td>Train</td><td>First 80% by date</td><td>Agent learns from this data during SB3 <code>model.learn()</code></td></tr>
    <tr><td>Validation</td><td>Last 20% by date</td><td>Held-out; used to compute real Sharpe/MDD after training and to select the best seed in multi-seed runs</td></tr>
  </tbody>
</table>
<p>Split is a simple date-ordered slice: <code>split_idx = int(len(df) * 0.8)</code>. No shuffling — financial time series must not have future data leaked into training.</p>

<hr/>

<h2>Model Storage</h2>
<table>
  <thead><tr><th>Path</th><th>Contents</th></tr></thead>
  <tbody>
    <tr><td><code>data/output/{INSTRUMENT}/{model_name}.zip</code></td><td>Trained SB3 DQN model. Loaded by <code>load_agent(model_path)</code> for inference and backtest.</td></tr>
  </tbody>
</table>
<p>The <code>/health</code> endpoint checks for <code>model_exists: true</code> by scanning this directory.
The backtest dispatcher resolves <code>"latest"</code> to the most recently modified .zip file.</p>

<hr/>

<h2>Supported Instruments</h2>
<table>
  <thead><tr><th>Instrument</th><th>Training data</th><th>Notes</th></tr></thead>
  <tbody>
    <tr><td>NIFTY</td><td>1999–present</td><td>Primary instrument; longest history; 9-feature obs when ema_ratio available</td></tr>
    <tr><td>BANKNIFTY</td><td>2007–present</td><td>Secondary; shorter history reduces usable episode count</td></tr>
    <tr><td>ASML</td><td>2001–present</td><td>Euronext; FnO positions + Agent Panel demo</td></tr>
    <tr><td>NVIDIA</td><td>2001–present</td><td>NASDAQ; portfolio benchmarking</td></tr>
  </tbody>
</table>
"""

# ─────────────────────────────────────────────────────────────────────────────
# PAGE 2 — ML Training Pipeline
# ─────────────────────────────────────────────────────────────────────────────

ML_PIPELINE_HTML = """
<h1>ML Training Pipeline</h1>
<p><strong>Version:</strong> v1.0 &nbsp;|&nbsp; <strong>Date:</strong> 2026-04-29</p>
<p>The ML Training Pipeline orchestrates the full journey from raw OHLCV CSV files to a validated
DDQN model and performance metrics. It is triggered by <code>POST /api/v1/train</code> and runs
entirely in a background thread — no blocking of the API server.</p>

<p>Key source files:</p>
<ul>
  <li><code>src/rita/core/ml_dispatch.py</code> — training entry point (<code>train()</code>)</li>
  <li><code>src/rita/core/backtest_dispatch.py</code> — historical backtest (<code>run_backtest()</code>)</li>
  <li><code>src/rita/core/technical_analyzer.py</code> — feature engineering (<code>calculate_indicators()</code>)</li>
  <li><code>src/rita/core/performance.py</code> — metrics (<code>compute_all_metrics()</code>)</li>
  <li><code>src/rita/core/data_loader.py</code> — CSV loading</li>
  <li><code>src/rita/core/drift_detector.py</code> — model drift checks</li>
</ul>

<hr/>

<h2>End-to-End Training Pipeline</h2>
<p>Triggered by <code>WorkflowService.run_training(config)</code> in a background thread.
The 7-step pipeline runs inside <code>ml_dispatch.train(config)</code>:</p>

<table>
  <thead><tr><th>Step</th><th>Action</th><th>Output</th></tr></thead>
  <tbody>
    <tr><td>1</td><td>Load OHLCV CSV via <code>find_instrument_csv()</code> + <code>load_nifty_csv()</code></td><td>Raw DataFrame (date-indexed)</td></tr>
    <tr><td>2</td><td>Compute 17 technical indicators via <code>calculate_indicators(df)</code></td><td>DataFrame with RSI, MACD, BB, ATR, EMAs, trend_score, ema_ratio, daily_return</td></tr>
    <tr><td>3</td><td>80/20 train/validation split by date</td><td><code>train_df</code>, <code>val_df</code></td></tr>
    <tr><td>4</td><td>Train DDQN — single seed or <code>train_best_of_n</code></td><td>Trained <code>DQN</code> model, <code>TrainingProgressCallback</code></td></tr>
    <tr><td>5</td><td>Validation episode — <code>run_episode(model, val_df)</code></td><td>Real Sharpe, MDD, total return, trade count</td></tr>
    <tr><td>5b</td><td>Training episode — <code>run_episode(model, train_df)</code></td><td>Train-phase Sharpe, MDD, return (for overfitting comparison)</td></tr>
    <tr><td>6</td><td>Collect episode metrics from <code>TrainingProgressCallback.records</code></td><td>List of <code>{episode, timestep, reward, loss}</code> for training curve chart</td></tr>
    <tr><td>7</td><td>Return <code>TrainingOutcome</code> to WorkflowService</td><td>Stored in <code>training_runs</code> table; model .zip saved to <code>data/output/</code></td></tr>
  </tbody>
</table>

<hr/>

<h2>Data Layer</h2>

<h3>CSV Sources</h3>
<table>
  <thead><tr><th>Directory</th><th>File pattern</th><th>Description</th></tr></thead>
  <tbody>
    <tr><td><code>data/raw/</code></td><td><code>merged.csv</code> per instrument</td><td>Immutable 25-year history. Never written by code.</td></tr>
    <tr><td><code>data/input/DAILY-DATA/</code></td><td><code>nifty_manual.csv</code>, <code>banknifty_manual.csv</code></td><td>Manually appended after each trading day. Extends raw history into 2026.</td></tr>
  </tbody>
</table>

<h3>Loading</h3>
<p><code>load_instrument_data(instrument)</code> in <code>data_loader.py</code>:</p>
<ol>
  <li>Loads <code>data/raw/{instrument}/merged.csv</code> as the primary source.</li>
  <li>If a manual supplement file exists (<code>nifty_manual.csv</code> etc.), it is appended and duplicates are dropped.</li>
  <li>Returns a date-indexed DataFrame sorted chronologically.</li>
</ol>
<p>The backtest dispatcher pre-filters to a 250-row warmup window before calling
<code>calculate_indicators()</code> to avoid computing indicators over the full 4,500+ row history
when only a 1-year backtest window is needed.</p>

<hr/>

<h2>Feature Engineering — <code>calculate_indicators(df)</code></h2>
<p>Adds 17 computed columns to the raw OHLCV DataFrame using the <code>ta</code> library.
All indicators are computed in a single pass; the result DataFrame is used directly
as both training input and inference input.</p>

<table>
  <thead><tr><th>Column</th><th>Indicator</th><th>Window / Parameters</th></tr></thead>
  <tbody>
    <tr><td><code>rsi_14</code></td><td>Relative Strength Index</td><td>14-period</td></tr>
    <tr><td><code>macd</code></td><td>MACD line</td><td>Fast 12, slow 26, signal 9</td></tr>
    <tr><td><code>macd_signal</code></td><td>MACD signal line</td><td>9-period EMA of MACD</td></tr>
    <tr><td><code>macd_hist</code></td><td>MACD histogram</td><td>MACD − signal</td></tr>
    <tr><td><code>bb_upper</code></td><td>Bollinger upper band</td><td>20-period, 2 std devs</td></tr>
    <tr><td><code>bb_mid</code></td><td>Bollinger middle band (SMA-20)</td><td>20-period</td></tr>
    <tr><td><code>bb_lower</code></td><td>Bollinger lower band</td><td>20-period, 2 std devs</td></tr>
    <tr><td><code>bb_pct_b</code></td><td>Bollinger %B</td><td>0 = lower band, 1 = upper band</td></tr>
    <tr><td><code>atr_14</code></td><td>Average True Range</td><td>14-period</td></tr>
    <tr><td><code>ema_5</code></td><td>Exponential Moving Average</td><td>5-day</td></tr>
    <tr><td><code>ema_13</code></td><td>Exponential Moving Average</td><td>13-day</td></tr>
    <tr><td><code>ema_26</code></td><td>Exponential Moving Average</td><td>26-day</td></tr>
    <tr><td><code>ema_50</code></td><td>Exponential Moving Average</td><td>50-day</td></tr>
    <tr><td><code>ema_200</code></td><td>Exponential Moving Average</td><td>200-day</td></tr>
    <tr><td><code>trend_score</code></td><td>Normalised slope of EMA-50</td><td>20-day rolling window, clipped to [−1, +1] — computed via vectorised convolution (one O(N) pass, not N polyfit calls)</td></tr>
    <tr><td><code>ema_ratio</code></td><td>EMA-26 / EMA-50</td><td>Regime signal; clipped to [0.5, 1.5]</td></tr>
    <tr><td><code>daily_return</code></td><td>Daily close-to-close return</td><td><code>(Close − prev_Close) / prev_Close</code></td></tr>
  </tbody>
</table>
<p>The environment uses 8 of these features in its observation vector (9 when <code>ema_ratio</code> is present).
All remaining indicators are available to dashboard JS modules via the market-signals API endpoint.</p>

<hr/>

<h2>Performance Metrics — <code>compute_all_metrics()</code></h2>
<p>Pure-computation module (<code>performance.py</code>) — no DB or file I/O. Called after every
training episode and backtest run. Risk-free rate is set to 7% (India 10Y government bond yield).</p>

<table>
  <thead><tr><th>Metric</th><th>Formula</th><th>Constraint</th></tr></thead>
  <tbody>
    <tr><td><code>sharpe_ratio</code></td><td>(mean daily return − daily risk-free) / std × √252</td><td>Must be &gt; 1.0</td></tr>
    <tr><td><code>max_drawdown_pct</code></td><td>min((val − running_max) / running_max) × 100</td><td>Must be &gt; −10%</td></tr>
    <tr><td><code>portfolio_cagr_pct</code></td><td>(end / start)^(1 / years) − 1</td><td>—</td></tr>
    <tr><td><code>benchmark_cagr_pct</code></td><td>Same formula on Buy &amp; Hold values</td><td>—</td></tr>
    <tr><td><code>portfolio_total_return_pct</code></td><td>(end / start − 1) × 100</td><td>—</td></tr>
    <tr><td><code>annual_volatility_pct</code></td><td>std(daily returns) × √252 × 100</td><td>—</td></tr>
    <tr><td><code>win_rate_pct</code></td><td>days with positive return / total days × 100</td><td>—</td></tr>
    <tr><td><code>sharpe_constraint_met</code></td><td>sharpe &gt; 1.0</td><td>Boolean gate</td></tr>
    <tr><td><code>drawdown_constraint_met</code></td><td>max_drawdown &gt; −10%</td><td>Boolean gate</td></tr>
    <tr><td><code>constraints_met</code></td><td>sharpe_ok AND drawdown_ok</td><td>Overall pass/fail</td></tr>
  </tbody>
</table>

<h3>Portfolio Comparison</h3>
<p><code>build_portfolio_comparison(backtest_df, portfolio_inr)</code> benchmarks the RITA RL model
against three fixed-allocation manual strategies:</p>
<table>
  <thead><tr><th>Profile</th><th>Allocation</th></tr></thead>
  <tbody>
    <tr><td>Conservative</td><td>30% Nifty + 70% Cash</td></tr>
    <tr><td>Moderate</td><td>60% Nifty + 40% Cash</td></tr>
    <tr><td>Aggressive (Buy &amp; Hold)</td><td>100% Nifty</td></tr>
    <tr><td>RITA RL Model</td><td>0 / 50 / 100% dynamic (DDQN decision)</td></tr>
  </tbody>
</table>
<p>Winner is selected by Sharpe ratio (project goal). INR profit/loss is computed for each profile
against a user-supplied starting capital.</p>

<h3>Stress Simulation</h3>
<p><code>simulate_stress_scenarios(portfolio_inr, market_moves, rita_allocation_pct)</code>
shows point-in-time impact of market moves (e.g. −20%, −10%, +10%, +20%) across all profiles.
Flags which profiles breach the 10% drawdown limit and calculates RITA → HOLD (0%) as an always-safe baseline.</p>

<hr/>

<h2>Backtest Dispatch — <code>run_backtest(config)</code></h2>
<p>Triggered by <code>POST /api/v1/backtest</code> via <code>BacktestService</code>.
Evaluates the saved DDQN model over a specific historical date range.</p>

<table>
  <thead><tr><th>Step</th><th>Action</th></tr></thead>
  <tbody>
    <tr><td>1</td><td>Locate model .zip — resolves <code>"latest"</code> to the most recently modified file in <code>data/output/{INSTRUMENT}/</code></td></tr>
    <tr><td>2</td><td>Load raw CSV + compute indicators. Pre-filters with a 250-row warmup before the requested start date to ensure EMA-200 is warm.</td></tr>
    <tr><td>3</td><td>Filter to exact date range. Raises <code>ValueError</code> if &lt; 30 rows result — prevents meaningless backtests on very short windows.</td></tr>
    <tr><td>4</td><td>Load model via <code>load_agent(model_path)</code> and run <code>run_episode(model, filtered_df)</code> deterministically.</td></tr>
    <tr><td>5</td><td>Build <code>BacktestOutcome</code> with per-day <code>DailyResult</code> entries (portfolio value, benchmark value, allocation, close price).</td></tr>
  </tbody>
</table>

<h3>BacktestConfig fields</h3>
<table>
  <thead><tr><th>Field</th><th>Type</th><th>Description</th></tr></thead>
  <tbody>
    <tr><td><code>run_id</code></td><td>str</td><td>Unique ID for this backtest run</td></tr>
    <tr><td><code>start_date</code></td><td>date</td><td>Inclusive start of date range</td></tr>
    <tr><td><code>end_date</code></td><td>date</td><td>Inclusive end of date range</td></tr>
    <tr><td><code>model_version</code></td><td>str</td><td><code>"latest"</code> or a specific model name stem</td></tr>
    <tr><td><code>strategy_params</code></td><td>str | None</td><td>Reserved for future strategy overrides</td></tr>
    <tr><td><code>instrument</code></td><td>str</td><td>Defaults to <code>"NIFTY"</code></td></tr>
  </tbody>
</table>

<hr/>

<h2>Drift Detection — <code>drift_detector.py</code></h2>
<p>Five DB-backed checks run against the latest backtest results to detect when the model
is drifting from its expected behaviour. Surfaced at <code>GET /api/v1/drift</code> and
displayed in the RITA dashboard Observability section.</p>

<table>
  <thead><tr><th>Check</th><th>What it detects</th></tr></thead>
  <tbody>
    <tr><td>Allocation drift</td><td>Model allocation distribution has shifted significantly from the training distribution</td></tr>
    <tr><td>Volatility drift</td><td>Recent market volatility (ATR) is outside the range seen during training</td></tr>
    <tr><td>Drawdown drift</td><td>Current drawdown exceeds the −10% constraint threshold</td></tr>
    <tr><td>Feature drift</td><td>Input feature statistics (RSI, MACD, BB) have shifted from training-time distributions</td></tr>
    <tr><td>Regime drift</td><td>Market regime (Bull / Bear / Neutral) has changed relative to the predominant training regime</td></tr>
  </tbody>
</table>

<hr/>

<h2>TrainingConfig &amp; TrainingOutcome</h2>
<p>The two dataclasses that cross the boundary between <code>WorkflowService</code> and <code>ml_dispatch</code>.</p>

<h3>TrainingConfig</h3>
<table>
  <thead><tr><th>Field</th><th>Type</th><th>Description</th></tr></thead>
  <tbody>
    <tr><td><code>run_id</code></td><td>str</td><td>UUID for this training run — stored in <code>training_runs</code> table</td></tr>
    <tr><td><code>instrument</code></td><td>str</td><td>e.g. <code>"NIFTY"</code></td></tr>
    <tr><td><code>model_version</code></td><td>str</td><td>Stem for the output .zip filename</td></tr>
    <tr><td><code>algorithm</code></td><td>str</td><td><code>"DDQN"</code></td></tr>
    <tr><td><code>timesteps</code></td><td>int</td><td>Total SB3 training steps</td></tr>
    <tr><td><code>learning_rate</code></td><td>float</td><td>DQN learning rate</td></tr>
    <tr><td><code>buffer_size</code></td><td>int</td><td>Replay buffer size</td></tr>
    <tr><td><code>net_arch</code></td><td>str</td><td>Architecture description (e.g. <code>"[256,256]"</code>)</td></tr>
    <tr><td><code>exploration_pct</code></td><td>float</td><td>Fraction of timesteps for epsilon decay</td></tr>
    <tr><td><code>output_dir</code></td><td>str</td><td>Path to save the model .zip</td></tr>
    <tr><td><code>n_seeds</code></td><td>int</td><td>1 = single seed; &gt;1 = <code>train_best_of_n</code></td></tr>
  </tbody>
</table>

<h3>TrainingOutcome</h3>
<table>
  <thead><tr><th>Field</th><th>Description</th></tr></thead>
  <tbody>
    <tr><td><code>model_path</code></td><td>Absolute path to the saved .zip</td></tr>
    <tr><td><code>sharpe</code></td><td>Validation-phase Sharpe ratio</td></tr>
    <tr><td><code>max_drawdown</code></td><td>Validation-phase MDD (fraction)</td></tr>
    <tr><td><code>total_return</code></td><td>Validation-phase total return (fraction)</td></tr>
    <tr><td><code>val_trades</code></td><td>Number of allocation changes in validation episode</td></tr>
    <tr><td><code>train_sharpe / train_mdd / train_return / train_trades</code></td><td>Same metrics from training-phase episode (for overfitting check)</td></tr>
    <tr><td><code>episode_metrics</code></td><td>List of <code>{episode, timestep, reward, loss}</code> — plotted as training curve</td></tr>
    <tr><td><code>seed_results</code></td><td><code>{best_seed, n_seeds_tried, seed_results}</code> — populated when n_seeds &gt; 1</td></tr>
  </tbody>
</table>

<hr/>

<h2>API Endpoints</h2>
<table>
  <thead><tr><th>Endpoint</th><th>Method</th><th>Description</th></tr></thead>
  <tbody>
    <tr><td><code>/api/v1/train</code></td><td>POST (JWT)</td><td>Launch training run — returns run_id immediately; training runs in background thread</td></tr>
    <tr><td><code>/api/v1/backtest</code></td><td>POST (JWT)</td><td>Launch backtest — returns run_id; results polled via training-history</td></tr>
    <tr><td><code>/api/v1/backtest-daily</code></td><td>GET</td><td>Latest backtest daily results (portfolio_value, benchmark_value, allocation per day)</td></tr>
    <tr><td><code>/api/v1/evaluate</code></td><td>POST (JWT)</td><td>Evaluate latest saved model on the full held-out period</td></tr>
    <tr><td><code>/api/v1/training-history</code></td><td>GET</td><td>All training runs, newest-first; includes episode metrics for training curve chart</td></tr>
    <tr><td><code>/api/v1/performance-summary</code></td><td>GET</td><td>Aggregated KPIs from latest backtest (Sharpe, MDD, CAGR, win rate)</td></tr>
    <tr><td><code>/api/v1/drift</code></td><td>GET</td><td>5-check drift detector status</td></tr>
  </tbody>
</table>
"""

# ─────────────────────────────────────────────────────────────────────────────
# PUBLISH
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    client = ConfluenceClient()

    print("=" * 60)
    print("Publishing ML/RL model documentation pages")
    print(f"Parent: Engineering Documentation [{PARENT_ID}]")
    print("=" * 60)

    print("\n[1/2] RL Trading Model")
    page_id, url = client.create_page("RL Trading Model", RL_MODEL_HTML, parent_id=PARENT_ID)
    print(f"  CREATED [{page_id}]")
    print(f"  {url}")

    print("\n[2/2] ML Training Pipeline")
    page_id, url = client.create_page("ML Training Pipeline", ML_PIPELINE_HTML, parent_id=PARENT_ID)
    print(f"  CREATED [{page_id}]")
    print(f"  {url}")

    print("\n" + "=" * 60)
    print("Done. 2 pages published under Engineering Documentation.")
    print("=" * 60)
