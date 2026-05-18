from __future__ import annotations

import pytest

from llm_agent.config import Settings
from llm_agent.provider import MockLLMProvider, build_provider
from llm_agent.service import build_prompt


def test_build_prompt_includes_trends() -> None:
    prompt = build_prompt(
        {
            "source_items": 3,
            "trends": [
                {"term": "качество", "count": 2},
                {"term": "поддержка", "count": 1},
            ],
        }
    )

    assert "Количество источников: 3" in prompt
    assert "качество" in prompt
    assert "поддержка" in prompt


@pytest.mark.asyncio
async def test_mock_provider_returns_actionable_insight() -> None:
    provider = MockLLMProvider()

    response = await provider.generate("Тренды: качество, поддержка")

    assert "LLM-вывод" in response
    assert "Рекомендуется" in response


def test_build_provider_defaults_to_mock() -> None:
    provider = build_provider(Settings(llm_provider="mock"))

    assert isinstance(provider, MockLLMProvider)

