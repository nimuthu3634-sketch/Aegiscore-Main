from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = Field(default="development", alias="APP_ENV")
    database_url: str = Field(
        default="postgresql+psycopg://aegiscore:aegiscore_dev_password@postgres:5432/aegiscore",
        alias="DATABASE_URL",
    )
    worker_poll_interval_seconds: int = Field(
        default=15,
        alias="WORKER_POLL_INTERVAL_SECONDS",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()

