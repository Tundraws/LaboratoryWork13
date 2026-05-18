from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class AgentTask(BaseModel):
    """Task received from the orchestrator."""

    model_config = ConfigDict(str_strip_whitespace=True)

    id: str
    type: Literal["llm"]
    trace_id: str
    payload: dict[str, Any]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AgentResult(BaseModel):
    """Result returned to the orchestrator."""

    task_id: str
    agent: str
    role: Literal["llm"]
    trace_id: str
    success: bool
    output: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    duration: str


class BidRequest(BaseModel):
    task_type: Literal["llm"]
    payload: dict[str, Any]


class BidResponse(BaseModel):
    agent: str
    role: Literal["llm"] = "llm"
    cost: int = Field(ge=1)
    available: bool
    reason: str

