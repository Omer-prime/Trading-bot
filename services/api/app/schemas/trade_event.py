from datetime import datetime
from pydantic import BaseModel, ConfigDict


class TradeEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    trade_id: int
    event_type: str
    event_message: str | None
    payload_json: dict | None
    created_at: datetime
    updated_at: datetime