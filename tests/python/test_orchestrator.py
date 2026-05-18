from __future__ import annotations

import asyncio
from typing import Any

import pytest

from social_mas.schemas import AnalyzeRequest
from social_mas.services.event_log import EventLog
from social_mas.services.orchestrator import Orchestrator


class FakeBus:
    def __init__(self, failures: dict[str, int] | None = None) -> None:
        self.failures = failures or {}
        self.calls: list[str] = []

    async def request_json(self, subject: str, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
        self.calls.append(subject)
        if self.failures.get(subject, 0) > 0:
            self.failures[subject] -= 1
            raise asyncio.TimeoutError("simulated timeout")

        if subject.startswith("social.auction."):
            role = subject.rsplit(".", maxsplit=1)[-1]
            return {"agent": f"{role}-agent", "role": role, "cost": 3, "available": True, "reason": "test"}

        role = subject.rsplit(".", maxsplit=1)[-1]
        task_id = payload["id"]
        if role == "collector":
            output = {"posts": [{"id": "p1", "text": "хороший сервис и отчёт"}], "count": 1}
        elif role == "sentiment":
            output = {"items": [{"id": "p1", "text": "хороший сервис и отчёт", "sentiment": "positive", "score": 2}]}
        elif role == "trends":
            output = {"trends": [{"term": "сервис", "count": 1}, {"term": "отчёт", "count": 1}]}
        elif role == "llm":
            output = {
                "trends": payload["payload"]["trends"],
                "llm_insight": "LLM-вывод: усилить мониторинг ключевых тем",
                "llm_provider": "mock",
            }
        else:
            output = {
                "markdown": "Отчёт готов",
                "trend_count": 2,
                "llm_insight": payload["payload"].get("llm_insight"),
            }
        return {
            "task_id": task_id,
            "agent": f"{role}-agent",
            "role": role,
            "trace_id": payload["trace_id"],
            "success": True,
            "output": output,
            "duration": "1ms",
        }

    async def close(self) -> None:
        return None


@pytest.mark.asyncio
async def test_pipeline_success() -> None:
    events = EventLog()
    orchestrator = Orchestrator(FakeBus(), events, timeout_seconds=1, retries=2)

    result = await orchestrator.analyze(AnalyzeRequest(query="соцсети", limit=1))

    assert result.query == "соцсети"
    assert len(result.steps) == 5
    assert result.report["markdown"] == "Отчёт готов"
    assert result.report["llm_insight"] == "LLM-вывод: усилить мониторинг ключевых тем"
    assert len(events.list()) >= 9


@pytest.mark.asyncio
async def test_retry_after_timeout() -> None:
    events = EventLog()
    bus = FakeBus(failures={"social.tasks.collector": 1})
    orchestrator = Orchestrator(bus, events, timeout_seconds=1, retries=2)

    result = await orchestrator.analyze(AnalyzeRequest(query="соцсети", limit=1))

    assert result.steps[0].role == "collector"
    assert bus.calls.count("social.tasks.collector") == 2


@pytest.mark.asyncio
async def test_timeout_after_retries() -> None:
    orchestrator = Orchestrator(
        FakeBus(failures={"social.tasks.collector": 3}),
        EventLog(),
        timeout_seconds=1,
        retries=2,
    )

    with pytest.raises(TimeoutError):
        await orchestrator.analyze(AnalyzeRequest(query="соцсети", limit=1))
