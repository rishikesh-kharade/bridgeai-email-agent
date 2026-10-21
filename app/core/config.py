from typing import Literal
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application
    app_name: str = "BridgeAI Email Agent"
    app_version: str = "2.0.0"
    app_port: int = Field(default=8000, ge=1024, le=65535)
    environment: Literal["development", "test", "production"] = "development"
    debug: bool = False

    # Logging
    log_level: str = "INFO"

    # Gemini
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.6-flash"
    gemini_temperature: float = 0.1

    # Provider configuration
    provider_mode: Literal["memory", "gmail"] = "memory"

    # OAuth
    oauth_credentials_path: str = "credentials/credentials.json"
    oauth_token_path: str = "token.json"
    oauth_scopes: list[str] = [
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/tasks",
    ]

    # Timeouts (seconds)
    request_timeout: float = 30.0
    gemini_timeout: float = 60.0
    max_email_body_chars: int = Field(default=30000, ge=1000, le=100000)
    task_provider_mode: Literal["memory", "google_tasks"] = "memory"

    # Limits
    max_email_list_limit: int = Field(default=100, ge=1, le=500)
    default_email_list_limit: int = Field(default=50, ge=1, le=100)

    @model_validator(mode="after")
    def validate_provider_configuration(self):
        if self.environment == "production":
            if self.provider_mode != "gmail":
                raise ValueError("Production requires PROVIDER_MODE=gmail; memory providers are development-only.")
            raise ValueError("Production deployment is disabled until authentication and tenant authorization are implemented.")
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def is_production(self) -> bool:
        return self.environment == "production"

    def is_test(self) -> bool:
        return self.environment == "test"


settings = Settings()
