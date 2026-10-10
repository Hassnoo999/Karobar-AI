"""Real-provider fallback, with one repair retry for structured output.

Unavailable APIs fail clearly; they never manufacture a Demo response.
Explicit local demo mode remains available for isolated offline tests only.
"""
from __future__ import annotations

from datetime import date
import asyncio
import io
import logging
import wave
from typing import Any

from app.ai.base import AI_FAILURE_MESSAGES, ProviderError
from app.ai.demo_provider import DemoProvider
from app.ai.gemini_provider import GeminiProvider
from app.ai.groq_provider import GroqProvider
from app.ai.openrouter_provider import OpenRouterProvider
from app.config import settings

logger = logging.getLogger(__name__)
CAPABILITY_TIMEOUT_SECONDS = 120.0  # voice has two phases; keep both below the 300s cloud limit


def _failure_status(exc: Exception) -> int | None:
    """Provider exception text can contain keys/input; retain only numeric status."""
    cause = exc.__cause__
    for attribute in ("status_code", "code"):
        value = getattr(cause, attribute, None)
        if type(value) is int and 400 <= value <= 599:
            return value
    return None

def _failure_category(exc: Exception) -> str:
    if isinstance(exc, ValueError):
        return "invalid_output"
    status = _failure_status(exc)
    if status == 429:
        return "rate_limit"
    if status == 402:
        return "quota_exhausted"
    if status in {400, 401, 403, 404, 422}:
        return "configuration"
    if status in {502, 503, 504}:
        return "busy"
    if isinstance(exc.__cause__, TimeoutError) or type(exc.__cause__).__name__ in {"APITimeoutError", "ReadTimeout", "ConnectTimeout"}:
        return "timeout"
    return getattr(exc, "category", "unavailable")


REPAIR_HINT = (
    "IMPORTANT: Your previous reply was not a single valid JSON object. "
    "Reply again with ONLY the JSON object — no explanations, no markdown fences."
)


class FallbackAdapter:
    def __init__(self, providers: list[Any]) -> None:
        self.providers = providers

    def chain_names(self) -> list[str]:
        return [p.name for p in self.providers]

    async def _call(self, method_name: str, /, *args: Any, **kwargs: Any) -> Any:
        try:
            return await asyncio.wait_for(self._call_chain(method_name, *args, **kwargs), timeout=CAPABILITY_TIMEOUT_SECONDS)
        except TimeoutError as exc:
            raise ProviderError(AI_FAILURE_MESSAGES["timeout"], category="timeout") from exc

    async def _call_chain(self, method_name: str, /, *args: Any, **kwargs: Any) -> Any:
        last_error: Exception = ProviderError("no provider configured", category="not_configured")
        for provider in self.providers:
            if method_name in getattr(provider, "unsupported_capabilities", ()):
                continue
            method = getattr(provider, method_name)
            for attempt in ((1,) if method_name == "transcribe_audio" else (1, 2)):
                call_kwargs = dict(kwargs)
                if attempt == 2:
                    call_kwargs["repair_hint"] = REPAIR_HINT
                try:
                    result = await method(*args, **call_kwargs)
                    if method_name == "transcribe_audio" and (
                        not result.text.strip() or result.text.strip().upper() == "[NO_SPEECH]"
                    ):
                        raise ValueError("no intelligible speech")
                except ValueError as exc:
                    # malformed model output -> retry same provider once with repair hint
                    last_error = exc
                    logger.warning("AI output rejected provider=%s capability=%s attempt=%d",
                                   provider.name, method_name, attempt)
                    continue
                except ProviderError as exc:
                    # provider unavailable -> next provider immediately
                    last_error = exc
                    logger.warning("AI provider unavailable provider=%s capability=%s category=%s status=%s",
                                   provider.name, method_name, type(exc.__cause__ or exc).__name__,
                                   _failure_status(exc))
                    break
                result.provider = provider.name
                return result
        category = _failure_category(last_error)
        raise ProviderError(AI_FAILURE_MESSAGES.get(category, AI_FAILURE_MESSAGES["unavailable"]), category=category) from last_error

    # --- capability facade ---------------------------------------------------

    async def transcribe_audio(self, audio: bytes, mime: str):
        # Whisper can hallucinate speech even for an all-zero WAV. Reject
        # unambiguous digital silence before any paid provider request.
        if (mime or "").split(";")[0] in {"audio/wav", "audio/x-wav"}:
            try:
                with wave.open(io.BytesIO(audio), "rb") as recording:
                    samples = recording.readframes(recording.getnframes())
                    silent_value = 128 if recording.getsampwidth() == 1 else 0
                    if not samples or all(sample == silent_value for sample in samples):
                        raise ProviderError(AI_FAILURE_MESSAGES["no_speech"], category="no_speech")
            except (wave.Error, EOFError):
                # Other supported encodings still go through the real provider.
                pass
        return await self._call("transcribe_audio", audio, mime)

    async def extract_event_from_text(self, text: str, today: date):
        return await self._call("extract_event_from_text", text, today)

    async def extract_event_from_image(self, image: bytes, mime: str, today: date):
        return await self._call("extract_event_from_image", image, mime, today)

    async def interpret_question(self, question: str, today: date):
        return await self._call("interpret_question", question, today)

    async def compose_answer(self, question: str, tool_name: str, tool_result: dict[str, Any]):
        return await self._call("compose_answer", question, tool_name, tool_result)

    async def draft_reminder(self, debtor: str, outstanding_paisa: int, oldest_unpaid: date | None, *, tone: str = "friendly"):
        return await self._call("draft_reminder", debtor, outstanding_paisa, oldest_unpaid, tone=tone)


_ADAPTER: FallbackAdapter | None = None


def get_adapter() -> FallbackAdapter:
    """Build the explicitly configured chain; no implicit Demo fallback."""
    global _ADAPTER
    if _ADAPTER is None:
        providers: list[Any] = []
        for name in settings.provider_chain():
            if name == "groq":
                providers.append(GroqProvider())
            elif name == "groq_backup":
                providers.append(GroqProvider(api_key=settings.groq_fallback_api_key, name="groq_backup"))
            elif name == "gemini":
                providers.append(GeminiProvider())
            elif name == "demo":
                providers.append(DemoProvider())
            elif name == "openrouter":
                providers.append(OpenRouterProvider())
        _ADAPTER = FallbackAdapter(providers)
    return _ADAPTER


def reset_adapter() -> None:
    """Used by tests / config reloads."""
    global _ADAPTER
    _ADAPTER = None
