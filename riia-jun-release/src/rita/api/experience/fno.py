"""Experience Layer — FnO view aggregation router.

ADR-001: Tier 3 (Experience Layer). Read-only composition. No writes, no side effects.
Composes: option position snapshots + daily portfolio P&L + recent manoeuvres.

Greeks (delta/gamma/theta/vega) are computed in core/ and will be surfaced here
once Sprint 3 services are in place. For now the snapshots include per-leg P&L.
"""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from rita.repositories.manoeuvres import ManoeuvresRepository
from rita.repositories.portfolio import PortfolioRepository
from rita.repositories.snapshots import SnapshotsRepository
from rita.schemas.manoeuvres import Manoeuvre
from rita.schemas.portfolio import Portfolio
from rita.schemas.snapshots import Snapshot

router = APIRouter(prefix="/api/experience/fno", tags=["experience:fno"])


class FnoPayload(BaseModel):
    snapshots: list[Snapshot]
    portfolio: list[Portfolio]
    recent_manoeuvres: list[Manoeuvre]


def get_snapshots_repo() -> SnapshotsRepository:
    return SnapshotsRepository()


def get_portfolio_repo() -> PortfolioRepository:
    return PortfolioRepository()


def get_manoeuvres_repo() -> ManoeuvresRepository:
    return ManoeuvresRepository()


@router.get("/", response_model=FnoPayload)
def get_fno(
    manoeuvre_limit: int = Query(default=50, ge=1, le=500),
    snapshots_repo: SnapshotsRepository = Depends(get_snapshots_repo),
    portfolio_repo: PortfolioRepository = Depends(get_portfolio_repo),
    manoeuvres_repo: ManoeuvresRepository = Depends(get_manoeuvres_repo),
) -> FnoPayload:
    """Return a single aggregated payload for the FnO portfolio view."""
    snapshots = snapshots_repo.read_all()
    portfolio = portfolio_repo.read_all()

    manoeuvres = manoeuvres_repo.read_all()
    recent_manoeuvres = sorted(manoeuvres, key=lambda m: m.timestamp, reverse=True)[:manoeuvre_limit]

    return FnoPayload(
        snapshots=snapshots,
        portfolio=portfolio,
        recent_manoeuvres=recent_manoeuvres,
    )
