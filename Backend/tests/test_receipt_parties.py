"""Receipt facts survive ambiguous purpose, without guessing or ledger writes."""
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.ai.base import ExtractionResult, normalize_extraction
from app.db import pkt_today
from app.schemas.events import EventType
from tests.test_capture_api import PNG_BYTES


def test_normalization_keeps_parties_without_inventing_customer_or_type():
    result = normalize_extraction({
        "sender_name": "  Test   Sender ", "recipient_name": "Test Receiver",
        "transfer_purpose": " Family & Friends ", "counterparty": None,
        "event_type": None, "amount_rupees": 150,
    })
    assert result.sender_name == "Test Sender"
    assert result.recipient_name == "Test Receiver"
    assert result.transfer_purpose == "Family & Friends"
    assert result.counterparty is None and result.event_type is None
    assert result.amount_rupees == 150


@pytest.mark.parametrize("value", [123, {}, [], "", "x" * 121])
def test_malformed_party_names_are_missing_not_guessed(value):
    result = normalize_extraction({"sender_name": value, "recipient_name": value})
    assert result.sender_name is None and result.recipient_name is None


def test_previous_provider_output_is_backward_compatible():
    result = normalize_extraction({"event_type": "credit_sale", "counterparty": "Naveed", "amount_rupees": 5000})
    assert result.event_type == EventType.credit_sale and result.counterparty == "Naveed"
    assert result.sender_name is None and result.recipient_name is None


def test_receipt_http_draft_keeps_parties_and_does_not_write(client, monkeypatch):
    extraction = ExtractionResult(provider="groq", amount_rupees=150, occurred_at=pkt_today(),
        sender_name="Test Sender", recipient_name="Test Receiver", transfer_purpose="Family & Friends",
        notes="Confirm which party is your business and whether this is a business transaction.")
    adapter = SimpleNamespace(extract_event_from_image=AsyncMock(return_value=extraction))
    monkeypatch.setattr("app.routers.bridge.get_adapter", lambda: adapter)
    response = client.post("/api/understand/receipt", files={"file": ("receipt.png", PNG_BYTES, "image/png")})
    assert response.status_code == 200
    draft = response.json()["event"]
    assert draft["sender_name"] == "Test Sender" and draft["recipient_name"] == "Test Receiver"
    assert draft["transfer_purpose"] == "Family & Friends"
    assert draft["customer_name"] is None and draft["event_type"] is None
    assert client.get("/api/combined").json()["summary"]["record_count"] == 0
    # No ambiguous/personal event can be saved until the merchant chooses a supported type.
    assert client.post("/api/ledger/events", json=draft).status_code == 422
    assert client.get("/api/events").json()["total"] == 0


def test_selected_party_name_survives_confirmation_and_ledger(client):
    response = client.post("/api/ledger/events", json={
        "event_type": "sale", "amount": 150, "date": pkt_today().isoformat(),
        "customer_name": "Test Sender", "source": "manual",
        "sender_name": "Test Sender", "recipient_name": "Test Receiver",
    })
    assert response.status_code == 201
    assert response.json()["customer_name"] == "Test Sender"
    assert client.get("/api/ledger/events").json()[0]["customer_name"] == "Test Sender"


@pytest.mark.parametrize("event_type", list(EventType))
def test_explicit_receipt_business_classification_is_preserved(client, monkeypatch, event_type):
    extraction = ExtractionResult(provider="groq", event_type=event_type,
        counterparty="Explicit Customer", amount_rupees=5000, occurred_at=pkt_today())
    monkeypatch.setattr("app.routers.bridge.get_adapter", lambda: SimpleNamespace(
        extract_event_from_image=AsyncMock(return_value=extraction)))
    draft = client.post("/api/understand/receipt", files={"file": ("receipt.png", PNG_BYTES, "image/png")}).json()["event"]
    expected = {"cash_sale": "sale", "credit_sale": "credit_given", "payment_received": "credit_received", "expense": "expense"}
    assert draft["event_type"] == expected[event_type.value]
    assert draft["customer_name"] == "Explicit Customer"
