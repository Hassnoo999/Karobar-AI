"""Private filesystem receipts with upload-time ownership, not client claims.

The upload directory AND its .owners metadata must live on durable private
storage. Unregistered legacy files are deliberately inaccessible until an
operator explicitly assigns their owner; ledger references are not proof.
"""
from __future__ import annotations

import json
import re
import uuid
from pathlib import Path

from app.config import settings
from app.errors import NotFoundError

_NAME = re.compile(r"[a-f0-9]{32}\.(?:jpg|png|webp|heic|heif)")
_EXTENSIONS = {".jpg", ".png", ".webp", ".heic", ".heif"}
_MIMES = {".jpg": "image/jpeg", ".png": "image/png", ".webp": "image/webp", ".heic": "image/heic", ".heif": "image/heif"}


def _validate(filename: str, merchant_id: str) -> None:
    if not _NAME.fullmatch(filename) or not merchant_id.strip():
        raise NotFoundError("evidence file not found")


def assert_receipt_owned(filename: str, merchant_id: str) -> None:
    _validate(filename, merchant_id)
    if settings.receipt_storage == "vercel_blob":
        from app.services import blob_receipts
        blob_receipts.assert_owned(filename, merchant_id)
    else:
        owned_receipt_path(filename, merchant_id)


def read_receipt(filename: str, merchant_id: str) -> bytes:
    _validate(filename, merchant_id)
    if settings.receipt_storage == "vercel_blob":
        from app.services import blob_receipts
        return blob_receipts.read(filename, merchant_id)
    return owned_receipt_path(filename, merchant_id).read_bytes()


def _paths(filename: str) -> tuple[Path, Path]:
    if not _NAME.fullmatch(filename):
        raise NotFoundError("evidence file not found")
    root = settings.uploads_dir
    return root / filename, root / ".owners" / f"{filename}.json"


def owned_receipt_path(filename: str, merchant_id: str) -> Path:
    path, metadata = _paths(filename)
    try:
        if path.is_symlink() or metadata.is_symlink() or not path.is_file():
            raise NotFoundError("evidence file not found")
        owner = json.loads(metadata.read_text(encoding="utf-8"))
        if owner.get("merchant_id") != merchant_id or owner.get("filename") != filename:
            raise NotFoundError("evidence file not found")
    except (OSError, ValueError, AttributeError) as exc:
        raise NotFoundError("evidence file not found") from exc
    return path


def register_existing_receipt(filename: str, merchant_id: str) -> None:
    """Operator-only reassignment of an unregistered file; never an API path."""
    path, metadata = _paths(filename)
    if not merchant_id.strip() or path.is_symlink() or not path.is_file():
        raise NotFoundError("evidence file not found")
    metadata.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation: never replace another merchant's registered owner.
    with metadata.open("x", encoding="utf-8") as output:
        json.dump({"filename": filename, "merchant_id": merchant_id}, output)


def store_receipt(image: bytes, extension: str, merchant_id: str) -> str:
    if extension not in _EXTENSIONS or not merchant_id.strip():
        raise ValueError("invalid receipt storage parameters")
    filename = f"{uuid.uuid4().hex}{extension}"
    if settings.receipt_storage == "vercel_blob":
        from app.services import blob_receipts
        blob_receipts.store(image, filename, merchant_id, _MIMES[extension])
        return filename
    path, _ = _paths(filename)
    with path.open("xb") as output:
        output.write(image)
    try:
        register_existing_receipt(filename, merchant_id)
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return filename


def discard_receipt(filename: str, merchant_id: str) -> None:
    """Remove only the current uploader's failed extraction, including metadata."""
    _validate(filename, merchant_id)
    if settings.receipt_storage == "vercel_blob":
        from app.services import blob_receipts
        blob_receipts.discard(filename, merchant_id)
        return
    path = owned_receipt_path(filename, merchant_id)
    _, metadata = _paths(filename)
    path.unlink(missing_ok=True)
    metadata.unlink(missing_ok=True)
