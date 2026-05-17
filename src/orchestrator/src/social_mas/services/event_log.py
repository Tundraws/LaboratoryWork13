from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class Event:
    timestamp: datetime
    trace_id: str
    actor: str
    action: str
    payload: dict[str, Any] = field(default_factory=dict)


class EventLog:
    """In-memory event log for the monitoring dashboard and traces."""

    def __init__(self, max_size: int = 300) -> None:
        self._events: deque[Event] = deque(maxlen=max_size)

    def append(self, trace_id: str, actor: str, action: str, payload: dict[str, Any] | None = None) -> None:
        self._events.append(
            Event(
                timestamp=datetime.now(timezone.utc),
                trace_id=trace_id,
                actor=actor,
                action=action,
                payload=payload or {},
            )
        )

    def list(self, limit: int = 100) -> list[Event]:
        return list(self._events)[-limit:]

