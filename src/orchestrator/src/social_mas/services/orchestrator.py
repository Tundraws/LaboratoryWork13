from __future__ import annotations

import logging
from uuid import uuid4

from social_mas.schemas import (
    AgentResult,
    AgentRole,
    AgentTask,
    AnalyzeRequest,
    AnalyzeResponse,
    BidRequest,
    BidResponse,
    PipelineStep,
)
from social_mas.services.event_log import EventLog
from social_mas.services.nats_gateway import MessageBus


TASK_SUBJECTS: dict[AgentRole, str] = {
    "collector": "social.tasks.collector",
    "sentiment": "social.tasks.sentiment",
    "trends": "social.tasks.trends",
    "llm": "social.tasks.llm",
    "reports": "social.tasks.reports",
}

AUCTION_SUBJECTS: dict[AgentRole, str] = {
    "collector": "social.auction.collector",
    "sentiment": "social.auction.sentiment",
    "trends": "social.auction.trends",
    "llm": "social.auction.llm",
    "reports": "social.auction.reports",
}


class Orchestrator:
    """Coordinates social media analysis across distributed agents."""

    def __init__(
        self,
        bus: MessageBus,
        events: EventLog,
        timeout_seconds: float,
        retries: int,
        logger: logging.Logger | None = None,
    ) -> None:
        self._bus = bus
        self._events = events
        self._timeout_seconds = timeout_seconds
        self._retries = retries
        self._logger = logger or logging.getLogger(__name__)

    async def analyze(self, request: AnalyzeRequest) -> AnalyzeResponse:
        trace_id = str(uuid4())
        self._events.append(trace_id, "orchestrator", "pipeline_started", request.model_dump())

        steps: list[PipelineStep] = []
        payload: dict[str, object] = request.model_dump()
        for role in ("collector", "sentiment", "trends", "llm", "reports"):
            selected = await self._run_auction(role, trace_id, payload)
            result = await self._send_with_retry(role, trace_id, payload)
            step = PipelineStep(
                role=role,
                task_id=result.task_id,
                selected_agent=selected.agent if selected else None,
                duration=result.duration,
                success=result.success,
                output=result.output,
            )
            steps.append(step)
            if not result.success:
                self._events.append(trace_id, role, "pipeline_failed", {"error": result.error})
                raise RuntimeError(f"agent {role} failed: {result.error}")
            payload = result.output

        self._events.append(trace_id, "orchestrator", "pipeline_completed", {"steps": len(steps)})
        return AnalyzeResponse(trace_id=trace_id, query=request.query, steps=steps, report=payload)

    async def _run_auction(self, role: AgentRole, trace_id: str, payload: dict[str, object]) -> BidResponse | None:
        request = BidRequest(task_type=role, payload=dict(payload))
        try:
            raw_bid = await self._bus.request_json(AUCTION_SUBJECTS[role], request.model_dump(), timeout=2)
            bid = BidResponse.model_validate(raw_bid)
            self._events.append(trace_id, "auction", f"{role}_bid", bid.model_dump())
            return bid if bid.available else None
        except Exception as exc:
            self._logger.warning("auction failed role=%s error=%s", role, exc)
            self._events.append(trace_id, "auction", f"{role}_bid_failed", {"error": str(exc)})
            return None

    async def _send_with_retry(self, role: AgentRole, trace_id: str, payload: dict[str, object]) -> AgentResult:
        last_error: Exception | None = None
        for attempt in range(1, self._retries + 1):
            task = AgentTask(type=role, trace_id=trace_id, payload=dict(payload))
            self._events.append(trace_id, "orchestrator", f"send_{role}", {"task_id": task.id, "attempt": attempt})
            try:
                raw_result = await self._bus.request_json(
                    TASK_SUBJECTS[role],
                    task.model_dump(mode="json"),
                    timeout=self._timeout_seconds,
                )
                result = AgentResult.model_validate(raw_result)
                self._events.append(trace_id, role, "completed", {"task_id": result.task_id, "success": result.success})
                return result
            except Exception as exc:
                last_error = exc
                self._logger.warning("agent request failed role=%s attempt=%s error=%s", role, attempt, exc)
                self._events.append(trace_id, role, "retry", {"attempt": attempt, "error": str(exc)})

        raise TimeoutError(f"agent {role} did not respond after {self._retries} attempts") from last_error
