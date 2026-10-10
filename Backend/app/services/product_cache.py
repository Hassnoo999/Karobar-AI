"""Shared short-lived product snapshot cache, invalidated by every ledger mutation."""
combined_cache: dict[str, tuple[float, dict]] = {}


def invalidate_product_cache(merchant_id: str) -> None:
    combined_cache.pop(merchant_id, None)
