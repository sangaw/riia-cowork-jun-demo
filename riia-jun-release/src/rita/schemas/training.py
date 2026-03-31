"""Pydantic schemas for training_runs and training_metrics tables."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


# ── Training Runs ─────────────────────────────────────────────────────────────

class TrainingRunBase(BaseModel):
    model_version: str                      # e.g. v1.0, v1.1
    algorithm: str = "DoubleDQN"
    timesteps: int                          # e.g. 200000
    learning_rate: float                    # e.g. 1e-4
    buffer_size: int                        # e.g. 50000
    net_arch: str                           # e.g. [128, 128]
    exploration_pct: float                  # e.g. 0.1
    notes: Optional[str] = None


class TrainingRunCreate(TrainingRunBase):
    pass


class TrainingRun(TrainingRunBase):
    model_config = ConfigDict(from_attributes=True)

    run_id: str
    status: str = "pending"                 # pending / running / complete / failed
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    backtest_sharpe: Optional[float] = None
    backtest_mdd: Optional[float] = None
    backtest_return: Optional[float] = None
    model_path: Optional[str] = None        # path to .zip model file
    recorded_at: datetime


# ── Training Metrics (per episode) ───────────────────────────────────────────

class TrainingMetricBase(BaseModel):
    run_id: str
    episode: int
    reward: float
    loss: Optional[float] = None
    epsilon: float                          # exploration rate
    portfolio_value: Optional[float] = None


class TrainingMetricCreate(TrainingMetricBase):
    pass


class TrainingMetric(TrainingMetricBase):
    model_config = ConfigDict(from_attributes=True)

    metric_id: str
    recorded_at: datetime
