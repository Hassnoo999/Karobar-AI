"""Real-capture boundaries, without paid API calls or shared ledger writes."""
import asyncio
import io
import wave
from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from PIL import Image

from app.ai.adapter import FallbackAdapter
from app.ai.base import ExtractionResult, ProviderError, TranscriptResult, normalize_extraction
from app.ai.gemini_provider import CaptureOutput, GeminiProvider, _compress_image
from app.ai.groq_provider import GroqProvider
from app.config import Settings, settings


@pytest.mark.parametrize("mode,keys,expected", [
    ("auto", {}, []),
    ("auto", {"groq_api_key": "fixture"}, ["groq"]),
    ("auto", {"gemini_api_key": "fixture"}, ["gemini"]),
    ("auto", {"groq_api_key": "fixture", "gemini_api_key": "fixture"}, ["groq", "gemini"]),
    ("groq", {"gemini_api_key": "fixture"}, []),
    ("gemini", {"groq_api_key": "fixture"}, []),
])
def test_real_modes_never_implicitly_use_demo(mode, keys, expected):
    config = Settings(_env_file=None, ai_provider=mode, groq_api_key="", gemini_api_key="")
    for key, value in keys.items():
        setattr(config, key, value)
    assert config.provider_chain() == expected


def test_demo_is_explicit_local_only():
    assert Settings(_env_file=None, ai_provider="demo", environment="development").provider_chain() == ["demo"]
    assert Settings(_env_file=None, ai_provider="demo", environment="production").provider_chain() == []


def test_empty_chain_fails_instead_of_manufacturing_capture():
    with pytest.raises(ProviderError, match="real AI provider"):
        asyncio.run(FallbackAdapter([]).transcribe_audio(b"audio", "audio/webm"))


@pytest.mark.parametrize("width", [1, 2])
def test_digital_wav_silence_rejected_before_paid_call(width):
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as recording:
        recording.setnchannels(1)
        recording.setsampwidth(width)
        recording.setframerate(16000)
        recording.writeframes(bytes([128 if width == 1 else 0]) * (16000 * width))
    provider = SimpleNamespace(name="groq", transcribe_audio=AsyncMock())
    with pytest.raises(ProviderError, match="No speech"):
        asyncio.run(FallbackAdapter([provider]).transcribe_audio(buffer.getvalue(), "audio/wav"))
    provider.transcribe_audio.assert_not_awaited()


@pytest.mark.parametrize("text", ["", "  ", "[NO_SPEECH]"])
def test_empty_transcription_uses_next_real_provider_without_json_retry(text):
    first = SimpleNamespace(name="groq", transcribe_audio=AsyncMock(return_value=TranscriptResult(text=text)))
    second = SimpleNamespace(name="gemini", transcribe_audio=AsyncMock(return_value=TranscriptResult(text="Cash sale 2500")))
    result = asyncio.run(FallbackAdapter([first, second]).transcribe_audio(b"audio", "audio/webm"))
    assert result.provider == "gemini"
    first.transcribe_audio.assert_awaited_once()


def test_receipt_skips_unimplemented_groq_vision():
    first = SimpleNamespace(name="groq", unsupported_capabilities={"extract_event_from_image"}, extract_event_from_image=AsyncMock())
    second = SimpleNamespace(name="gemini", extract_event_from_image=AsyncMock(return_value=ExtractionResult(amount_rupees=5000)))
    result = asyncio.run(FallbackAdapter([first, second]).extract_event_from_image(b"image", "image/png", date.today()))
    assert result.provider == "gemini"
    first.extract_event_from_image.assert_not_awaited()


def test_exhausted_chain_does_not_echo_provider_secrets():
    provider = SimpleNamespace(name="groq", transcribe_audio=AsyncMock(side_effect=ProviderError("SECRET merchant data")))
    with pytest.raises(ProviderError) as exc:
        asyncio.run(FallbackAdapter([provider]).transcribe_audio(b"audio", "audio/webm"))
    assert "SECRET" not in str(exc.value)
    assert "merchant data" not in str(exc.value)


def test_whisper_auto_detects_language_and_preserves_container():
    create = AsyncMock(return_value=SimpleNamespace(text="A cash sale of 2500 rupees"))
    provider = GroqProvider.__new__(GroqProvider)
    provider.client = SimpleNamespace(audio=SimpleNamespace(transcriptions=SimpleNamespace(create=create)))
    result = asyncio.run(provider.transcribe_audio(b"audio", "audio/mp4"))
    arguments = create.call_args.kwargs
    assert "language" not in arguments
    assert arguments["temperature"] == 0
    assert arguments["file"] == ("audio.m4a", b"audio", "audio/mp4")
    assert "2500" in result.text


def test_receipt_keeps_small_png_lossless():
    buffer = io.BytesIO()
    Image.new("RGB", (900, 760), "white").save(buffer, format="PNG")
    assert _compress_image(buffer.getvalue(), "image/png") == (buffer.getvalue(), "image/png")


def test_receipt_applies_orientation_and_keeps_more_detail():
    buffer = io.BytesIO()
    image = Image.new("RGB", (3000, 1500), "white")
    exif = image.getexif()
    exif[274] = 6
    image.save(buffer, format="JPEG", exif=exif)
    result, mime = _compress_image(buffer.getvalue(), "image/jpeg")
    assert mime == "image/jpeg"
    assert Image.open(io.BytesIO(result)).size == (1024, 2048)


def test_gemini_capture_requests_nullable_schema():
    generate = AsyncMock(return_value=SimpleNamespace(text='{"event_type":null,"counterparty":null,"amount_rupees":5000,"occurred_at":null,"payment_status":null,"confidence":0.3,"notes":"Clarify transfer purpose"}'))
    provider = GeminiProvider.__new__(GeminiProvider)
    provider.client = SimpleNamespace(aio=SimpleNamespace(models=SimpleNamespace(generate_content=generate)))
    result = asyncio.run(provider.extract_event_from_image(b"unreadable", "image/png", date.today()))
    config = generate.call_args.kwargs["config"]
    assert config.response_schema == CaptureOutput
    assert config.response_mime_type == "application/json"
    assert result.event_type is None and result.occurred_at is None
    assert result.notes


@pytest.mark.parametrize("value", [float("inf"), float("nan"), "Infinity"])
def test_nonfinite_capture_values_become_missing(value):
    result = normalize_extraction({"amount_rupees": value, "confidence": value})
    assert result.amount_rupees is None and result.confidence is None


@pytest.mark.parametrize("route,mime", [("/api/understand/voice", "audio/webm"), ("/api/understand/receipt", "image/png")])
def test_no_real_provider_means_503_and_no_placeholder_or_write(client, monkeypatch, route, mime):
    from tests.test_capture_api import PNG_BYTES
    monkeypatch.setattr("app.routers.bridge.get_adapter", lambda: FallbackAdapter([]))
    before = {path for path in settings.uploads_dir.rglob("*") if path.is_file()}
    response = client.post(route, files={"file": ("capture", PNG_BYTES if "receipt" in route else b"audio", mime)})
    assert response.status_code == 503
    assert "event" not in response.json()
    assert {path for path in settings.uploads_dir.rglob("*") if path.is_file()} == before
    assert client.get("/api/combined").json()["summary"]["record_count"] == 0


def test_voice_draft_exposes_both_actual_providers(client, monkeypatch):
    from app.schemas.events import EventType
    adapter = SimpleNamespace(
        transcribe_audio=AsyncMock(return_value=TranscriptResult(text="cash sale 2500", provider="groq")),
        extract_event_from_text=AsyncMock(return_value=ExtractionResult(provider="gemini", event_type=EventType.cash_sale, amount_rupees=2500, occurred_at=date.today())),
    )
    monkeypatch.setattr("app.routers.bridge.get_adapter", lambda: adapter)
    response = client.post("/api/understand/voice", files={"file": ("audio.webm", b"audio", "audio/webm")})
    assert response.status_code == 200
    assert response.json()["event"]["transcript_provider"] == "groq"
    assert response.json()["event"]["ai_provider"] == "gemini"


def test_ambiguous_receipt_requires_type_and_date_review(client, monkeypatch):
    from tests.test_capture_api import PNG_BYTES
    adapter = SimpleNamespace(extract_event_from_image=AsyncMock(return_value=ExtractionResult(
        provider="gemini", amount_rupees=5000, notes="Please clarify sender and purpose", confidence=0.3)))
    monkeypatch.setattr("app.routers.bridge.get_adapter", lambda: adapter)
    response = client.post("/api/understand/receipt", files={"file": ("receipt.png", PNG_BYTES, "image/png")})
    event = response.json()["event"]
    assert event["event_type"] is None and event["payment_type"] is None
    assert event["date"] is None
    assert event["status"] == "pending_validation"
    assert event["notes"] == "Please clarify sender and purpose"
