from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class AccountBase(BaseModel):
    client_id: int = Field(gt=0)
    broker_name: str | None = None
    mt5_login: str
    server_name: str
    account_mode: str = "monitor"
    symbol: str = "XAUUSD"
    is_enabled: bool = True
    max_daily_loss_pct: Decimal = Field(default=Decimal("3.00"), gt=0)
    max_open_trades: int = Field(default=1, ge=1)


class AccountCreate(AccountBase):
    pass


class AccountUpdate(BaseModel):
    client_id: int | None = Field(default=None, gt=0)
    broker_name: str | None = None
    mt5_login: str | None = None
    server_name: str | None = None
    account_mode: str | None = None
    symbol: str | None = None
    is_enabled: bool | None = None
    max_daily_loss_pct: Decimal | None = Field(default=None, gt=0)
    max_open_trades: int | None = Field(default=None, ge=1)


class AccountRead(AccountBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
