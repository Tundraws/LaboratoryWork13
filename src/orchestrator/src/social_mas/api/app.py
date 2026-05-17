from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.templating import Jinja2Templates

from social_mas.core.config import Settings
from social_mas.core.logging import configure_logging
from social_mas.core.security import JWTVerifier, Principal, bearer_scheme
from social_mas.schemas import AnalyzeRequest, AnalyzeResponse
from social_mas.services.event_log import EventLog
from social_mas.services.nats_gateway import NATSGateway
from social_mas.services.orchestrator import Orchestrator


templates = Jinja2Templates(directory="src/social_mas/templates")


class AppState:
    def __init__(self, settings: Settings, events: EventLog, orchestrator: Orchestrator, bus: NATSGateway) -> None:
        self.settings = settings
        self.events = events
        self.orchestrator = orchestrator
        self.bus = bus
        self.security = JWTVerifier(settings)


def create_app() -> FastAPI:
    configure_logging()
    logger = logging.getLogger("social_mas.api")
    settings = Settings()
    events = EventLog()
    bus = NATSGateway(settings.nats_url, logger)
    orchestrator = Orchestrator(
        bus=bus,
        events=events,
        timeout_seconds=settings.request_timeout_seconds,
        retries=settings.request_retries,
        logger=logger,
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.container = AppState(settings, events, orchestrator, bus)
        await bus.connect()
        yield
        await bus.close()

    app = FastAPI(
        title="Social MAS Orchestrator",
        description="Мультиагентная система анализа социальных сетей",
        version="1.0.0",
        lifespan=lifespan,
    )

    def get_state(request: Request) -> AppState:
        return request.app.state.container

    def require_principal(
        request: Request,
        credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    ) -> Principal:
        state_container: AppState = request.app.state.container
        return state_container.security.verify(credentials)

    @app.get("/healthz")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/analyze", response_model=AnalyzeResponse)
    async def analyze(
        payload: AnalyzeRequest,
        state_container: AppState = Depends(get_state),
        _: Principal = Depends(require_principal),
    ) -> AnalyzeResponse:
        try:
            return await state_container.orchestrator.analyze(payload)
        except TimeoutError as exc:
            raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    @app.get("/api/traces")
    async def traces(state_container: AppState = Depends(get_state), limit: int = 100) -> list[dict[str, object]]:
        return [
            {
                "timestamp": event.timestamp.isoformat(),
                "trace_id": event.trace_id,
                "actor": event.actor,
                "action": event.action,
                "payload": event.payload,
            }
            for event in state_container.events.list(limit=limit)
        ]

    @app.get("/dashboard", response_class=HTMLResponse)
    async def dashboard(request: Request, state_container: AppState = Depends(get_state)) -> HTMLResponse:
        return templates.TemplateResponse(
            "dashboard.html",
            {"request": request, "events": state_container.events.list(limit=80)},
        )

    return app

