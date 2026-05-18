from __future__ import annotations

from typing import Protocol

import httpx

from llm_agent.config import Settings


class LLMProvider(Protocol):
    """Abstraction over local or cloud LLM providers."""

    async def generate(self, prompt: str) -> str:
        """Generate a compact analytical answer for the prompt."""


class MockLLMProvider:
    """Deterministic fallback that keeps the lab runnable without secrets."""

    async def generate(self, prompt: str) -> str:
        keywords = []
        for marker in ("тренды:", "trends:"):
            if marker in prompt.lower():
                keywords = prompt.split(":", maxsplit=1)[-1].split(",")[:3]
                break
        topics = ", ".join(item.strip() for item in keywords if item.strip()) or "ключевые темы обсуждения"
        return (
            "LLM-вывод: аудитория активно реагирует на "
            f"{topics}. Рекомендуется усилить мониторинг негативных упоминаний, "
            "подготовить короткие публичные ответы и вынести частые темы в еженедельный отчёт."
        )


class OllamaProvider:
    """Local LLM provider using Ollama /api/generate."""

    def __init__(self, settings: Settings) -> None:
        self._base_url = settings.ollama_url.rstrip("/")
        self._model = settings.ollama_model
        self._timeout = settings.request_timeout_seconds

    async def generate(self, prompt: str) -> str:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                f"{self._base_url}/api/generate",
                json={"model": self._model, "prompt": prompt, "stream": False},
            )
            response.raise_for_status()
            data = response.json()
            return str(data.get("response", "")).strip()


class CloudProvider:
    """Minimal OpenAI-compatible cloud provider through a configured HTTP endpoint."""

    def __init__(self, settings: Settings) -> None:
        if not settings.cloud_llm_api_url:
            raise ValueError("CLOUD_LLM_API_URL is required for cloud provider")
        if not settings.cloud_llm_api_key:
            raise ValueError("CLOUD_LLM_API_KEY is required for cloud provider")
        self._url = settings.cloud_llm_api_url
        self._key = settings.cloud_llm_api_key
        self._timeout = settings.request_timeout_seconds

    async def generate(self, prompt: str) -> str:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                self._url,
                headers={"Authorization": f"Bearer {self._key}"},
                json={"prompt": prompt, "max_tokens": 220},
            )
            response.raise_for_status()
            data = response.json()
            if "text" in data:
                return str(data["text"]).strip()
            choices = data.get("choices", [])
            if choices:
                message = choices[0].get("message", {})
                return str(message.get("content", choices[0].get("text", ""))).strip()
            return ""


def build_provider(settings: Settings) -> LLMProvider:
    """Create an LLM provider from settings."""
    if settings.llm_provider == "ollama":
        return OllamaProvider(settings)
    if settings.llm_provider == "cloud":
        return CloudProvider(settings)
    return MockLLMProvider()

