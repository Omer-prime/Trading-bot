from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Auto Gold Bot API"
    environment: str = "development"
    database_url: str = "postgresql+psycopg://postgres:postgres@db:5432/autogoldbot"
    secret_key: str = "change-me"
    jwt_secret: str = "change-me-too"
    worker_shared_secret: str = "worker-secret-change-me"
    worker_heartbeat_timeout_seconds: int = 90

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
