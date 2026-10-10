"""Operator-only paid provider checks: python -m scripts.check_providers."""
import asyncio

from app.ai import get_adapter


async def main() -> int:
    failed = False
    for provider in get_adapter().providers:
        try:
            await provider.ping()
            print(f"{provider.name}: ok")
        except Exception as exc:
            # Provider responses can contain credentials or request details.
            print(f"{provider.name}: unavailable ({type(exc).__name__})")
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
