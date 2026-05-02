from pydantic import BaseModel, ConfigDict, Field


class BotConfigBase(BaseModel):
    account_id: int = Field(gt=0)
    entry_timeframe: str = "M5"
    confirmation_timeframe: str = "H1"
    bias_timeframe: str = "H4"
    risk_per_trade_pct: float = Field(default=1.0, gt=0)
    min_rr: float = Field(default=2.0, gt=0)
    break_even_enabled: bool = True
    trailing_stop_enabled: bool = False
    trend_only: bool = True
    london_newyork_only: bool = True
    news_filter_enabled: bool = True


class BotConfigCreate(BotConfigBase):
    pass


class BotConfigUpdate(BaseModel):
    entry_timeframe: str | None = None
    confirmation_timeframe: str | None = None
    bias_timeframe: str | None = None
    risk_per_trade_pct: float | None = Field(default=None, gt=0)
    min_rr: float | None = Field(default=None, gt=0)
    break_even_enabled: bool | None = None
    trailing_stop_enabled: bool | None = None
    trend_only: bool | None = None
    london_newyork_only: bool | None = None
    news_filter_enabled: bool | None = None


class BotConfigRead(BotConfigBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
