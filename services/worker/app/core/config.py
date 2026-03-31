from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    api_base_url: str = "http://localhost:8000"
    worker_shared_secret: str = "worker-secret-change-me"
    account_id: int = 1
    symbol: str = "XAUUSD"
    entry_timeframe: str = "M5"
    confirmation_timeframe: str = "H1"
    bias_timeframe: str = "H4"
    max_spread_points: int = 60
    environment: str = "development"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
