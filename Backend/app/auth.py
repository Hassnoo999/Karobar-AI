"""Authentication and merchant scoping.

Two modes controlled by REQUIRE_AUTH (default False for development):

- **REQUIRE_AUTH=false** (dev/demo): every request is treated as the "demo"
  merchant.  No token is checked.  The seed data and all queries are scoped to
  merchant_id="demo", so the app works exactly as before.

- **REQUIRE_AUTH=true** (production): every request must carry
  ``Authorization: Bearer <supabase-jwt>``.  The JWT signature, issuer,
  audience, and expiry are verified before ``sub`` becomes the merchant_id.
"""
from __future__ import annotations

import logging
from functools import lru_cache

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings

logger = logging.getLogger(__name__)

_bearer_scheme = HTTPBearer(auto_error=False)

DEMO_MERCHANT = "demo"


@lru_cache(maxsize=1)
def _supabase_jwk_client() -> jwt.PyJWKClient:
    if not settings.supabase_url:
        raise RuntimeError("SUPABASE_URL is required for asymmetric JWT verification")
    jwks_url = f"{settings.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
    return jwt.PyJWKClient(jwks_url, cache_keys=True)


def _decode_supabase_token(token: str) -> dict:
    """Verify a Supabase access token and return its trusted claims."""
    try:
        header = jwt.get_unverified_header(token)
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token") from exc

    algorithm = header.get("alg")
    issuer = f"{settings.supabase_url.rstrip('/')}/auth/v1" if settings.supabase_url else None
    decode_kwargs = {
        "audience": "authenticated",
        "issuer": issuer,
        "options": {"require": ["exp", "sub", "aud"]},
    }

    try:
        if algorithm == "HS256":
            if not settings.supabase_jwt_secret:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Authentication verification is not configured",
                )
            return jwt.decode(token, settings.supabase_jwt_secret, algorithms=["HS256"], **decode_kwargs)

        if algorithm in {"RS256", "ES256"}:
            signing_key = _supabase_jwk_client().get_signing_key_from_jwt(token).key
            return jwt.decode(token, signing_key, algorithms=[algorithm], **decode_kwargs)

        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unsupported authentication token")
    except HTTPException:
        raise
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired") from exc
    except jwt.InvalidTokenError as exc:
        logger.info("Rejected invalid Supabase JWT: %s", exc)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token") from exc
    except Exception as exc:
        logger.warning("Supabase JWT verification unavailable: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication verification is temporarily unavailable",
        ) from exc


def get_merchant_id(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> str:
    """Return the merchant_id for the current request.

    When REQUIRE_AUTH is off, always returns "demo".
    When on, decodes the Supabase JWT locally (instant — no network round-trip)
    and returns the ``sub`` claim (user UUID) as merchant_id.
    """
    if not settings.require_auth:
        return DEMO_MERCHANT

    if creds is None or not creds.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = creds.credentials

    payload = _decode_supabase_token(token)

    merchant_id = payload.get("sub")
    if not merchant_id or not isinstance(merchant_id, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing 'sub' claim",
        )

    # Validate it looks like a UUID (Supabase user IDs are UUIDs)
    if len(merchant_id) < 32 or merchant_id.count("-") < 4:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token identity format",
        )

    return merchant_id
