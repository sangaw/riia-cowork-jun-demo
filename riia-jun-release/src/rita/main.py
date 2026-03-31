from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from rita.config import get_settings
from rita.exception_handlers import (
    http_exception_handler,
    repository_validation_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from rita.middleware import TraceIDMiddleware
from rita.repositories.base import RepositoryValidationError
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
app = FastAPI(title=settings.app.name, version=settings.app.version)

# ── Middleware ────────────────────────────────────────────────────────────────
app.add_middleware(TraceIDMiddleware)

# ── Exception handlers (most-specific first) ─────────────────────────────────
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(RepositoryValidationError, repository_validation_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# ── System tier — pure CRUD routers (one per CSV table) ──────────────────────
app.include_router(positions_router)
app.include_router(orders_router)
app.include_router(snapshots_router)
app.include_router(trades_router)
app.include_router(alerts_router)
app.include_router(audit_router)
app.include_router(market_data_router)
app.include_router(config_overrides_router)

# ── Workflow tier — business process routers (job submission + status) ────────
app.include_router(train_router)
app.include_router(backtest_router)
app.include_router(evaluate_router)

# ── Experience Layer — UI-shaped aggregation routers (read-only) ──────────────
app.include_router(dashboard_router)
app.include_router(fno_router)
app.include_router(ops_router)


@app.get("/health")
def health():
    return {"status": "ok", "version": settings.app.version}
