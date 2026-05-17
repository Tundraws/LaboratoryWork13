from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Protocol

import nats


class MessageBus(Protocol):
    async def request_json(self, subject: str, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
        """Send request and decode JSON response."""

    async def close(self) -> None:
        """Close bus resources."""


class NATSGateway:
    """NATS request/reply adapter isolated from orchestration business logic."""

    def __init__(self, url: str, logger: logging.Logger | None = None) -> None:
        self._url = url
        self._logger = logger or logging.getLogger(__name__)
        self._client: nats.NATS | None = None

    async def connect(self) -> None:
        self._client = await nats.connect(self._url, name="social-mas-orchestrator")
        self._logger.info("connected to nats url=%s", self._url)

    async def request_json(self, subject: str, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
        if self._client is None:
            raise RuntimeError("NATS client is not connected")
        encoded = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
        message = await self._client.request(subject, encoded, timeout=timeout)
        return json.loads(message.data.decode("utf-8"))

    async def close(self) -> None:
        if self._client is not None:
            await asyncio.wait_for(self._client.drain(), timeout=5)
            self._client = None

