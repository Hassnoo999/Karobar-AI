"""Database engine, session factory, and Pakistan Standard Time (PKT) helpers.

All "today" decisions in Karobaar are made in Asia/Karachi time (fixed UTC+5,
no DST) so month bucketing and overdue aging always match the merchant's clock.
"""
from __future__ import annotations

from collections.abc import Iterator
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

PKT = timezone(timedelta(hours=5), name="Asia/Karachi")


def managed_connect_args() -> dict:
    """Verify the pooler's certificate and bound connection attempts."""
    # Public Supabase CA downloaded from Database Settings on 10 October 2026.
    # This is a trust certificate, not a private key or application credential.
    return {"connect_timeout": 12, "sslmode": "verify-full",
            "sslrootcert": str(Path(__file__).parent / "certs" / "supabase-root.crt")}


_connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
_pool_kwargs: dict = {}
if not settings.database_url.startswith("sqlite"):
    # Postgres: keep connections alive longer to avoid cold-start latency
    # (Supabase PgBouncer + SSL handshake from Pakistan costs ~4s per cold connection).
    # pool_pre_ping is disabled because PgBouncer already handles liveness,
    # and each pre-ping adds a ~200ms round-trip to Tokyo.
    _pool_kwargs = {
        "pool_size": 5,
        "max_overflow": 10,
        "pool_recycle": 1800,       # 30 min (was 5 min) — avoid frequent cold starts
        "pool_pre_ping": False,     # PgBouncer handles liveness; skip extra round-trip
        "pool_timeout": 30,         # wait up to 30s for a connection
    }
    if settings.deployed:
        _connect_args = managed_connect_args()
        # Keep each short-lived cloud instance's pool small. The managed
        # transaction pooler handles the overall connection fan-out.
        _pool_kwargs.update(pool_size=1, max_overflow=0, pool_pre_ping=True, pool_timeout=12)
engine = create_engine(settings.database_url, connect_args=_connect_args, **_pool_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def pkt_now() -> datetime:
    return datetime.now(PKT)


def pkt_today() -> date:
    return pkt_now().date()


def month_key(d: date) -> str:
    return f"{d.year:04d}-{d.month:02d}"


def month_bounds(month: str) -> tuple[date, date]:
    """First and last calendar day of a 'YYYY-MM' month key."""
    year, mon = int(month[:4]), int(month[5:7])
    if mon == 12:
        return date(year, 12, 1), date(year, 12, 31)
    return date(year, mon, 1), date(year, mon + 1, 1) - timedelta(days=1)


def prev_month_key(month: str) -> str:
    year, mon = int(month[:4]), int(month[5:7])
    mon -= 1
    if mon == 0:
        mon, year = 12, year - 1
    return f"{year:04d}-{mon:02d}"


def months_between(first: date, last: date) -> int:
    return max(0, (last.year - first.year) * 12 + (last.month - first.month))


def month_keys_between(first: date, last: date) -> list[str]:
    keys: list[str] = []
    y, m = first.year, first.month
    for _ in range(months_between(first, last) + 1):
        keys.append(f"{y:04d}-{m:02d}")
        m += 1
        if m == 13:
            m, y = 1, y + 1
    return keys


def init_db() -> None:
    from app import models  # noqa: F401  (registers tables on the metadata)

    Base.metadata.create_all(bind=engine)


def get_db() -> Iterator[Session]:
    """Request-scoped session; execute blocking SQL only in a worker thread.

    Async routes offload their SQL phase and never share a session concurrently.
    Read-only AI/Blob routes release their transaction before network waits.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
