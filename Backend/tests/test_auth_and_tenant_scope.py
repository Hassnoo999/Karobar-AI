"""Security regression tests for JWT verification and merchant isolation."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.auth import get_merchant_id
from app.config import settings
from app.errors import NotFoundError
from app.models import Customer
from app.schemas.events import EventCreate, EventType, EventUpdate
from app.services.ledger import confirm_event, delete_event, update_event


def _credentials(secret: str, subject: str) -> HTTPAuthorizationCredentials:
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {
            "sub": subject,
            "aud": "authenticated",
            "iss": "https://example.supabase.co/auth/v1",
            "iat": now,
            "exp": now + timedelta(minutes=10),
        },
        secret,
        algorithm="HS256",
    )
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


def test_auth_accepts_valid_signed_supabase_token(monkeypatch):
    subject = "9fb3d594-2dd4-4e4b-8c71-c849bfb9c001"
    secret = "test-signing-secret-with-enough-entropy"
    monkeypatch.setattr(settings, "require_auth", True)
    monkeypatch.setattr(settings, "supabase_url", "https://example.supabase.co")
    monkeypatch.setattr(settings, "supabase_jwt_secret", secret)

    assert get_merchant_id(_credentials(secret, subject)) == subject


def test_auth_rejects_forged_supabase_token(monkeypatch):
    subject = "9fb3d594-2dd4-4e4b-8c71-c849bfb9c001"
    monkeypatch.setattr(settings, "require_auth", True)
    monkeypatch.setattr(settings, "supabase_url", "https://example.supabase.co")
    monkeypatch.setattr(settings, "supabase_jwt_secret", "trusted-secret-that-is-at-least-32-bytes")

    with pytest.raises(HTTPException) as exc_info:
        get_merchant_id(_credentials("attacker-secret-that-is-at-least-32-bytes", subject))

    assert exc_info.value.status_code == 401


def test_event_mutations_cannot_cross_merchant_boundary(db):
    owner = "11111111-1111-4111-8111-111111111111"
    attacker = "22222222-2222-4222-8222-222222222222"
    customer = Customer(
        merchant_id=owner,
        name_normalized="ahmed",
        display_name="Ahmed",
    )
    db.add(customer)
    db.commit()

    event, _ = confirm_event(
        db,
        EventCreate(
            event_type=EventType.credit_sale,
            customer_id=customer.id,
            amount_paisa=500_000,
            occurred_at=datetime.now(timezone.utc).date(),
        ),
        merchant_id=owner,
    )

    with pytest.raises(NotFoundError):
        update_event(db, event.id, EventUpdate(amount_paisa=1), merchant_id=attacker)
    with pytest.raises(NotFoundError):
        delete_event(db, event.id, merchant_id=attacker)
    with pytest.raises(NotFoundError):
        confirm_event(
            db,
            EventCreate(
                event_type=EventType.credit_sale,
                customer_id=customer.id,
                amount_paisa=100,
                occurred_at=datetime.now(timezone.utc).date(),
            ),
            merchant_id=attacker,
        )
