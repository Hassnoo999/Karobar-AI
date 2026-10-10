"""Small private Blob transport using Vercel's request-scoped OIDC credentials.

The published Python Blob SDK (0.11.6) only supports long-lived RW tokens.
This transport follows the official vercel/storage API v12 protocol instead:
api.ts, put-helpers.ts, get.ts and del.ts. Never accept client URLs or tokens.
"""
from __future__ import annotations

import hashlib
import logging
import re

import httpx
from vercel.oidc import get_vercel_oidc_token

from app.config import settings
from app.errors import NotFoundError, StorageUnavailableError

logger = logging.getLogger(__name__)
_API = "https://blob.vercel-storage.com"


def _store_id() -> str:
    value = settings.blob_store_id.removeprefix("store_")
    if not re.fullmatch(r"[A-Za-z0-9]{8,64}", value):
        raise StorageUnavailableError("Private receipt storage is not configured")
    return value


def receipt_key(filename: str, merchant_id: str) -> str:
    # Ownership is recorded in the immutable namespace selected by the server,
    # not a ledger row or a mutable file supplied by the uploader.
    owner = hashlib.sha256(merchant_id.encode("utf-8")).hexdigest()
    return f"receipts/{owner}/{filename}"


def _request(method: str, url: str, **kwargs) -> httpx.Response:
    try:
        headers = {"authorization": f"Bearer {get_vercel_oidc_token()}",
                   "x-vercel-blob-store-id": _store_id(), "x-api-version": "12"}
        headers.update(kwargs.pop("headers", {}))
        with httpx.Client(timeout=30, follow_redirects=False) as client:
            response = client.request(method, url, headers=headers, **kwargs)
        if response.status_code == 404:
            raise NotFoundError("evidence file not found")
        response.raise_for_status()
        return response
    except NotFoundError:
        raise
    except Exception as exc:
        # Neither URLs, OIDC credentials nor upstream response bodies enter logs.
        logger.warning("Private receipt operation unavailable (%s)", type(exc).__name__)
        raise StorageUnavailableError("Private receipt storage is temporarily unavailable. Please try again.") from exc


def _metadata(response: httpx.Response) -> dict:
    try:
        result = response.json()
        if not isinstance(result, dict):
            raise ValueError("invalid metadata")
        return result
    except ValueError as exc:
        raise StorageUnavailableError("Private receipt storage returned an unexpected result") from exc


def store(image: bytes, filename: str, merchant_id: str, mime: str) -> None:
    key = receipt_key(filename, merchant_id)
    response = _request("PUT", _API + "/", params={"pathname": key}, content=image,
        headers={"x-vercel-blob-access": "private", "x-content-type": mime,
                 "x-add-random-suffix": "0", "x-allow-overwrite": "0"})
    if _metadata(response).get("pathname") != key:
        raise StorageUnavailableError("Private receipt storage returned an unexpected result")


def assert_owned(filename: str, merchant_id: str) -> None:
    key = receipt_key(filename, merchant_id)
    response = _request("GET", _API + "/", params={"url": key})
    if _metadata(response).get("pathname") != key:
        raise NotFoundError("evidence file not found")


def read(filename: str, merchant_id: str) -> bytes:
    key = receipt_key(filename, merchant_id)
    # Host and pathname are constructed solely from validated server settings.
    url = f"https://{_store_id()}.private.blob.vercel-storage.com/{key}"
    return _request("GET", url).content


def discard(filename: str, merchant_id: str) -> None:
    _request("POST", _API + "/delete", json={"urls": [receipt_key(filename, merchant_id)]})
