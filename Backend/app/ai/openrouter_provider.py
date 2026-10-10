"""Optional text/receipt fallback through a fixed, vision-capable OpenRouter model.

Reuse the existing extraction prompts and validation, not another accounting path.
This chosen model has no speech transcription capability; voice skips this provider
for transcription but may use it to extract the transcribed transaction.
"""
from __future__ import annotations

import asyncio
import base64
from datetime import date
import httpx

from app.ai import prompts
from app.ai.base import ProviderError, TextResult
from app.ai.groq_provider import GroqProvider
from app.config import settings


class OpenRouterStatusError(Exception):
    def __init__(self, status: int) -> None:
        self.status_code = status
        super().__init__("OpenRouter rejected the request")


class OpenRouterProvider(GroqProvider):
    name = "openrouter"
    unsupported_capabilities = {"transcribe_audio"}

    def __init__(self) -> None:
        # Do not construct a Groq SDK client for a different service's credential.
        pass

    async def _completion(self, messages: list[dict], *, json_mode: bool = True) -> str:
        payload = {"model": settings.openrouter_model, "messages": messages,
                   "max_tokens": 1024, "temperature": 0.1}
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        try:
            async with httpx.AsyncClient(timeout=settings.ai_timeout_seconds) as client:
                response = await asyncio.wait_for(client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {settings.openrouter_api_key}"},
                    json=payload,
                ), timeout=settings.ai_timeout_seconds)
                if response.status_code >= 400:
                    raise OpenRouterStatusError(response.status_code)
                data = response.json()
                if isinstance(data.get("error"), dict):
                    code = data["error"].get("code")
                    raise OpenRouterStatusError(code if type(code) is int else 503)
        except (httpx.HTTPError, TimeoutError, OpenRouterStatusError) as exc:
            # Never retain a response body, credential or image in exception text.
            raise ProviderError("OpenRouter request failed") from exc
        try:
            content = data["choices"][0]["message"]["content"]
            if not isinstance(content, str) or not content.strip():
                raise ValueError("empty model output")
            return content.strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError("unusable OpenRouter response") from exc

    async def _chat_text(self, system: str, user: str, *, repair_hint: str = "") -> str:
        return await self._completion([
            {"role": "system", "content": system},
            {"role": "user", "content": f"{user}\n{repair_hint}"},
        ])

    async def _chat_vision(self, prompt: str, image: bytes, mime: str) -> str:
        data_url = f"data:{mime};base64,{base64.b64encode(image).decode()}"
        return await self._completion([{"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": data_url}},
        ]}])

    async def transcribe_audio(self, audio: bytes, mime: str, *, repair_hint: str = ""):
        raise ProviderError("Selected OpenRouter model does not transcribe audio", category="configuration")

    async def compose_answer(self, question: str, tool_name: str, tool_result: dict, *, repair_hint: str = "") -> TextResult:
        text = await self._completion([
            {"role": "system", "content": prompts.answer_system(question, tool_name, tool_result)},
            {"role": "user", "content": f"Write the answer now.\n{repair_hint}"},
        ], json_mode=False)
        return TextResult(text=text)

    async def draft_reminder(self, debtor: str, outstanding_paisa: int, oldest_unpaid: date | None, *, tone: str = "friendly", repair_hint: str = "") -> TextResult:
        text = await self._completion([
            {"role": "system", "content": prompts.reminder_system(debtor, outstanding_paisa, oldest_unpaid, tone)},
            {"role": "user", "content": f"Write the reminder message now.\n{repair_hint}"},
        ], json_mode=False)
        return TextResult(text=text)

    async def ping(self) -> None:
        await self._chat_text("Reply with JSON only.", 'Return {"ok":true}.')
