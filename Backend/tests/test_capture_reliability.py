"""Real fallback contracts and safe user diagnostics; no paid calls."""
import asyncio
from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from app.ai.adapter import FallbackAdapter
from app.ai.base import ExtractionResult, ProviderError
from app.ai.groq_provider import GroqProvider
from app.config import Settings


def test_legacy_compound_vision_configuration_migrates():
    config = Settings(_env_file=None, groq_vision_model="groq/compound")
    assert config.receipt_vision_model == "qwen/qwen3.8-27b"


def test_groq_vision_sends_actual_image_and_json_mode():
    create = AsyncMock(return_value=SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content='{"amount_rupees":5000,"event_type":null,"occurred_at":null}'))]))
    provider = GroqProvider.__new__(GroqProvider)
    provider.client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    result = asyncio.run(provider.extract_event_from_image(b"image", "image/png", date.today()))
    args = create.call_args.kwargs
    assert args["response_format"] == {"type": "json_object"}
    assert args["messages"][0]["content"][1]["image_url"]["url"].startswith("data:image/png;base64,")
    assert result.amount_rupees == 5000 and result.event_type is None


def test_receipt_falls_back_to_second_real_provider():
    first = SimpleNamespace(name="groq", extract_event_from_image=AsyncMock(side_effect=ProviderError("private upstream body")))
    second = SimpleNamespace(name="gemini", extract_event_from_image=AsyncMock(return_value=ExtractionResult(amount_rupees=5000)))
    result = asyncio.run(FallbackAdapter([first, second]).extract_event_from_image(b"image", "image/png", date.today()))
    assert result.provider == "gemini"
    first.extract_event_from_image.assert_awaited_once()


@pytest.mark.parametrize("status,category", [(429,"rate_limit"),(401,"configuration"),(403,"configuration"),(404,"configuration"),(503,"busy")])
def test_safe_numeric_failure_categories(client, monkeypatch, status, category):
    from tests.test_capture_api import PNG_BYTES
    cause = Exception("SECRET receipt details")
    cause.status_code = status
    error = ProviderError("SECRET URL")
    error.__cause__ = cause
    provider = SimpleNamespace(name="groq", extract_event_from_image=AsyncMock(side_effect=error))
    monkeypatch.setattr("app.routers.bridge.get_adapter", lambda: FallbackAdapter([provider]))
    response = client.post("/api/understand/receipt", files={"file": ("photo.png", PNG_BYTES, "image/png")})
    assert response.status_code == 503
    assert response.json()["error"]["reason"] == category
    assert "SECRET" not in response.text
    assert client.get("/api/combined").json()["summary"]["record_count"] == 0


@pytest.mark.parametrize("route", ["/api/understand/receipt", "/api/capture/extract-receipt"])
def test_invalid_image_rejected_before_storage_or_provider(client, monkeypatch, route):
    store = AsyncMock()
    adapter = AsyncMock()
    monkeypatch.setattr("app.routers.bridge.get_adapter", lambda: adapter)
    response = client.post(route, files={"file": ("photo.png", b"not a photo", "image/png")})
    assert response.status_code == 422
    assert "could not be opened" in response.json()["error"]["message"]
    adapter.extract_event_from_image.assert_not_awaited()


def test_model_output_failure_not_reported_as_service_outage(client, monkeypatch):
    from tests.test_capture_api import PNG_BYTES
    provider = SimpleNamespace(name="groq", extract_event_from_image=AsyncMock(side_effect=ValueError("SECRET invalid output")))
    monkeypatch.setattr("app.routers.bridge.get_adapter", lambda: FallbackAdapter([provider]))
    response = client.post("/api/understand/receipt", files={"file": ("photo.png", PNG_BYTES, "image/png")})
    assert response.status_code == 422
    assert response.json()["error"]["reason"] == "invalid_output"
    assert "SECRET" not in response.text
