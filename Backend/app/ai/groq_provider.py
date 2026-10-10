"""Groq: Qwen text/receipt vision and multilingual Whisper, with real fallback."""
from __future__ import annotations

import asyncio
import base64
from datetime import date
from typing import Any

from groq import AsyncGroq

from app.ai import prompts
from app.ai.base import (
    ExtractionResult,
    ProviderError,
    TextResult,
    ToolCall,
    TranscriptResult,
    normalize_extraction,
    normalize_tool_call,
    parse_json_object,
)
from app.config import settings

_AUDIO_EXT_BY_MIME = {
    "audio/webm": "webm",
    "video/webm": "webm",
    "audio/mp4": "m4a",
    "audio/x-m4a": "m4a",
    "audio/mpeg": "mp3",
    "audio/mp3": "mp3",
    "audio/wav": "wav",
    "audio/x-wav": "wav",
    "audio/ogg": "ogg",
    "application/ogg": "ogg",
}


def _mime_to_ext(mime: str) -> str:
    mime = (mime or "").split(";")[0].strip().lower()
    return _AUDIO_EXT_BY_MIME.get(mime, "webm")


class GroqProvider:
    name = "groq"

    def __init__(self, *, api_key: str | None = None, name: str = "groq") -> None:
        self.name = name
        # The adapter owns fallback; don't retry a throttled key inside the SDK.
        self.client = AsyncGroq(api_key=api_key or settings.groq_api_key, max_retries=0)

    # --- internals ---------------------------------------------------------

    async def _chat_text(self, system: str, user: str, *, repair_hint: str = "") -> str:
        message = f"{user}\n\n{repair_hint}" if repair_hint else user
        try:
            response = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model=settings.groq_text_model,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": message},
                    ],
                    temperature=0.1,
                ),
                timeout=settings.ai_timeout_seconds,
            )
        except Exception as exc:  # network, auth, rate limit, timeout
            raise ProviderError(f"groq chat failed: {exc}") from exc
        return (response.choices[0].message.content or "").strip()

    async def _chat_vision(self, prompt: str, image: bytes, mime: str) -> str:
        data_url = f"data:{mime or 'image/jpeg'};base64,{base64.b64encode(image).decode()}"
        try:
            response = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model=settings.receipt_vision_model,
                    response_format={"type": "json_object"},
                    max_completion_tokens=1024,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {"type": "image_url", "image_url": {"url": data_url}},
                            ],
                        }
                    ],
                    temperature=0.1,
                ),
                timeout=settings.ai_timeout_seconds,
            )
        except Exception as exc:
            raise ProviderError(f"groq vision failed: {exc}") from exc
        return (response.choices[0].message.content or "").strip()

    async def ping(self) -> None:
        try:
            await asyncio.wait_for(
                self.client.chat.completions.create(
                    model=settings.groq_ping_model,
                    messages=[{"role": "user", "content": "Reply with the single word OK."}],
                    max_tokens=10,
                    temperature=0,
                ),
                timeout=20,
            )
        except Exception as exc:
            raise ProviderError(f"groq ping failed: {exc}") from exc

    # --- capabilities ------------------------------------------------------

    async def transcribe_audio(self, audio: bytes, mime: str, *, repair_hint: str = "") -> TranscriptResult:
        try:
            response = await asyncio.wait_for(
                self.client.audio.transcriptions.create(
                    model=settings.groq_audio_model,
                    file=(f"audio.{_mime_to_ext(mime)}", audio, mime or "audio/webm"),
                    response_format="json",
                    # Auto-detect rather than force English/mixed speech into Urdu.
                    temperature=0,
                    prompt="Business vocabulary: Karobaar, udhaar, rupay, rupees, PKR. Preserve spoken names and amounts.",
                ),
                timeout=settings.ai_timeout_seconds,
            )
        except Exception as exc:
            raise ProviderError(f"groq transcription failed: {exc}") from exc
        return TranscriptResult(text=(response.text or "").strip())

    async def extract_event_from_text(self, text: str, today: date, *, repair_hint: str = "") -> ExtractionResult:
        raw = await self._chat_text(prompts.extraction_system(today), text, repair_hint=repair_hint)
        return normalize_extraction(parse_json_object(raw))

    async def extract_event_from_image(self, image: bytes, mime: str, today: date, *, repair_hint: str = "") -> ExtractionResult:
        from app.ai.gemini_provider import _compress_image
        prepared, prepared_mime = _compress_image(image, mime)
        instruction = prompts.receipt_system(today) + "\n\n" + prompts.RECEIPT_USER_INSTRUCTION
        if repair_hint:
            instruction += "\n\n" + repair_hint
        raw = await self._chat_vision(instruction, prepared, prepared_mime)
        return normalize_extraction(parse_json_object(raw))

    async def interpret_question(self, question: str, today: date, *, repair_hint: str = "") -> ToolCall:
        raw = await self._chat_text(prompts.question_system(today), question, repair_hint=repair_hint)
        return normalize_tool_call(parse_json_object(raw))

    async def compose_answer(self, question: str, tool_name: str, tool_result: dict[str, Any], *, repair_hint: str = "") -> TextResult:
        raw = await self._chat_text(
            prompts.answer_system(question, tool_name, tool_result), "Write the answer now.", repair_hint=repair_hint
        )
        if not raw:
            raise ValueError("empty answer from groq model")
        return TextResult(text=raw)

    async def draft_reminder(
        self,
        debtor: str,
        outstanding_paisa: int,
        oldest_unpaid: date | None,
        *,
        tone: str = "friendly",
        repair_hint: str = "",
    ) -> TextResult:
        raw = await self._chat_text(
            prompts.reminder_system(debtor, outstanding_paisa, oldest_unpaid, tone),
            "Write the reminder message now.",
            repair_hint=repair_hint,
        )
        if not raw:
            raise ValueError("empty reminder from groq model")
        return TextResult(text=raw)
