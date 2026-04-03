"""WorkflowService — DQN training job tracking.

ADR-001: Workflow routers call services only.
ADR-002: All data access via repository classes.

Sprint 2: Creates job records with status=pending and persists them.
Sprint 3: Plugs in actual ML dispatch (stable-baselines3 DoubleDQN).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from rita.repositories.training import TrainingMetricsRepository, TrainingRunsRepository
from rita.schemas.training import TrainingMetric, TrainingRun, TrainingRunCreate


class WorkflowService:
    def __init__(self, db: Session) -> None:
        self._runs = TrainingRunsRepository(db)
        self._metrics = TrainingMetricsRepository(db)

    # ── Training jobs ─────────────────────────────────────────────────────────

    def start_training(self, body: TrainingRunCreate) -> TrainingRun:
        """Create a training run record with status=pending.

        Actual ML dispatch is implemented in Sprint 3.
        """
        now = datetime.now(timezone.utc)
        run = TrainingRun(
            **body.model_dump(),
            run_id=str(uuid.uuid4()),
            status="pending",
            started_at=None,
            ended_at=None,
            recorded_at=now,
        )
        return self._runs.upsert(run)

    def get_run(self, run_id: str) -> TrainingRun | None:
        return self._runs.find_by_id(run_id)

    def list_runs(self) -> list[TrainingRun]:
        return self._runs.read_all()

    def list_metrics(self, run_id: str) -> list[TrainingMetric]:
        return [m for m in self._metrics.read_all() if m.run_id == run_id]
