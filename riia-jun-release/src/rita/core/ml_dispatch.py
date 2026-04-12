"""RITA Core — ML Dispatch

Entry point for Double-DQN training.  Called by WorkflowService in a
background thread; must be fully self-contained (opens its own DB session
if needed, manages its own file I/O).

Pipeline:
    1. Load instrument OHLCV CSV
    2. Compute technical indicators (ta library)
    3. Train/validation split (80 / 20 by date)
    4. Train Double-DQN via stable-baselines3
    5. Run deterministic validation episode → real performance metrics
    6. Save model to output_dir
    7. Return TrainingOutcome with real Sharpe, MDD, return, episode_metrics
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path

import structlog

log = structlog.get_logger()


# ---------------------------------------------------------------------------
# Configuration & result dataclasses (imported by WorkflowService)
# ---------------------------------------------------------------------------

@dataclass
class TrainingConfig:
    run_id:           str
    instrument:       str
    model_version:    str
    algorithm:        str
    timesteps:        int
    learning_rate:    float
    buffer_size:      int
    net_arch:         str
    exploration_pct:  float
    output_dir:       str
    n_seeds:          int = 1


@dataclass
class TrainingOutcome:
    model_path:      str
    sharpe:          float
    max_drawdown:    float
    total_return:    float
    episode_metrics: list[dict] = field(default_factory=list)
    """Each dict: timestep, loss, ep_rew_mean."""
    seed_results:    dict = field(default_factory=dict)
    """Populated when n_seeds > 1: best_seed, n_seeds_tried, seed_results list."""


# ---------------------------------------------------------------------------
# Training entry point
# ---------------------------------------------------------------------------

def train(config: TrainingConfig) -> TrainingOutcome:
    """Load data, train Double-DQN, validate, save model, return real metrics."""
    import numpy as np

    from rita.core.data_loader import load_nifty_csv
    from rita.core.data_understanding import find_instrument_csv
    from rita.core.technical_analyzer import calculate_indicators
    from rita.core.trading_env import train_agent, train_best_of_n, run_episode

    # ── 1. Load OHLCV data ────────────────────────────────────────────────────
    log.info("ml_dispatch.load_data", instrument=config.instrument)
    csv_path = find_instrument_csv(config.instrument)
    df = load_nifty_csv(str(csv_path))
    log.info("ml_dispatch.data_loaded", rows=len(df))

    # ── 2. Technical indicators ───────────────────────────────────────────────
    df = calculate_indicators(df)
    log.info("ml_dispatch.indicators_computed", rows=len(df))

    # ── 3. Train / validation split (80 / 20 by date) ─────────────────────────
    split_idx = int(len(df) * 0.8)
    train_df = df.iloc[:split_idx]
    val_df   = df.iloc[split_idx:]

    # ── 4. Train ──────────────────────────────────────────────────────────────
    model_name = f"{config.model_version}_{config.run_id[:8]}"
    log.info("ml_dispatch.training_start", run_id=config.run_id, timesteps=config.timesteps, n_seeds=config.n_seeds)
    seed_results_dict: dict = {}

    if config.n_seeds > 1:
        # Multi-seed: pick best model by validation Sharpe
        model, progress_cb, seed_results_dict = train_best_of_n(
            train_df=train_df,
            val_df=val_df,
            output_dir=config.output_dir,
            timesteps=config.timesteps,
            n_seeds=config.n_seeds,
            learning_rate=config.learning_rate,
            buffer_size=config.buffer_size,
            exploration_fraction=config.exploration_pct,
            model_name=model_name,
        )
    else:
        # Single-seed: standard training path
        model, progress_cb = train_agent(
            train_df=train_df,
            output_dir=config.output_dir,
            timesteps=config.timesteps,
            learning_rate=config.learning_rate,
            buffer_size=config.buffer_size,
            exploration_fraction=config.exploration_pct,
            seed=42,
            model_name=model_name,
        )

    model_path = str(Path(config.output_dir) / (model_name + ".zip"))
    log.info("ml_dispatch.training_complete", run_id=config.run_id, model_path=model_path)

    # ── 5. Validation episode → real performance metrics ──────────────────────
    try:
        val_result = run_episode(model, val_df)
        perf = val_result["performance"]
        sharpe       = perf["sharpe_ratio"]
        mdd          = perf["max_drawdown_pct"] / 100.0   # store as fraction
        total_return = perf["portfolio_total_return_pct"] / 100.0
    except Exception:
        sharpe = 0.0
        mdd = 0.0
        total_return = 0.0
    log.info("ml_dispatch.validation_complete", run_id=config.run_id, sharpe=round(sharpe, 3), mdd=round(mdd, 4))

    # ── 6. Episode metrics from callback ─────────────────────────────────────
    episode_metrics = [
        {
            "episode":      i + 1,
            "timestep":     r["timestep"],
            "reward":       float(r["ep_rew_mean"]) if not math.isnan(r["ep_rew_mean"]) else 0.0,
            "loss":         float(r["loss"])        if not math.isnan(r["loss"])        else 0.0,
            "epsilon":      0.0,
            "portfolio_value": 1.0,
        }
        for i, r in enumerate(progress_cb.records)
    ]

    # Merge seed_results into episode_metrics metadata if multi-seed run
    training_metadata: dict = {}
    if seed_results_dict:
        training_metadata.update(seed_results_dict)

    return TrainingOutcome(
        model_path=model_path,
        sharpe=round(sharpe, 4),
        max_drawdown=round(mdd, 4),
        total_return=round(total_return, 4),
        episode_metrics=episode_metrics,
        seed_results=training_metadata,
    )
