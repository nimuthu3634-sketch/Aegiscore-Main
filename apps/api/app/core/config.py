from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AegisCore API"
    app_env: str = Field(default="development", alias="APP_ENV")
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    database_url: str = Field(
        default="postgresql+psycopg://aegiscore:aegiscore_dev_password@postgres:5432/aegiscore",
        alias="DATABASE_URL",
    )
    jwt_secret_key: str = Field(
        default="replace-with-a-development-secret",
        alias="JWT_SECRET_KEY",
    )
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=60,
        alias="ACCESS_TOKEN_EXPIRE_MINUTES",
    )
    wazuh_base_url: str = Field(
        default="http://wazuh-manager:55000",
        alias="WAZUH_BASE_URL",
    )
    suricata_source: str = Field(default="suricata", alias="SURICATA_SOURCE")
    dev_seed_admin_username: str = Field(
        default="admin",
        alias="DEV_SEED_ADMIN_USERNAME",
    )
    dev_seed_admin_password: str = Field(
        default="AegisCore123!",
        alias="DEV_SEED_ADMIN_PASSWORD",
    )
    dev_seed_analyst_username: str = Field(
        default="analyst",
        alias="DEV_SEED_ANALYST_USERNAME",
    )
    dev_seed_analyst_password: str = Field(
        default="AegisCore123!",
        alias="DEV_SEED_ANALYST_PASSWORD",
    )
    scoring_strategy: str = Field(default="baseline", alias="SCORING_STRATEGY")
    scoring_baseline_version: str = Field(
        default="baseline_v1",
        alias="SCORING_BASELINE_VERSION",
    )
    scoring_model_path: str = Field(
        default="/srv/ai/models/aegiscore-risk-priority-model.joblib",
        alias="SCORING_MODEL_PATH",
    )
    scoring_model_metadata_path: str = Field(
        default="/srv/ai/models/aegiscore-risk-priority-model.metadata.json",
        alias="SCORING_MODEL_METADATA_PATH",
    )
    scoring_model_version: str = Field(
        default="untrained",
        alias="SCORING_MODEL_VERSION",
    )
    automated_response_allow_destructive: bool = Field(
        default=False,
        alias="AUTOMATED_RESPONSE_ALLOW_DESTRUCTIVE",
    )
    automated_response_max_retries: int = Field(
        default=1,
        alias="AUTOMATED_RESPONSE_MAX_RETRIES",
    )
    response_adapter_block_ip_script: str | None = Field(
        default=None,
        alias="RESPONSE_ADAPTER_BLOCK_IP_SCRIPT",
    )
    response_adapter_disable_user_script: str | None = Field(
        default=None,
        alias="RESPONSE_ADAPTER_DISABLE_USER_SCRIPT",
    )
    response_adapter_quarantine_host_flag_script: str | None = Field(
        default=None,
        alias="RESPONSE_ADAPTER_QUARANTINE_HOST_FLAG_SCRIPT",
    )
    response_adapter_create_manual_review_script: str | None = Field(
        default=None,
        alias="RESPONSE_ADAPTER_CREATE_MANUAL_REVIEW_SCRIPT",
    )
    response_adapter_notify_admin_script: str | None = Field(
        default=None,
        alias="RESPONSE_ADAPTER_NOTIFY_ADMIN_SCRIPT",
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
