"""Financial Evidence Passport and protected receipt evidence endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from starlette.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from app.auth import get_merchant_id
from app.db import get_db
from app.errors import NotFoundError
from app.models import BusinessEvent
from app.schemas.evidence import PassportResponse
from app.services.passport import compute_passport
from app.services.evidence_storage import read_receipt
from pathlib import Path

router = APIRouter(prefix="/evidence", tags=["evidence"])


@router.get("/passport", response_model=PassportResponse)
async def passport(db: Session = Depends(get_db), merchant_id: str = Depends(get_merchant_id)):
    return compute_passport(db, merchant_id=merchant_id)


@router.get("/files/{filename}")
async def receipt_evidence(
    filename: str,
    db: Session = Depends(get_db),
    merchant_id: str = Depends(get_merchant_id),
):
    """Return receipt evidence only when it belongs to the authenticated merchant."""
    owned = (
        db.query(BusinessEvent.id)
        .filter(
            BusinessEvent.merchant_id == merchant_id,
            BusinessEvent.evidence_filename == filename,
        )
        .first()
    )
    if owned is None:
        raise NotFoundError("evidence file not found")
    image = await run_in_threadpool(read_receipt, filename, merchant_id)
    mime = {".jpg": "image/jpeg", ".png": "image/png", ".webp": "image/webp", ".heic": "image/heic", ".heif": "image/heif"}.get(Path(filename).suffix, "application/octet-stream")
    return Response(image, media_type=mime, headers={"Cache-Control": "private, no-store",
        "X-Content-Type-Options": "nosniff", "Content-Disposition": f'inline; filename="{filename}"'})
