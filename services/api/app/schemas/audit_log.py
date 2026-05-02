from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    actor_type: str
    actor_id: int | None
    action: str
    entity_type: str
    entity_id: int | None
    account_id: int | None
    payload_json: dict | None
    ip_address: str | None
    user_agent: str | None
    created_at: datetime
    updated_at: datetime