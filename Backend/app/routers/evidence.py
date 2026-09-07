"""Financial Evidence Passport and protected receipt evidence endpoints."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.auth import get_merchant_id
from app.config import settings
from app.db import get_db
from app.errors import NotFoundError
from app.models import BusinessEvent
from app.schemas.evidence import PassportResponse
from app.services.passport import compute_passport

router = APIRouter(prefix="/evidence", tags=["evidence"])


@router.get("/passport", response_model=PassportResponse)
async def passport(db: Session = Depends(get_db), merchant_id: str = Depends(get_merchant_id)):
    return compute_passport(db, merchant_id=merchant_id)


@router.get("/files/{filename}", response_class=FileResponse)
async def receipt_evidence(
    filename: str,
    db: Session = Depends(get_db),
    merchant_id: str = Depends(get_merchant_id),
):
    """Return receipt evidence only when it belongs to the authenticated merchant."""
    safe_name = Path(filename).name
    if safe_name != filename:
        raise NotFoundError("evidence file not found")

    owned = (
        db.query(BusinessEvent.id)
        .filter(
            BusinessEvent.merchant_id == merchant_id,
            BusinessEvent.evidence_filename == safe_name,
        )
        .first()
    )
    path = settings.uploads_dir / safe_name
    if owned is None or not path.is_file():
        raise NotFoundError("evidence file not found")
    return FileResponse(path)
