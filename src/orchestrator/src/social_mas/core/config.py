from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", str_strip_whitespace=True)

    nats_url: str = Field(default="nats://localhost:4222")
    redis_url: str = Field(default="redis://localhost:6379/0")
    jaeger_endpoint: str | None = Field(default=None)
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000, ge=1, le=65535)
    request_timeout_seconds: float = Field(default=8.0, gt=0)
    request_retries: int = Field(default=3, ge=1, le=5)
    jwt_secret: str = Field(default="change-me-in-local-env", min_length=12)
    jwt_algorithm: str = Field(default="HS256")

