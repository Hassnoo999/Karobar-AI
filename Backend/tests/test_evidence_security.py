"""Regression gates for upload-time ownership and no public paid health calls."""
import pytest

from app.auth import get_merchant_id
from app.config import settings
from app.db import pkt_today
from app.main import app
from app.models import BusinessEvent, Customer
from app.services.evidence_storage import register_existing_receipt
from tests.test_capture_api import PNG_BYTES


@pytest.fixture(autouse=True)
def private_upload_dir(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "uploads_dir_path", str(tmp_path))


def identity(merchant):
    app.dependency_overrides[get_merchant_id] = lambda: merchant


def confirm(client, filename, route="/api/events"):
    payload = {"event_type": "credit_sale", "amount_paisa": 12300,
               "counterparty": "Security fixture", "occurred_at": pkt_today().isoformat(),
               "source_type": "receipt", "evidence_filename": filename}
    if route == "/api/ledger/events":
        payload = {"event_type": "credit_given", "amount": 123,
                   "customer_name": "Security fixture", "date": pkt_today().isoformat(),
                   "source": "photo", "evidence_filename": filename}
    return client.post(route, json=payload)


@pytest.mark.parametrize("upload_route", ["/api/capture/extract-receipt", "/api/understand/receipt"])
@pytest.mark.parametrize("confirm_route", ["/api/events", "/api/ledger/events"])
def test_other_merchant_cannot_claim_receipt_even_before_owner_confirms(client, db, upload_route, confirm_route):
    identity("merchant-a")
    upload = client.post(upload_route, files={"file": ("receipt.png", PNG_BYTES, "image/png")})
    assert upload.status_code == 200
    body = upload.json()
    filename = body.get("event", body)["evidence_filename"]
    url = f"/api/evidence/files/{filename}"
    assert client.get(url).status_code == 404  # still only a draft
    identity("merchant-b")
    assert confirm(client, filename, confirm_route).status_code == 404
    assert db.query(Customer).count() == 0
    assert db.query(BusinessEvent).count() == 0
    identity("merchant-a")
    assert confirm(client, filename, confirm_route).status_code == 201
    assert client.get(url).content == PNG_BYTES
    identity("merchant-b")
    assert client.get(url).status_code == 404
    assert confirm(client, filename, confirm_route).status_code == 404
    assert db.query(BusinessEvent).count() == 1


@pytest.mark.parametrize("filename", ["../receipt.png", "..\\receipt.png", "missing.png", "a" * 32 + ".png", ""])
def test_untrusted_filename_cannot_create_an_event(client, db, filename):
    assert confirm(client, filename).status_code == 404
    assert db.query(Customer).count() == 0
    assert db.query(BusinessEvent).count() == 0


def test_legacy_ledger_claim_is_not_upload_ownership(client, db):
    filename = "a" * 32 + ".png"
    path = settings.uploads_dir / filename
    path.write_bytes(PNG_BYTES)
    db.add(BusinessEvent(merchant_id="demo", event_type="expense", amount_paisa=12300,
        occurred_at=pkt_today(), payment_status="paid", source_type="receipt",
        verification_status="confirmed", evidence_filename=filename))
    db.commit()
    assert client.get(f"/api/evidence/files/{filename}").status_code == 404
    assert confirm(client, filename).status_code == 404
    assert path.exists()  # inaccessible does not mean deleted
    register_existing_receipt(filename, "demo")  # explicit trusted operator action
    assert client.get(f"/api/evidence/files/{filename}").content == PNG_BYTES
    with pytest.raises(FileExistsError):
        register_existing_receipt(filename, "merchant-b")


def test_forged_row_cannot_override_registered_owner(client, db):
    identity("merchant-a")
    body = client.post("/api/capture/extract-receipt", files={"file": ("r.png", PNG_BYTES, "image/png")}).json()
    filename = body["evidence_filename"]
    db.add(BusinessEvent(merchant_id="merchant-b", event_type="expense", amount_paisa=12300,
        occurred_at=pkt_today(), payment_status="paid", source_type="receipt",
        verification_status="confirmed", evidence_filename=filename))
    db.commit()
    identity("merchant-b")
    assert client.get(f"/api/evidence/files/{filename}").status_code == 404


@pytest.mark.parametrize("route", ["/api/capture/extract-receipt", "/api/understand/receipt"])
def test_failed_extraction_cleans_up_current_upload(client, monkeypatch, route):
    from app.ai.base import ProviderError
    class Unavailable:
        async def extract_event_from_image(self, *args):
            raise ProviderError("fixture failure")
    target = "capture" if "capture" in route else "bridge"
    monkeypatch.setattr(f"app.routers.{target}.get_adapter", lambda: Unavailable())
    assert client.post(route, files={"file": ("r.png", PNG_BYTES, "image/png")}).status_code == 503
    assert list(settings.uploads_dir.glob("*.png")) == []
    assert list((settings.uploads_dir / ".owners").glob("*.json")) == []


def test_public_health_never_calls_paid_providers(client, monkeypatch):
    class NoPaidCalls:
        def chain_names(self):
            return ["fixture"]
        @property
        def providers(self):
            raise AssertionError("Public health must not ping providers")
    monkeypatch.setattr("app.routers.health.get_adapter", lambda: NoPaidCalls())
    assert client.get("/api/health").json()["provider_chain"] == ["fixture"]
    assert client.get("/api/health?verify=true").status_code == 403
