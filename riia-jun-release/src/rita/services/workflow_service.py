"""WorkflowService — DQN training job tracking and dispatch.

ADR-001: Workflow routers call services only.
ADR-002: All data access via repository classes.

Sprint 2: Creates job records with status=pending and persists them.
Sprint 3: Plugs in actual ML dispatch (stable-baselines3 DoubleDQN) via a
          daemon thread so the API returns immediately with status=pending.
"""

from __future__ import annotations

import threading
import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy.orm import Session

from rita.core.ml_dispatch import TrainingConfig, train
from rita.database import SessionLocal
from rita.repositories.training import TrainingMetricsRepository, TrainingRunsRepository
from rita.schemas.training import TrainingMetric, TrainingRun, TrainingRunCreate

log = structlog.get_logger()


# ---------------------------------------------------------------------------
# Module-level background worker
# ---------------------------------------------------------------------------


def _run_training_job(config: TrainingConfig) -> None:
    """Background thread: run training and persist all results."""
    db = SessionLocal()
    try:
        runs_repo = TrainingRunsRepository(db)
        metrics_repo = TrainingMetricsRepository(db)

        run = runs_repo.find_by_id(config.run_id)
        if run is None:
            return

        run = TrainingRun(
            **{**run.model_dump(), "status": "running", "started_at": datetime.now(timezone.utc)}
        )
        runs_repo.upsert(run)
        log.info("training.running", run_id=config.run_id)

        try:
            outcome = train(config)
        except Exception:
            log.error("training.failed", run_id=config.run_id, exc_info=True)
            run = runs_repo.find_by_id(config.run_id)
            if run is not None:
                runs_repo.upsert(
                    TrainingRun(
                        **{**run.model_dump(), "status": "failed", "ended_at": datetime.now(timezone.utc)}
                    )
                )
            return

        ended_at = datetime.now(timezone.utc)
        run = runs_repo.find_by_id(config.run_id)
        if run is None:
            return

        runs_repo.upsert(
            TrainingRun(
                **{
                    **run.model_dump(),
                    "status": "complete",
                    "ended_at": ended_at,
                    "model_path": outcome.model_path,
                    "backtest_sharpe": outcome.sharpe,
                    "backtest_mdd": outcome.max_drawdown,
                    "backtest_return": outcome.total_return,
                }
            )
        )
        log.info("training.complete", run_id=config.run_id, model_path=outcome.model_path)

        for ep in outcome.episode_metrics:
            metrics_repo.upsert(
                TrainingMetric(
                    metric_id=str(uuid.uuid4()),
                    run_id=config.run_id,
                    episode=ep["episode"],
                    reward=ep["reward"],
                    loss=ep["loss"],
                    epsilon=ep["epsilon"],
                    portfolio_value=ep["portfolio_value"],
                    recorded_at=ended_at,
                )
            )
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Service class
# ---------------------------------------------------------------------------


class WorkflowService:
    def __init__(self, db: Session) -> None:
        self._runs = TrainingRunsRepository(db)
        self._metrics = TrainingMetricsRepository(db)

    def start_training(self, body: TrainingRunCreate) -> TrainingRun:
        """Create a training run record with status=pending and dispatch."""
        now = datetime.now(timezone.utc)
        run_id = str(uuid.uuid4())
        run = TrainingRun(
            **body.model_dump(),
            run_id=run_id,
            status="pending",
            started_at=None,
            ended_at=None,
            recorded_at=now,
        )
        self._runs.upsert(run)
        log.info("training.submitted", run_id=run_id)

        settings = body.model_dump()
        config = TrainingConfig(
            run_id=run_id,
            model_version=settings["model_version"],
            algorithm=settings.get("algorithm", "DoubleDQN"),
            timesteps=settings["timesteps"],
            learning_rate=settings["learning_rate"],
            buffer_size=settings["buffer_size"],
            net_arch=settings["net_arch"],
            exploration_pct=settings["exploration_pct"],
            output_dir="rita_output/models",
        )
        threading.Thread(target=_run_training_job, args=(config,), daemon=True).start()
        return run

    def get_run(self, run_id: str) -> TrainingRun | None:
        return self._runs.find_by_id(run_id)

    def list_runs(self) -> list[TrainingRun]:
        return self._runs.read_all()

    def list_metrics(self, run_id: str) -> list[TrainingMetric]:
        return [m for m in self._metrics.read_all() if m.run_id == run_id]
