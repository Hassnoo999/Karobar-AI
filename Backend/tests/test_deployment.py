"""Release gates: fail-closed config, private OIDC receipt paths, upload caps."""
import json
import os
from pathlib import Path
import subprocess
import sys

import httpx
import pytest

from app.config import Settings, settings
from app.deployment import validate_deployment
from app.errors import NotFoundError, StorageUnavailableError
from app.services import blob_receipts
from app.services.evidence_storage import assert_receipt_owned, read_receipt, store_receipt
from tests.test_capture_api import PNG_BYTES
from tests.test_evidence_security import confirm, identity


def production(**overrides):
    values = dict(_env_file=None, environment="production", require_auth=True,
        database_url="postgresql://test.invalid/db", supabase_url="https://test.supabase.co",
        auto_seed=False, receipt_storage="vercel_blob", blob_store_id="store_test12345678")
    return Settings(**(values | overrides))


@pytest.mark.parametrize("override", [{"require_auth": False}, {"database_url": "sqlite:///test.db"},
    {"auto_seed": True}, {"receipt_storage": "local"}, {"blob_store_id": ""}, {"supabase_url": ""}, {"cors_origins": "*"}])
def test_production_cannot_publish_development_defaults(override):
    with pytest.raises(RuntimeError, match="Unsafe deployment"):
        validate_deployment(production(**override))


def test_valid_production_and_local_config():
    validate_deployment(production())
    validate_deployment(Settings(_env_file=None, environment="development"))


def test_cloud_database_verifies_certificate_and_bounds_connect():
    from pathlib import Path
    from app.db import managed_connect_args
    options = managed_connect_args()
    assert options["sslmode"] == "verify-full"
    assert options["connect_timeout"] == 12
    assert Path(options["sslrootcert"]).is_file()


def test_empty_cors_is_not_a_public_wildcard():
    assert Settings(_env_file=None, cors_origins="").cors_origins_list == []


def test_vercel_flag_enforces_production_guard(monkeypatch):
    monkeypatch.setenv("VERCEL", "1")
    with pytest.raises(RuntimeError):
        validate_deployment(Settings(_env_file=None, require_auth=False, auto_seed=True))


def test_serverless_import_cannot_skip_release_guard(tmp_path):
    env = os.environ | {"PYTHONPATH": str(Path(__file__).resolve().parents[1]), "VERCEL": "1",
        "ENVIRONMENT": "production", "REQUIRE_AUTH": "false", "AUTO_SEED": "true",
        "DATABASE_URL": "sqlite:///should-not-exist.db", "RECEIPT_STORAGE": "local"}
    result = subprocess.run([sys.executable, "-c", "import app.main"], cwd=tmp_path,
        env=env, capture_output=True, text=True, timeout=20)
    assert result.returncode != 0
    assert "Unsafe deployment configuration" in result.stderr
    assert not (tmp_path / "should-not-exist.db").exists()


@pytest.mark.parametrize("route", ["/api/capture/transcribe", "/api/understand/voice", "/api/actions/reminder/draft",
    "/api/capture/extract-receipt", "/api/understand/receipt"])
def test_upload_over_hosted_limit_is_rejected_before_paid_call(client, monkeypatch, route):
    def no_paid_calls():
        raise AssertionError("oversize uploads must not call a provider")
    monkeypatch.setattr("app.routers.bridge.get_adapter", no_paid_calls)
    monkeypatch.setattr("app.routers.capture.get_adapter", no_paid_calls)
    mime = "image/png" if "receipt" in route else "audio/webm"
    response = client.post(route, files={"file": ("file.png", b"x" * (4 * 1024 * 1024 + 1), mime)})
    assert response.status_code == 422
    assert "4 MB" in response.text


def test_api_responses_never_enter_shared_cache(client):
    response = client.get("/api/combined")
    assert response.headers["cache-control"] == "private, no-store"
    assert response.headers["x-content-type-options"] == "nosniff"


@pytest.mark.parametrize("route", ["/api/demo/seed", "/api/demo/reset"])
def test_deployed_demo_controls_cannot_change_ledger(seeded_client, monkeypatch, route):
    monkeypatch.setattr(settings, "environment", "production")
    assert seeded_client.post(route).status_code == 403
    assert seeded_client.get("/api/combined").json()["summary"]["record_count"] == 63


def test_cloud_skips_stale_process_snapshot(seeded_client, monkeypatch):
    from app.routers.bridge import _combined_cache
    _combined_cache["demo"] = (float("inf"), {"stale": True})
    monkeypatch.setattr(settings, "environment", "production")
    result = seeded_client.get("/api/combined").json()
    assert "stale" not in result
    assert result["summary"]["record_count"] == 63
    _combined_cache.clear()


@pytest.fixture()
def blob_mock(monkeypatch):
    monkeypatch.setattr(settings, "receipt_storage", "vercel_blob")
    monkeypatch.setattr(settings, "blob_store_id", "store_test12345678")
    monkeypatch.setattr(blob_receipts, "get_vercel_oidc_token", lambda: "fixture-oidc")
    objects = {}
    requests = []
    def transport(request):
        requests.append(request)
        assert request.headers["authorization"] == "Bearer fixture-oidc"
        if request.method == "PUT":
            assert request.headers["x-vercel-blob-access"] == "private"
            assert request.headers["x-allow-overwrite"] == "0"
            key = request.url.params["pathname"]
            assert key not in objects
            objects[key] = request.content
            return httpx.Response(200, json={"pathname": key})
        if request.method == "POST":
            for key in json.loads(request.content)["urls"]:
                objects.pop(key, None)
            return httpx.Response(200, json={})
        key = request.url.params.get("url") or request.url.path.lstrip("/")
        if key not in objects:
            return httpx.Response(404)
        return httpx.Response(200, json={"pathname": key}) if request.url.host == "blob.vercel-storage.com" else httpx.Response(200, content=objects[key])
    actual_client = httpx.Client
    monkeypatch.setattr(blob_receipts.httpx, "Client", lambda **kwargs: actual_client(transport=httpx.MockTransport(transport), **kwargs))
    return objects, requests


def test_cloud_receipts_owned_before_confirm_and_survive_new_client(blob_mock):
    objects, requests = blob_mock
    filename = store_receipt(PNG_BYTES, ".png", "merchant-a")
    assert_receipt_owned(filename, "merchant-a")
    assert read_receipt(filename, "merchant-a") == PNG_BYTES
    with pytest.raises(NotFoundError):
        assert_receipt_owned(filename, "merchant-b")
    with pytest.raises(NotFoundError):
        read_receipt(filename, "merchant-b")
    assert len(objects) == 1
    assert all("merchant-a" not in str(request.url) for request in requests)
    assert requests[0].headers["x-vercel-blob-store-id"] == "test12345678"


def test_cloud_failed_extraction_discards_only_own_object(blob_mock):
    from app.services.evidence_storage import discard_receipt
    store_receipt(PNG_BYTES, ".png", "merchant-b")
    filename = store_receipt(PNG_BYTES, ".png", "merchant-a")
    discard_receipt(filename, "merchant-a")
    assert len(blob_mock[0]) == 1


def test_cloud_credentials_failure_does_not_write_locally(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "receipt_storage", "vercel_blob")
    monkeypatch.setattr(settings, "uploads_dir_path", str(tmp_path))
    monkeypatch.setattr(blob_receipts, "get_vercel_oidc_token", lambda: (_ for _ in ()).throw(RuntimeError("SECRET-DO-NOT-LEAK")))
    with pytest.raises(StorageUnavailableError) as exc:
        store_receipt(PNG_BYTES, ".png", "demo")
    assert "SECRET" not in str(exc.value)
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("upload_route", ["/api/capture/extract-receipt", "/api/understand/receipt"])
@pytest.mark.parametrize("confirm_route", ["/api/events", "/api/ledger/events"])
def test_cloud_upload_confirm_read_boundary(client, db, blob_mock, upload_route, confirm_route):
    identity("merchant-a")
    response = client.post(upload_route, files={"file": ("receipt.png", PNG_BYTES, "image/png")})
    assert response.status_code == 200
    body = response.json()
    filename = body.get("event", body)["evidence_filename"]
    url = f"/api/evidence/files/{filename}"
    assert client.get(url).status_code == 404
    identity("merchant-b")
    assert confirm(client, filename, confirm_route).status_code == 404
    identity("merchant-a")
    assert confirm(client, filename, confirm_route).status_code == 201
    result = client.get(url)
    assert result.status_code == 200
    assert result.content == PNG_BYTES
    assert result.headers["cache-control"] == "private, no-store"
    identity("merchant-b")
    assert client.get(url).status_code == 404


def test_provider_failures_never_echo_credentials(client, monkeypatch):
    from app.ai.base import ProviderError
    class Unavailable:
        async def extract_event_from_text(self, *args):
            raise ProviderError("Bearer SECRET-DO-NOT-LEAK")
    monkeypatch.setattr("app.routers.capture.get_adapter", lambda: Unavailable())
    response = client.post("/api/capture/extract", json={"text": "Naveed udhaar 5000"})
    assert response.status_code == 503
    assert "SECRET" not in response.text
    assert "manually" in response.text


@pytest.mark.parametrize("body", [b"invalid", b"[]"])
def test_blob_invalid_metadata_is_a_safe_failure(body):
    with pytest.raises(StorageUnavailableError):
        blob_receipts._metadata(httpx.Response(200, content=body))
