"""Fail closed rather than publish a writable, unauthenticated demo backend."""
from app.config import Settings


def validate_deployment(config: Settings) -> None:
    if config.receipt_storage not in {"local", "vercel_blob"}:
        raise RuntimeError("RECEIPT_STORAGE must be local or vercel_blob")
    if not config.deployed:
        return
    missing = []
    if not config.require_auth:
        missing.append("REQUIRE_AUTH=true")
    if not config.supabase_url.startswith("https://"):
        missing.append("SUPABASE_URL")
    if "*" in config.cors_origins_list:
        missing.append("explicit CORS_ORIGINS (no wildcard)")
    if not config.database_url.startswith(("postgresql://", "postgresql+psycopg2://")):
        missing.append("managed PostgreSQL DATABASE_URL")
    if config.auto_seed:
        missing.append("AUTO_SEED=false")
    if config.receipt_storage != "vercel_blob" or not config.blob_store_id:
        missing.append("RECEIPT_STORAGE=vercel_blob and BLOB_STORE_ID")
    if missing:
        raise RuntimeError("Unsafe deployment configuration: " + ", ".join(missing))
