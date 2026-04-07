from __future__ import annotations

from contextlib import asynccontextmanager

import structlog
from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text
from starlette.exceptions import HTTPException as StarletteHTTPException

import rita.models  # noqa: F401 -- registers all ORM models with Base.metadata
from rita.auth import get_current_user
from rita.config import get_settings
from rita.limiter import limiter
from rita.database import Base, engine
from rita.exception_handlers import (
    http_exception_handler,
    repository_validation_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from rita.logging_config import configure_logging
from rita.metrics import instrument_app
from rita.middleware import TraceIDMiddleware
from rita.repositories.base import RepositoryValidationError
from rita.api.v1.auth import router as auth_router
from rita.api.v1.system.positions import router as positions_router
from rita.api.v1.system.orders import router as orders_router
from rita.api.v1.system.snapshots import router as snapshots_router
from rita.api.v1.system.trades import router as trades_router
from rita.api.v1.system.alerts import router as alerts_router
from rita.api.v1.system.audit import router as audit_router
from rita.api.v1.system.market_data import router as market_data_router
from rita.api.v1.system.config_overrides import router as config_overrides_router
from rita.api.v1.workflow.train import router as train_router
from rita.api.v1.workflow.backtest import router as backtest_router
from rita.api.v1.workflow.evaluate import router as evaluate_router
from rita.api.experience.dashboard import router as dashboard_router
from rita.api.experience.fno import router as fno_router
from rita.api.experience.ops import router as ops_router

settings = get_settings()
log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    log.info("app.startup", name=settings.app.name, version=settings.app.version)
    Base.metadata.create_all(bind=engine)
    yield
    log.info("app.shutdown")


app = FastAPI(title=settings.app.name, version=settings.app.version, lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# -- Middleware (registration order: last-added executes outermost/first) ------
app.add_middleware(TraceIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.security.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -- Exception handlers (most-specific first) ---------------------------------
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(RepositoryValidationError, repository_validation_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# -- Auth router (no auth required on /auth/token itself) ---------------------
app.include_router(auth_router)

# -- System tier -- pure CRUD routers (one per table) -------------------------
app.include_router(positions_router)
app.include_router(orders_router)
app.include_router(snapshots_router)
app.include_router(trades_router)
app.include_router(alerts_router)
app.include_router(audit_router)
app.include_router(market_data_router)
app.include_router(config_overrides_router)

# -- Workflow tier -- JWT-protected business process routers ------------------
app.include_router(train_router, dependencies=[Depends(get_current_user)])
app.include_router(backtest_router, dependencies=[Depends(get_current_user)])
app.include_router(evaluate_router, dependencies=[Depends(get_current_user)])

# -- Experience Layer -- UI-shaped aggregation routers (read-only) -------------
app.include_router(dashboard_router)
app.include_router(fno_router)
app.include_router(ops_router)

# -- Prometheus metrics (must come after all routers are registered) -----------
instrument_app(app)

# -- Static files: dashboard UI (must be last — catch-all) --------------------
_dashboard_dir = Path(__file__).parent.parent.parent / "dashboard"
if _dashboard_dir.exists():
    app.mount("/dashboard", StaticFiles(directory=_dashboard_dir, html=True), name="dashboard")


@app.get("/health", tags=["observability"])
def health() -> dict:
    """Liveness probe.

    Returns HTTP 200 as long as the process is running.  No data-layer check
    is performed — liveness must not fail due to storage issues.
    """
    return {"status": "ok", "version": settings.app.version}


@app.get("/readyz", tags=["observability"])
def readyz() -> JSONResponse:
    """Readiness probe.

    Checks DB connectivity via SELECT 1.  Returns HTTP 200 when the database
    is reachable, HTTP 503 otherwise.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001
        log.warning("readyz_check_failed", error=str(exc))
        return JSONResponse(
            status_code=503,
            content={"status": "unavailable", "detail": str(exc)},
        )
    return JSONResponse(status_code=200, content={"status": "ready"})
