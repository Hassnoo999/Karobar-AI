"""Backup routing, vision payloads, privacy and bounded waits: no live API calls."""
import asyncio
import json
from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest

from app.ai import adapter
from app.ai.adapter import FallbackAdapter
from app.ai.base import ExtractionResult, ProviderError, TranscriptResult
from app.ai.openrouter_provider import OpenRouterProvider
from app.config import Settings, settings


def test_backup_chain_and_duplicate_key_skip():
    config = Settings(_env_file=None, ai_provider="auto", groq_api_key="primary", groq_fallback_api_key="backup",
                      gemini_api_key="gemini", openrouter_api_key="router")
    assert config.provider_chain() == ["groq", "groq_backup", "gemini", "openrouter"]
    config.groq_fallback_api_key = "primary"
    assert config.provider_chain() == ["groq", "gemini", "openrouter"]
    config.ai_provider = "openrouter"
    assert config.provider_chain() == ["openrouter"]


def test_backup_groq_uses_separate_key(monkeypatch):
    from app.ai import groq_provider
    calls = []
    monkeypatch.setattr(groq_provider, "AsyncGroq", lambda **kwargs: calls.append(kwargs))
    provider = groq_provider.GroqProvider(api_key="fixture-backup", name="groq_backup")
    assert provider.name == "groq_backup"
    assert calls == [{"api_key": "fixture-backup", "max_retries": 0}]


def test_throttled_primary_falls_back_to_backup_without_demo():
    cause = SimpleNamespace(status_code=429)
    error = ProviderError("private upstream detail")
    error.__cause__ = Exception("private")
    error.__cause__.status_code = cause.status_code
    first = SimpleNamespace(name="groq", extract_event_from_image=AsyncMock(side_effect=error))
    second = SimpleNamespace(name="groq_backup", extract_event_from_image=AsyncMock(return_value=ExtractionResult(amount_rupees=5000)))
    result = asyncio.run(FallbackAdapter([first, second]).extract_event_from_image(b"image", "image/png", date.today()))
    assert result.provider == "groq_backup"
    first.extract_event_from_image.assert_awaited_once()


@pytest.mark.parametrize("status,category", [(402, "quota_exhausted"), (429, "rate_limit"), (503, "busy"), (401, "configuration")])
def test_openrouter_errors_safe_and_typed(monkeypatch, status, category):
    async def respond(*args, **kwargs):
        return httpx.Response(status, json={"error": {"message": "SECRET merchant receipt"}})
    monkeypatch.setattr(httpx.AsyncClient, "post", respond)
    with pytest.raises(ProviderError) as caught:
        asyncio.run(FallbackAdapter([OpenRouterProvider()]).extract_event_from_text("fixture", date.today()))
    assert caught.value.category == category
    assert "SECRET" not in str(caught.value)


def test_openrouter_vision_json_and_prose_modes(monkeypatch):
    calls = []
    async def respond(*args, **kwargs):
        calls.append(kwargs)
        content = json.dumps({"event_type": "credit_sale", "amount_rupees": 5000}) if "response_format" in kwargs["json"] else "A polite payment reminder."
        return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})
    monkeypatch.setattr(httpx.AsyncClient, "post", respond)
    monkeypatch.setattr(settings, "openrouter_api_key", "fixture-private-key")
    provider = OpenRouterProvider()
    result = asyncio.run(provider.extract_event_from_image(b"fixture", "image/png", date.today()))
    assert result.amount_rupees == 5000
    image = calls[0]["json"]["messages"][0]["content"][1]
    assert image["type"] == "image_url" and image["image_url"]["url"].startswith("data:image/png;base64,")
    assert calls[0]["json"]["max_tokens"] == 1024
    reminder = asyncio.run(provider.draft_reminder("Fixture", 500000, date.today()))
    assert "response_format" not in calls[1]["json"]
    assert reminder.text == "A polite payment reminder."


def test_openrouter_is_skipped_for_speech():
    router = OpenRouterProvider()
    router.transcribe_audio = AsyncMock()
    speech = SimpleNamespace(name="gemini", transcribe_audio=AsyncMock(return_value=TranscriptResult(text="Cash sale 2500")))
    result = asyncio.run(FallbackAdapter([router, speech]).transcribe_audio(b"audio", "audio/webm"))
    assert result.provider == "gemini"
    router.transcribe_audio.assert_not_awaited()


def test_fallback_deadline_returns_actionable_error(monkeypatch):
    monkeypatch.setattr(adapter, "CAPABILITY_TIMEOUT_SECONDS", 0.001)
    async def slow(*args, **kwargs):
        await asyncio.sleep(1)
    provider = SimpleNamespace(name="groq", extract_event_from_text=slow)
    with pytest.raises(ProviderError) as caught:
        asyncio.run(FallbackAdapter([provider]).extract_event_from_text("fixture", date.today()))
    assert caught.value.category == "timeout"
