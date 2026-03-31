from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.bot_config import BotConfig
from app.schemas.bot_config import BotConfigCreate, BotConfigRead

router = APIRouter(prefix="/configs", tags=["configs"])


@router.get("", response_model=list[BotConfigRead])
def list_configs(db: Session = Depends(get_db)):
    return db.query(BotConfig).order_by(BotConfig.id.desc()).all()


@router.post("", response_model=BotConfigRead)
def create_config(payload: BotConfigCreate, db: Session = Depends(get_db)):
    config = BotConfig(**payload.model_dump())
    db.add(config)
    db.commit()
    db.refresh(config)
    return config
