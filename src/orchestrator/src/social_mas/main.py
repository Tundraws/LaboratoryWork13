from __future__ import annotations

import uvicorn

from social_mas.core.config import Settings


def main() -> None:
    """Run the FastAPI orchestrator with uvicorn."""
    settings = Settings()
    uvicorn.run(
        "social_mas.api.app:create_app",
        host=settings.api_host,
        port=settings.api_port,
        factory=True,
        log_config=None,
    )


if __name__ == "__main__":
    main()

