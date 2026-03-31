"""Experience Layer — Ops view aggregation router.

ADR-001: Tier 3 (Experience Layer). Read-only composition. No writes, no side effects.
Composes: training run history + backtest run history + recent audit log.
"""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from rita.repositories.audit import AuditLogRepository
from rita.schemas.audit import AuditLog
from rita.schemas.backtest import BacktestRun
from rita.schemas.training import TrainingRun
from rita.services.backtest_service import BacktestService
from rita.services.workflow_service import WorkflowService

router = APIRouter(prefix="/api/experience/ops", tags=["experience:ops"])


class OpsPayload(BaseModel):
    training_runs: list[TrainingRun]
    backtest_runs: list[BacktestRun]
    recent_audit: list[AuditLog]


def get_workflow_svc() -> WorkflowService:
    return WorkflowService()


def get_backtest_svc() -> BacktestService:
    return BacktestService()


def get_audit_repo() -> AuditLogRepository:
    return AuditLogRepository()


@router.get("/", response_model=OpsPayload)
def get_ops(
    audit_limit: int = Query(default=100, ge=1, le=1000),
    workflow_svc: WorkflowService = Depends(get_workflow_svc),
    backtest_svc: BacktestService = Depends(get_backtest_svc),
    audit_repo: AuditLogRepository = Depends(get_audit_repo),
) -> OpsPayload:
    """Return a single aggregated payload for the Ops dashboard."""
    training_runs = workflow_svc.list_runs()
    backtest_runs = backtest_svc.list_runs()

    audit = audit_repo.read_all()
    recent_audit = sorted(audit, key=lambda e: e.timestamp, reverse=True)[:audit_limit]

    return OpsPayload(
        training_runs=training_runs,
        backtest_runs=backtest_runs,
        recent_audit=recent_audit,
    )
