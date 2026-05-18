from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


AgentRole = Literal["collector", "sentiment", "trends", "llm", "reports"]


class AnalyzeRequest(BaseModel):
    """Incoming request for a full social media analysis pipeline."""

    model_config = ConfigDict(str_strip_whitespace=True)

    query: str = Field(min_length=2, max_length=120)
    limit: int = Field(default=5, ge=1, le=50)
    networks: list[str] = Field(default_factory=lambda: ["telegram", "vk"])


class AgentTask(BaseModel):
    """Task sent by the orchestrator to a concrete agent."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    type: AgentRole
    trace_id: str
    payload: dict[str, Any]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AgentResult(BaseModel):
    """Response returned from a Go agent."""

    task_id: str
    agent: str
    role: AgentRole
    trace_id: str
    success: bool
    output: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    duration: str


class BidRequest(BaseModel):
    task_type: AgentRole
    payload: dict[str, Any]


class BidResponse(BaseModel):
    agent: str
    role: AgentRole
    cost: int = Field(ge=1)
    available: bool
    reason: str


class PipelineStep(BaseModel):
    role: AgentRole
    task_id: str
    selected_agent: str | None = None
    duration: str | None = None
    success: bool
    output: dict[str, Any] = Field(default_factory=dict)


class AnalyzeResponse(BaseModel):
    trace_id: str
    query: str
    steps: list[PipelineStep]
    report: dict[str, Any]
