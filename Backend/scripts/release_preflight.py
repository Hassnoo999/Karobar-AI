"""Read-only managed-database and provider capability checks. No secrets output.

python -m scripts.release_preflight --database
python -m scripts.release_preflight --providers (makes bounded provider calls)
"""
import argparse
import asyncio
import json

from sqlalchemy import create_engine, text

from app.config import settings
from app.db import managed_connect_args


def database_check() -> bool:
    engine = create_engine(settings.database_url, connect_args=managed_connect_args())
    try:
        with engine.connect() as conn, conn.begin():
            conn.exec_driver_sql("SET TRANSACTION READ ONLY")
            rows = conn.execute(text("""
                SELECT c.relname, c.relrowsecurity AS rls,
                  has_table_privilege('anon', c.oid, 'SELECT') AS anon_read,
                  has_table_privilege('authenticated', c.oid, 'SELECT') AS user_read
                FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
                WHERE n.nspname='public' AND c.relkind='r'
                  AND c.relname IN ('business_events','customers')
            """))
            result = [dict(row._mapping) for row in rows]
            policies = [dict(row._mapping) for row in conn.execute(text("""
                SELECT tablename, policyname, roles, cmd, qual, with_check
                FROM pg_policies WHERE schemaname='public'
                  AND tablename IN ('business_events','customers')
            """))]
            role = dict(conn.execute(text("""
                SELECT rolsuper AS superuser, rolbypassrls AS bypass_rls
                FROM pg_roles WHERE rolname=current_user
            """)).one()._mapping)
            # pg_stat_ssl behind a pooler describes its upstream connection,
            # not our client's TLS. Inspect the verified libpq connection.
            ssl = bool(conn.connection.driver_connection.info.ssl_in_use)
            print(json.dumps({"database": "connected", "ssl": ssl, "backend_role": role,
                "tables": result, "policies": policies}))
            if len(result) != 2:
                return False
            isolation = {}
            for browser_role in ("anon", "authenticated"):
                conn.exec_driver_sql(f"SET LOCAL ROLE {browser_role}")
                conn.execute(text("SELECT set_config('request.jwt.claim.sub', :subject, true)"),
                    {"subject": "00000000-0000-4000-8000-000000000001" if browser_role == "authenticated" else ""})
                isolation[browser_role] = {table: conn.execute(text(f"SELECT COUNT(*) FROM public.{table}")).scalar()
                    for table in ("business_events", "customers")}
                conn.exec_driver_sql("RESET ROLE")
            print(json.dumps({"direct_database_visible_rows": isolation}))
            # An enabled RLS flag is not a policy audit. Inspect the expressions
            # above and test authenticated API isolation before release.
            return ssl and all(row["rls"] or not (row["anon_read"] or row["user_read"]) for row in result) and all(
                count == 0 for counts in isolation.values() for count in counts.values())
    except Exception as exc:
        message = str(getattr(exc, "orig", exc)).lower()
        reason = next((label for token, label in [("tenant or user not found", "pooler tenant/user not found"),
            ("password authentication failed", "database password rejected"), ("could not translate host", "DNS lookup failed"),
            ("certificate verify failed", "TLS certificate verification failed"),
            ("server does not support ssl", "TLS unavailable"), ("root certificate file", "TLS trust file unavailable"),
            ("timeout", "connection timed out"), ("refused", "connection refused"), ("paused", "project paused")]
            if token in message), "connection failed")
        print(json.dumps({"database": "unavailable", "exception": type(exc).__name__, "reason": reason}))
        return False
    finally:
        engine.dispose()


async def provider_check() -> bool:
    from app.ai import get_adapter
    from app.db import pkt_today
    available = False
    for provider in get_adapter().providers:
        if provider.name == "demo":
            continue
        try:
            result = await provider.extract_event_from_text("Naveed ne 5000 rupay ka saman udhaar liya", pkt_today())
            print(json.dumps({"provider": provider.name, "capability": "text extraction", "status": "ok",
                "event_type": str(result.event_type), "amount_rupees": result.amount_rupees}))
            available = True
        except Exception as exc:
            cause = exc.__cause__
            status = getattr(cause, "status_code", None)
            code = getattr(cause, "code", None)
            # Emit only a short API error code, never the response message/body.
            safe_code = code if isinstance(code, str) and code.replace("_", "").isalnum() and len(code) < 64 else None
            print(json.dumps({"provider": provider.name, "capability": "text extraction", "status": "unavailable",
                "exception": type(exc).__name__, "http_status": status, "code": safe_code}))
    return available


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", action="store_true")
    parser.add_argument("--providers", action="store_true")
    args = parser.parse_args()
    ok = True
    if args.database:
        ok = database_check() and ok
    if args.providers:
        ok = asyncio.run(provider_check()) and ok
    raise SystemExit(0 if ok else 1)
