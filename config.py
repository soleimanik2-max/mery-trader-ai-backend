from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "MERY TRADER AI"
    app_version: str = "1.0.0"
    environment: str = "production"
    debug: bool = False

    api_key: str | None = None
    api_secret: str | None = None

    trading_enabled: bool = False

    max_risk_per_trade: float = 3.0
    max_combined_open_risk: float = 5.0
    daily_loss_limit: float = 3.0
    max_drawdown: float = 5.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
