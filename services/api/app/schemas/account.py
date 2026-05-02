from decimal import Decimal

from pydantic import BaseModel


class AccountBase(BaseModel):
    client_id: int
    broker_name: str | None = None
    mt5_login: str
    server_name: str
    account_mode: str = "monitor"
    symbol: str = "XAUUSD"
    is_enabled: bool = True
    max_daily_loss_pct: Decimal = Decimal("3.00")
    max_open_trades: int = 1


class AccountCreate(AccountBase):
    pass


class AccountRead(AccountBase):
    id: int

    class Config:
        from_attributes = True
