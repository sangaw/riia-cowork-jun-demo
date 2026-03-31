from fastapi import FastAPI
from rita.config import get_settings
from rita.api.v1.system.positions import router as positions_router
from rita.api.v1.system.orders import router as orders_router
from rita.api.v1.system.snapshots import router as snapshots_router
from rita.api.v1.system.trades import router as trades_router
from rita.api.v1.system.alerts import router as alerts_router
from rita.api.v1.system.audit import router as audit_router
from rita.api.v1.system.market_data import router as market_data_router
from rita.api.v1.system.config_overrides import router as config_overrides_router

settings = get_settings()
app = FastAPI(title=settings.app.name, version=settings.app.version)

# System tier — pure CRUD routers (one per CSV table)
app.include_router(positions_router)
app.include_router(orders_router)
app.include_router(snapshots_router)
app.include_router(trades_router)
app.include_router(alerts_router)
app.include_router(audit_router)
app.include_router(market_data_router)
app.include_router(config_overrides_router)


@app.get("/health")
def health():
    return {"status": "ok", "version": settings.app.version}
