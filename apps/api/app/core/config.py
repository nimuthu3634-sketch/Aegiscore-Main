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
    wazuh_username: str | None = Field(default=None, alias="WAZUH_USERNAME")
    wazuh_password: str | None = Field(default=None, alias="WAZUH_PASSWORD")
    wazuh_bearer_token: str | None = Field(default=None, alias="WAZUH_BEARER_TOKEN")
    wazuh_auth_mode: str = Field(default="basic", alias="WAZUH_AUTH_MODE")
    wazuh_auth_endpoint: str = Field(
        default="/security/user/authenticate",
        alias="WAZUH_AUTH_ENDPOINT",
    )
    wazuh_alerts_path: str = Field(default="/alerts", alias="WAZUH_ALERTS_PATH")
    wazuh_connector_enabled: bool = Field(
        default=False,
        alias="WAZUH_CONNECTOR_ENABLED",
    )
    wazuh_poll_interval_seconds: int = Field(
        default=30,
        alias="WAZUH_POLL_INTERVAL_SECONDS",
    )
    wazuh_timeout_seconds: float = Field(default=10.0, alias="WAZUH_TIMEOUT_SECONDS")
    wazuh_retry_attempts: int = Field(default=2, alias="WAZUH_RETRY_ATTEMPTS")
    wazuh_retry_backoff_seconds: float = Field(
        default=1.0,
        alias="WAZUH_RETRY_BACKOFF_SECONDS",
    )
    wazuh_verify_tls: bool = Field(default=True, alias="WAZUH_VERIFY_TLS")
    wazuh_ca_file: str | None = Field(default=None, alias="WAZUH_CA_FILE")
    wazuh_page_size: int = Field(default=200, alias="WAZUH_PAGE_SIZE")
    wazuh_max_pages_per_cycle: int = Field(
        default=5,
        alias="WAZUH_MAX_PAGES_PER_CYCLE",
    )
    wazuh_offset_param: str = Field(default="offset", alias="WAZUH_OFFSET_PARAM")
    wazuh_since_param: str = Field(default="since", alias="WAZUH_SINCE_PARAM")
    wazuh_timestamp_field: str = Field(
        default="timestamp",
        alias="WAZUH_TIMESTAMP_FIELD",
    )
    suricata_source: str = Field(default="suricata", alias="SURICATA_SOURCE")
    suricata_connector_enabled: bool = Field(
        default=False,
        alias="SURICATA_CONNECTOR_ENABLED",
    )
    suricata_connector_mode: str = Field(
        default="file_tail",
        alias="SURICATA_CONNECTOR_MODE",
    )
    suricata_eve_file_path: str = Field(
        default="/var/log/suricata/eve.json",
        alias="SURICATA_EVE_FILE_PATH",
    )
    suricata_poll_interval_seconds: int = Field(
        default=15,
        alias="SURICATA_POLL_INTERVAL_SECONDS",
    )
    suricata_max_events_per_cycle: int = Field(
        default=250,
        alias="SURICATA_MAX_EVENTS_PER_CYCLE",
    )
    suricata_retry_attempts: int = Field(
        default=2,
        alias="SURICATA_RETRY_ATTEMPTS",
    )
    suricata_retry_backoff_seconds: float = Field(
        default=1.0,
        alias="SURICATA_RETRY_BACKOFF_SECONDS",
    )
    suricata_fail_when_source_missing: bool = Field(
        default=True,
        alias="SURICATA_FAIL_WHEN_SOURCE_MISSING",
    )
    ingestion_allow_asset_autocreate: bool = Field(
        default=True,
        alias="INGESTION_ALLOW_ASSET_AUTOCREATE",
    )
    ingestion_default_asset_criticality: str = Field(
        default="medium",
        alias="INGESTION_DEFAULT_ASSET_CRITICALITY",
    )
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
    automated_response_builtin_adapters_enabled: bool = Field(
        default=True,
        alias="AUTOMATED_RESPONSE_BUILTIN_ADAPTERS_ENABLED",
    )
    automated_response_lab_adapters_enabled: bool = Field(
        default=False,
        alias="AUTOMATED_RESPONSE_LAB_ADAPTERS_ENABLED",
    )
    automated_response_block_ip_backend: str = Field(
        default="ledger",
        alias="AUTOMATED_RESPONSE_BLOCK_IP_BACKEND",
    )
    automated_response_disable_user_backend: str = Field(
        default="ledger",
        alias="AUTOMATED_RESPONSE_DISABLE_USER_BACKEND",
    )
    automated_response_ledger_path: str = Field(
        default="/tmp/aegiscore-response-ledger.jsonl",
        alias="AUTOMATED_RESPONSE_LEDGER_PATH",
    )
    automated_response_host_tag_path: str = Field(
        default="/tmp/aegiscore-host-tags.jsonl",
        alias="AUTOMATED_RESPONSE_HOST_TAG_PATH",
    )
    automated_response_enable_host_tag_write: bool = Field(
        default=False,
        alias="AUTOMATED_RESPONSE_ENABLE_HOST_TAG_WRITE",
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
    notifications_enabled: bool = Field(default=False, alias="NOTIFICATIONS_ENABLED")
    notifications_mode: str = Field(default="log", alias="NOTIFICATIONS_MODE")
    notifications_risk_threshold: int = Field(
        default=85,
        alias="NOTIFICATIONS_RISK_THRESHOLD",
    )
    notifications_incident_states: str = Field(
        default="triaged,investigating,contained",
        alias="NOTIFICATIONS_INCIDENT_STATES",
    )
    notifications_response_statuses: str = Field(
        default="warning,failed",
        alias="NOTIFICATIONS_RESPONSE_STATUSES",
    )
    notifications_response_action_types: str = Field(
        default="*",
        alias="NOTIFICATIONS_RESPONSE_ACTION_TYPES",
    )
    notifications_admin_recipients: str = Field(
        default="admin@aegiscore.local",
        alias="NOTIFICATIONS_ADMIN_RECIPIENTS",
    )
    notifications_sender: str = Field(
        default="aegiscore@localhost",
        alias="NOTIFICATIONS_SENDER",
    )
    smtp_host: str = Field(default="localhost", alias="SMTP_HOST")
    smtp_port: int = Field(default=1025, alias="SMTP_PORT")
    smtp_username: str | None = Field(default=None, alias="SMTP_USERNAME")
    smtp_password: str | None = Field(default=None, alias="SMTP_PASSWORD")
    smtp_use_tls: bool = Field(default=False, alias="SMTP_USE_TLS")
    smtp_use_starttls: bool = Field(default=False, alias="SMTP_USE_STARTTLS")
    smtp_timeout_seconds: float = Field(default=10.0, alias="SMTP_TIMEOUT_SECONDS")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
