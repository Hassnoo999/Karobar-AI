"""Cheap public liveness. Paid provider checks belong to an operator CLI."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.ai import get_adapter
from app.config import settings
from app.db import pkt_today

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(verify: bool = Query(False, description="Deprecated: active checks are operator-only")):
    """Provider configuration is not proof of provider availability."""
    if verify:
        raise HTTPException(status_code=403, detail="Active provider checks are disabled on HTTP. Use python -m scripts.check_providers on the backend host.")
    payload: dict[str, object] = {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.environment,
        "today": pkt_today().isoformat(),
        "provider_chain": get_adapter().chain_names(),
        "providers": None,
    }
    return payload
