"""Fallback diagnostics must not log exception bodies or merchant input."""
import asyncio
from types import SimpleNamespace

from app.ai.adapter import FallbackAdapter
from app.ai.base import ProviderError


class GoodProvider:
    name = "demo"

    async def probe(self, *args, **kwargs):
        return SimpleNamespace(provider="")


def test_provider_failure_logs_status_not_sensitive_content(caplog):
    class UpstreamError(Exception):
        status_code = 429

    class BadProvider:
        name = "groq"

        async def probe(self, *args, **kwargs):
            try:
                raise UpstreamError("private-api-key private-merchant-input")
            except UpstreamError as exc:
                raise ProviderError(str(exc)) from exc

    result = asyncio.run(FallbackAdapter([BadProvider(), GoodProvider()])._call("probe", "private-merchant-input"))
    assert result.provider == "demo"
    assert "provider=groq" in caplog.text and "status=429" in caplog.text
    assert "private-api-key" not in caplog.text
    assert "private-merchant-input" not in caplog.text


def test_rejected_output_logs_attempts_not_model_output(caplog):
    class BadProvider:
        name = "gemini"

        async def probe(self, *args, **kwargs):
            raise ValueError("private-receipt-text")

    result = asyncio.run(FallbackAdapter([BadProvider(), GoodProvider()])._call("probe"))
    assert result.provider == "demo"
    assert "attempt=1" in caplog.text and "attempt=2" in caplog.text
    assert "private-receipt-text" not in caplog.text
