"""Cloud regression: overlapping requests must reuse a one-connection pool.

Separate sessions, a file-backed SQLite QueuePool, and one event loop model the
failure a shared StaticPool/TestClient fixture cannot expose. No live DB or keys.
"""
import asyncio
from types import SimpleNamespace

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from starlette.concurrency import run_in_threadpool

from app.auth import get_merchant_id
from app.config import settings
from app.db import Base, get_db
from app.routers import ALL_ROUTERS
from app.routers import bridge, evidence, reminders


@pytest.fixture()
def small_pool_app(tmp_path, monkeypatch):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'concurrency.db'}",
        connect_args={"check_same_thread": False},
        pool_size=1, max_overflow=0, pool_timeout=0.25,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)

    async def isolated_session():
        session = factory()
        try:
            yield session
        finally:
            await run_in_threadpool(session.close)

    app = FastAPI()
    for router in ALL_ROUTERS:
        app.include_router(router, prefix="/api")
    app.dependency_overrides[get_db] = isolated_session
    app.dependency_overrides[get_merchant_id] = lambda: "concurrency-test"
    monkeypatch.setattr(settings, "environment", "production")  # no local cache
    try:
        yield app, engine
    finally:
        engine.dispose()


@pytest.mark.parametrize("path", [
    "/api/combined", "/api/ledger/events", "/api/ledger/summary",
    "/api/intelligence", "/api/dashboard", "/api/evidence/passport",
    "/api/customers", "/api/events", "/api/financing/readiness", "/api/ask",
])
def test_overlapping_ledger_requests_return_connections(small_pool_app, path):
    app, engine = small_pool_app

    async def burst():
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            async def request():
                if path == "/api/ask":
                    return await client.post(path, json={"question": "Total udhaar kitna hai?"})
                return await client.get(path)
            return await asyncio.gather(*(request() for _ in range(4)))

    responses = asyncio.run(burst())
    assert [response.status_code for response in responses] == [200] * 4
    assert engine.pool.checkedout() == 0


@pytest.mark.parametrize("voice", [False, True])
def test_reminder_ai_wait_does_not_hold_database_connection(small_pool_app, monkeypatch, voice):
    app, engine = small_pool_app

    async def story():
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            sale = await client.post("/api/ledger/events", json={
                "event_type": "credit_given", "amount": 5000,
                "date": bridge.pkt_today().isoformat(), "source": "manual",
                "customer_name": "Naveed",
            })
            assert sale.status_code == 201

            class WaitingAdapter:
                async def transcribe_audio(self, *args):
                    return SimpleNamespace(text="Naveed ko reminder bhejo", provider="test")

                async def draft_reminder(self, name, outstanding, oldest, **kwargs):
                    assert name == "Naveed" and outstanding == 500000
                    assert engine.pool.checkedout() == 0
                    # Another request must work while the provider is pending.
                    response = await client.get("/api/combined")
                    assert response.status_code == 200
                    assert response.json()["summary"]["total_receivables"] == 5000
                    return SimpleNamespace(text="Please review this test reminder.", provider="test")

            adapter = WaitingAdapter()
            monkeypatch.setattr(bridge, "get_adapter", lambda: adapter)
            monkeypatch.setattr(reminders, "get_adapter", lambda: adapter)
            if voice:
                response = await client.post("/api/actions/reminder/draft", files={
                    "file": ("test.wav", b"synthetic test audio", "audio/wav"),
                })
                assert response.json()["balance"]["receivable_balance"] == 5000
            else:
                response = await client.post("/api/reminders/draft", json={
                    "customer_id": sale.json()["customer_id"], "tone": "friendly",
                })
                assert response.json()["outstanding_paisa"] == 500000
            assert response.status_code == 200

    asyncio.run(story())
    assert engine.pool.checkedout() == 0


def test_receipt_download_does_not_hold_database_connection(small_pool_app, monkeypatch):
    app, engine = small_pool_app
    from app.models import BusinessEvent
    from app.db import pkt_today
    from sqlalchemy.orm import Session

    with Session(engine) as session:
        session.add(BusinessEvent(
            merchant_id="concurrency-test", event_type="cash_sale", amount_paisa=50000,
            occurred_at=pkt_today(), source_type="receipt", payment_status="paid",
            verification_status="confirmed", evidence_filename="test.png",
        ))
        session.commit()

    def download(filename, merchant_id):
        assert filename == "test.png" and merchant_id == "concurrency-test"
        assert engine.pool.checkedout() == 0
        return b"synthetic image"

    monkeypatch.setattr(evidence, "read_receipt", download)

    async def read():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/evidence/files/test.png")
            assert response.status_code == 200
            assert response.content == b"synthetic image"

    asyncio.run(read())
    assert engine.pool.checkedout() == 0
