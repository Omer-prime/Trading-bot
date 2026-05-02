from fastapi import Request
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def write_audit_log(
    db: Session,
    *,
    actor_type: str,
    action: str,
    entity_type: str,
    actor_id: int | None = None,
    entity_id: int | None = None,
    account_id: int | None = None,
    payload_json: dict | None = None,
    request: Request | None = None,
) -> AuditLog:
    audit_log = AuditLog(
        actor_type=actor_type,
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        account_id=account_id,
        payload_json=payload_json,
        ip_address=request.client.host if request and request.client else None,
        user_agent=request.headers.get("user-agent") if request else None,
    )
    db.add(audit_log)
    return audit_log
