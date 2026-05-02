from fastapi import FastAPI

import app.models  # noqa: F401

from app.api.routes.health import router as health_router
from app.api.routes.auth import router as auth_router
from app.api.routes.clients import router as clients_router
from app.api.routes.accounts import router as accounts_router
from app.api.routes.configs import router as configs_router
from app.api.routes.workers import router as workers_router
from app.api.routes.trades import router as trades_router
from app.api.routes.audit_logs import router as audit_logs_router

app = FastAPI(title="Auto Gold Bot API", version="0.1.0")

app.include_router(health_router)
app.include_router(auth_router, prefix="/api/v1")
app.include_router(clients_router, prefix="/api/v1")
app.include_router(accounts_router, prefix="/api/v1")
app.include_router(configs_router, prefix="/api/v1")
app.include_router(workers_router, prefix="/api/v1")
app.include_router(trades_router, prefix="/api/v1")
app.include_router(audit_logs_router, prefix="/api/v1")


@app.get("/")
def root():
    return {
        "message": "Auto Gold Bot API running",
        "docs": "/docs",
        "version": "0.1.0",
    }