"""Demo data controls: load the deterministic seed dataset or wipe the ledger."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from app.config import settings
from sqlalchemy.orm import Session

from app.auth import get_merchant_id
from app.data.seed import load_seed
from app.db import get_db
from app.models import BusinessEvent, Customer
from app.services.product_cache import invalidate_product_cache

router = APIRouter(prefix="/demo", tags=["demo"])


def require_local_demo() -> None:
    if settings.deployed:
        raise HTTPException(403, "Seed/reset controls are disabled on deployed environments")


@router.post("/seed", dependencies=[Depends(require_local_demo)])
def seed(db: Session = Depends(get_db), merchant_id: str = Depends(get_merchant_id)):
    counts = load_seed(db, merchant_id=merchant_id)
    invalidate_product_cache(merchant_id)
    return {"status": "seeded", **counts}


@router.post("/reset", dependencies=[Depends(require_local_demo)])
def reset(db: Session = Depends(get_db), merchant_id: str = Depends(get_merchant_id)):
    db.query(BusinessEvent).filter(BusinessEvent.merchant_id == merchant_id).delete()
    db.query(Customer).filter(Customer.merchant_id == merchant_id).delete()
    db.commit()
    invalidate_product_cache(merchant_id)
    return {"status": "reset", "customers": 0, "events": 0}
