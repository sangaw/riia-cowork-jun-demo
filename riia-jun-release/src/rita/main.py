from fastapi import FastAPI
from rita.config import get_settings

settings = get_settings()
app = FastAPI(title=settings.app.name, version=settings.app.version)


@app.get("/health")
def health():
    return {"status": "ok", "version": settings.app.version}
