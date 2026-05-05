from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.schemas.account import AccountRead
from app.schemas.bot_config import BotConfigRead

WorkerStatus = Literal["online", "offline", "error", "disabled"]
HeartbeatStatus = Literal["fresh", "stale", "missing"]


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


class WorkerRuntimeLifecycleFlags(BaseModel):
    worker_status: WorkerStatus
    is_active: bool
    can_fetch_runtime: bool
    heartbeat_status: HeartbeatStatus
    heartbeat_stale: bool
    heartbeat_timeout_seconds: int


class WorkerRuntimeEnabledFlags(BaseModel):
    worker_enabled: bool
    account_enabled: bool
    bot_config_present: bool


class WorkerRuntimeRead(BaseModel):
    worker: WorkerRead
    account: AccountRead
    bot_config: BotConfigRead
    lifecycle_flags: WorkerRuntimeLifecycleFlags
    enabled_flags: WorkerRuntimeEnabledFlags
