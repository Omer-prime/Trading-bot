from pydantic import BaseModel


class TradingAccountBase(BaseModel):
    client_id: int
    broker_name: str | None = None
    mt5_login: str
    server_name: str
    account_mode: str = "monitor"
    symbol: str = "XAUUSD"
    is_enabled: bool = True
    max_daily_loss_pct: float = 3.0
    max_open_trades: int = 1


class TradingAccountCreate(TradingAccountBase):
    pass


class TradingAccountRead(TradingAccountBase):
    id: int

    class Config:
        from_attributes = True
