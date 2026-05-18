from __future__ import annotations

import asyncio
import json
import logging
import signal
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from typing import Any

import nats

from llm_agent.config import Settings
from llm_agent.models import AgentResult, AgentTask, BidRequest, BidResponse
from llm_agent.provider import LLMProvider


class HealthHandler(BaseHTTPRequestHandler):
    """Tiny stdlib health endpoint to avoid another framework dependency."""

    def do_GET(self) -> None:
        if self.path != "/healthz":
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status":"ok"}')

    def log_message(self, format: str, *args: object) -> None:
        return


class HealthServer:
    """Background HTTP health server for Docker healthchecks."""

    def __init__(self, host: str, port: int) -> None:
        self._server = ThreadingHTTPServer((host, port), HealthHandler)
        self._thread = Thread(target=self._server.serve_forever, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=3)


class LLMAgent:
    """NATS request/reply agent that turns trends into LLM insights."""

    def __init__(self, settings: Settings, provider: LLMProvider, logger: logging.Logger | None = None) -> None:
        self._settings = settings
        self._provider = provider
        self._logger = logger or logging.getLogger(__name__)
        self._processed_count = 0
        self._nats: nats.NATS | None = None

    async def run(self) -> None:
        self._nats = await nats.connect(self._settings.nats_url, name=self._settings.agent_name)
        await self._nats.queue_subscribe(self._settings.task_subject, "social-mas-llm", cb=self._handle_task)
        await self._nats.queue_subscribe(self._settings.auction_subject, "social-mas-llm", cb=self._handle_bid)
        self._logger.info("llm agent subscribed task_subject=%s", self._settings.task_subject)

        stop_event = asyncio.Event()
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, stop_event.set)
        await stop_event.wait()
        await self.close()

    async def close(self) -> None:
        if self._nats is not None:
            await self._nats.drain()
            self._nats = None

    async def _handle_bid(self, msg: nats.aio.msg.Msg) -> None:
        try:
            request = BidRequest.model_validate_json(msg.data)
            relevance = 3 if request.payload.get("trends") else 0
            cost = max(1, 8 + (self._processed_count % 4) - relevance)
            response = BidResponse(
                agent=self._settings.agent_name,
                cost=cost,
                available=True,
                reason=f"provider={self._settings.llm_provider} relevance={relevance}",
            )
        except Exception as exc:
            response = BidResponse(agent=self._settings.agent_name, cost=999, available=False, reason=str(exc))
        await msg.respond(response.model_dump_json().encode("utf-8"))

    async def _handle_task(self, msg: nats.aio.msg.Msg) -> None:
        started = time.perf_counter()
        try:
            task = AgentTask.model_validate_json(msg.data)
            prompt = build_prompt(task.payload)
            insight = await self._provider.generate(prompt)
            self._processed_count += 1
            output = dict(task.payload)
            output["llm_insight"] = insight
            output["llm_provider"] = self._settings.llm_provider
            output["processed_total"] = self._processed_count
            result = AgentResult(
                task_id=task.id,
                agent=self._settings.agent_name,
                role="llm",
                trace_id=task.trace_id,
                success=True,
                output=output,
                duration=f"{time.perf_counter() - started:.3f}s",
            )
        except Exception as exc:
            self._logger.exception("llm task failed")
            result = AgentResult(
                task_id="unknown",
                agent=self._settings.agent_name,
                role="llm",
                trace_id="unknown",
                success=False,
                error=str(exc),
                duration=f"{time.perf_counter() - started:.3f}s",
            )
        await msg.respond(result.model_dump_json().encode("utf-8"))


def build_prompt(payload: dict[str, Any]) -> str:
    """Build a concise prompt from detected trends and sentiment data."""
    trends = payload.get("trends", [])
    trend_terms: list[str] = []
    if isinstance(trends, list):
        for item in trends[:5]:
            if isinstance(item, dict) and item.get("term"):
                trend_terms.append(str(item["term"]))
    source_items = payload.get("source_items", "unknown")
    return (
        "Ты аналитик социальных сетей. На основе данных дай краткий вывод и рекомендации. "
        f"Количество источников: {source_items}. Тренды: {', '.join(trend_terms) or 'нет данных'}."
    )

