from __future__ import annotations

import asyncio
import logging

from llm_agent.config import Settings
from llm_agent.provider import build_provider
from llm_agent.service import HealthServer, LLMAgent


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        force=True,
    )


async def async_main() -> None:
    configure_logging()
    settings = Settings()
    health = HealthServer(settings.health_addr, settings.health_port)
    health.start()
    try:
        agent = LLMAgent(settings, build_provider(settings), logging.getLogger("llm_agent"))
        await agent.run()
    finally:
        health.stop()


def main() -> None:
    asyncio.run(async_main())


if __name__ == "__main__":
    main()

