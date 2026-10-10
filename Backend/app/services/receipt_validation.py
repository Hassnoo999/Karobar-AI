"""Reject corrupt or unsupported photos before storage and paid recognition."""
import io
import warnings

from PIL import Image
from app.errors import DomainValidationError


def validate_receipt_image(image: bytes, mime: str) -> None:
    if mime in {"image/heic", "image/heif"}:
        raise DomainValidationError("This server cannot read HEIC photos yet. Export the receipt as JPEG, PNG or WebP and try again. No entry was saved.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(image)) as photo:
                expected = {"image/jpeg": "JPEG", "image/jpg": "JPEG", "image/png": "PNG", "image/webp": "WEBP"}
                if photo.format != expected.get(mime):
                    raise ValueError("photo format does not match content type")
                if photo.width * photo.height > 25_000_000:
                    raise ValueError("oversized photo")
                photo.load()
    except (OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise DomainValidationError("This file could not be opened as a supported receipt photo. Choose a valid JPEG, PNG or WebP (up to 25 megapixels) and try again. No entry was saved.") from exc
