from __future__ import annotations

from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-based settings for the LLM agent."""

    model_config = SettingsConfigDict(extra="ignore", str_strip_whitespace=True)

    agent_name: str = Field(default="llm-insight-agent")
    nats_url: str = Field(default="nats://localhost:4222")
    task_subject: str = Field(default="social.tasks.llm")
    auction_subject: str = Field(default="social.auction.llm")
    llm_provider: Literal["mock", "ollama", "cloud"] = Field(default="mock")
    ollama_url: str = Field(default="http://ollama:11434")
    ollama_model: str = Field(default="llama3.1")
    cloud_llm_api_url: str | None = Field(default=None)
    cloud_llm_api_key: str | None = Field(default=None)
    request_timeout_seconds: float = Field(default=8.0, gt=0)
    health_addr: str = Field(default="0.0.0.0")
    health_port: int = Field(default=8090, ge=1, le=65535)

