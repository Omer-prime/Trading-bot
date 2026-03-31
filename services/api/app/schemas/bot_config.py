from pydantic import BaseModel


class BotConfigBase(BaseModel):
    account_id: int
    entry_timeframe: str = "M5"
    confirmation_timeframe: str = "H1"
    bias_timeframe: str = "H4"
    risk_per_trade_pct: float = 1.0
    min_rr: float = 2.0
    break_even_enabled: bool = True
    trailing_stop_enabled: bool = False
    trend_only: bool = True
    london_newyork_only: bool = True
    news_filter_enabled: bool = True


class BotConfigCreate(BotConfigBase):
    pass


class BotConfigRead(BotConfigBase):
    id: int

    class Config:
        from_attributes = True
