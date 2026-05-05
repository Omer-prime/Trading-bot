from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict

SignalStatus = Literal["accepted", "rejected"]


class DryRunSignalCreate(BaseModel):
    account_id: int
    worker_id: int | None = None
    symbol: str
    timeframe: str
    timeframes_json: list[str] | None = None
    direction: str
    trend_bias: str | None = None
    liquidity_sweep_detected: bool = False
    bos_detected: bool = False
    entry_price: Decimal | None = None
    stop_loss: Decimal | None = None
    take_profit: Decimal | None = None
    rr_estimate: Decimal | None = None
    status: SignalStatus
    rejection_reason: str | None = None
    payload_json: dict | None = None


class SignalLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    worker_id: int | None
    symbol: str
    timeframe: str
    timeframes_json: list[str] | None
    direction: str
    trend_bias: str | None
    liquidity_sweep_detected: bool
    bos_detected: bool
    entry_price: Decimal | None
    stop_loss: Decimal | None
    take_profit: Decimal | None
    rr_estimate: Decimal | None
    status: str
    rejection_reason: str | None
    payload_json: dict | None
    created_at: datetime
    updated_at: datetime
