from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.schemas.account import AccountRead
from app.schemas.bot_config import BotConfigRead

WorkerStatus = Literal["online", "offline", "error", "disabled"]


class WorkerRegisterRequest(BaseModel):
    account_id: int
    machine_name: str | None = None
    version: str | None = None


class WorkerHeartbeatRequest(BaseModel):
    worker_id: int
    status: WorkerStatus = "online"
    last_error: str | None = None


class WorkerStatusUpdate(BaseModel):
    status: WorkerStatus
    is_active: bool | None = None
    last_error: str | None = None


class WorkerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    machine_name: str | None
    version: str | None
    status: str
    is_active: bool
    heartbeat_at: datetime | None
    last_started_at: datetime | None
    last_error: str | None
    last_error_at: datetime | None
    created_at: datetime
    updated_at: datetime


class WorkerRuntimeRead(BaseModel):
    worker: WorkerRead
    account: AccountRead
    config: BotConfigRead
