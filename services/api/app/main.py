from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.clients import router as clients_router
from app.api.routes.accounts import router as accounts_router
from app.api.routes.configs import router as configs_router

app = FastAPI(title="Auto Gold Bot API", version="0.1.0")

app.include_router(health_router)
app.include_router(clients_router, prefix="/api/v1")
app.include_router(accounts_router, prefix="/api/v1")
app.include_router(configs_router, prefix="/api/v1")


@app.get("/")
def root():
    return {
        "message": "Auto Gold Bot API running",
        "docs": "/docs",
        "version": "0.1.0",
    }