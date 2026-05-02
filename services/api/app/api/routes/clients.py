from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.core.database import get_db
from app.models.client import Client
from app.models.user import User
from app.schemas.client import ClientCreate, ClientRead, ClientUpdate
from app.services.audit import write_audit_log

router = APIRouter(
    prefix="/clients",
    tags=["clients"],
    dependencies=[Depends(require_admin)],
)


@router.get("", response_model=list[ClientRead])
def list_clients(db: Session = Depends(get_db)):
    return db.query(Client).order_by(Client.id.desc()).all()


@router.get("/{client_id}", response_model=ClientRead)
def get_client(client_id: int, db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )
    return client


@router.post("", response_model=ClientRead, status_code=status.HTTP_201_CREATED)
def create_client(
    payload: ClientCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    client = Client(**payload.model_dump())

    try:
        db.add(client)
        db.flush()
        write_audit_log(
            db,
            actor_type="user",
            actor_id=current_user.id,
            action="client.created",
            entity_type="client",
            entity_id=client.id,
            payload_json=payload.model_dump(),
            request=request,
        )
        db.commit()
        db.refresh(client)
        return client
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to create client",
        )


@router.patch("/{client_id}", response_model=ClientRead)
def update_client(
    client_id: int,
    payload: ClientUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )

    changes = payload.model_dump(exclude_unset=True)
    for key, value in changes.items():
        setattr(client, key, value)

    try:
        write_audit_log(
            db,
            actor_type="user",
            actor_id=current_user.id,
            action="client.updated",
            entity_type="client",
            entity_id=client.id,
            payload_json=changes,
            request=request,
        )
        db.commit()
        db.refresh(client)
        return client
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to update client",
        )
