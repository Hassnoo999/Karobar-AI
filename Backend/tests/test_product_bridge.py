"""Focused regression gates for the regional-round UI's data boundary."""
from datetime import timedelta

import pytest

from app.db import pkt_today
from app.models import BusinessEvent
from app.routers.bridge import _combined_cache, _draft_to_fe_event
from app.schemas.capture import DraftEvent
from app.schemas.events import SourceType


@pytest.fixture(autouse=True)
def isolate_product_cache():
    _combined_cache.clear()
    yield
    _combined_cache.clear()


def payload(**changes):
    return {"event_type": "sale", "amount": "23.45", "date": pkt_today().isoformat(),
            "source": "manual", "confidence": None, **changes}


@pytest.mark.parametrize("changes", [
    {"event_type": "not-a-real-event"}, {"amount": "abc"}, {"amount": None},
    {"amount": 0}, {"amount": -1}, {"amount": "NaN"}, {"amount": "1.005"},
    {"date": "not-a-date"}, {"date": None}, {"source": "invented"},
    {"confidence": 1.1},
])
def test_bridge_rejects_invalid_inputs_without_writing(client, changes):
    response = client.post("/api/ledger/events", json=payload(**changes))
    assert response.status_code == 422
    assert client.get("/api/events").json()["total"] == 0


def test_bridge_exact_money_and_honest_source(client):
    response = client.post("/api/ledger/events", json=payload(confidence=0))
    assert response.status_code == 201
    event = response.json()
    assert event["source"] == "manual"
    assert event["confidence"] == 0
    canonical = client.get(f"/api/events/{event['id']}").json()
    assert canonical["amount_paisa"] == 2345
    assert canonical["ai_confidence"] == 0


def test_unknown_draft_is_not_silently_a_sale():
    draft = DraftEvent(provider="demo", source_type=SourceType.voice, confidence=0,
                       possible_duplicate=True, duplicate_of=7, notes="Check the amount")
    event = _draft_to_fe_event(draft)
    assert event["event_type"] is None
    assert event["date"] is None
    assert event["confidence"] == 0
    assert event["ai_provider"] == "demo"
    assert event["possible_duplicate"] is True
    assert event["duplicate_of"] == 7
    assert event["notes"] == "Check the amount"


def test_full_history_customer_balance_survives_200_row_limit(client, db):
    yesterday = (pkt_today() - timedelta(days=1)).isoformat()
    client.post("/api/ledger/events", json=payload(event_type="credit_given", amount=5000,
                customer_name="Naveed", date=yesterday))
    client.post("/api/ledger/events", json=payload(event_type="credit_received", amount=2000,
                customer_name="Naveed", date=yesterday))
    db.add_all([BusinessEvent(merchant_id="demo", event_type="cash_sale", amount_paisa=100,
                occurred_at=pkt_today(), payment_status="paid", source_type="manual",
                verification_status="confirmed", settled_paisa=0) for _ in range(205)])
    db.commit()
    snapshot = client.get("/api/combined").json()
    assert len(snapshot["events"]) == 200
    assert snapshot["summary"]["record_count"] == 207
    assert snapshot["customers"][0]["outstanding_paisa"] == 300000
    assert snapshot["customers"][0]["event_count"] == 2
    assert snapshot["summary"]["total_receivables"] == 3000
    assert snapshot["passport"]["recovery_rate_pct"] == 40
    assert snapshot["source_counts"]["manual"] == 207
    assert client.get("/api/customers").json()["customers"][0]["outstanding_paisa"] == 300000


def test_canonical_mutations_invalidate_snapshot(client):
    assert client.get("/api/combined").json()["summary"]["record_count"] == 0
    response = client.post("/api/events", json={"event_type":"cash_sale", "amount_paisa":100,
                "occurred_at":pkt_today().isoformat(), "source_type":"manual"})
    event_id = response.json()["id"]
    assert client.get("/api/combined").json()["summary"]["record_count"] == 1
    client.patch(f"/api/events/{event_id}", json={"amount_paisa":200})
    assert client.get("/api/combined").json()["summary"]["total_sales"] == 2
    client.delete(f"/api/events/{event_id}")
    assert client.get("/api/combined").json()["summary"]["record_count"] == 0
    assert client.post("/api/demo/seed").status_code == 404
    assert client.post("/api/demo/reset").status_code == 404
    assert client.get("/api/combined").json()["summary"]["record_count"] == 0


def test_offline_fixture_remains_truthfully_labelled(seeded_client):
    seeded = seeded_client.get("/api/combined").json()
    assert seeded["summary"]["record_count"] == 63
    assert seeded["source_counts"]["seed"] == 63
    assert all(event["source"] == "seed" and event["confidence"] is None for event in seeded["events"])
