"""BacktestService — backtest and evaluate job tracking.

ADR-001: Workflow routers call services only.
ADR-002: All data access via repository classes.

Sprint 2: Creates job records with status=pending and persists them.
Sprint 3: Plugs in actual backtest/evaluate execution logic.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from rita.repositories.backtest import BacktestResultsRepository, BacktestRunsRepository
from rita.schemas.backtest import BacktestResult, BacktestRun, BacktestRunCreate


class BacktestService:
    def __init__(self, db: Session) -> None:
        self._runs = BacktestRunsRepository(db)
        self._results = BacktestResultsRepository(db)

    # ── Backtest jobs ─────────────────────────────────────────────────────────

    def start_backtest(self, body: BacktestRunCreate) -> BacktestRun:
        """Create a backtest run record with status=pending.

        Actual execution is implemented in Sprint 3.
        """
        return self._create_run(body, triggered_by=body.triggered_by or "api")

    def start_evaluation(self, body: BacktestRunCreate) -> BacktestRun:
        """Create an evaluation run record with status=pending.

        Evaluation reuses the BacktestRun schema; distinguished by triggered_by='evaluate'.
        Actual execution is implemented in Sprint 3.
        """
        return self._create_run(body, triggered_by="evaluate")

    def get_run(self, run_id: str) -> BacktestRun | None:
        return self._runs.find_by_id(run_id)

    def list_runs(self) -> list[BacktestRun]:
        return [r for r in self._runs.read_all() if r.triggered_by != "evaluate"]

    def list_evaluations(self) -> list[BacktestRun]:
        return [r for r in self._runs.read_all() if r.triggered_by == "evaluate"]

    def list_results(self, run_id: str) -> list[BacktestResult]:
        return [r for r in self._results.read_all() if r.run_id == run_id]

    # ── Internal ──────────────────────────────────────────────────────────────

    def _create_run(self, body: BacktestRunCreate, triggered_by: str) -> BacktestRun:
        now = datetime.now(timezone.utc)
        run = BacktestRun(
            **{**body.model_dump(), "triggered_by": triggered_by},
            run_id=str(uuid.uuid4()),
            status="pending",
            started_at=None,
            ended_at=None,
            recorded_at=now,
        )
        return self._runs.upsert(run)
