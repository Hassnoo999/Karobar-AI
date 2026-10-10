"""Bridge statements must describe recorded facts, not inferred verification."""
import pytest

from app.services.product_cache import invalidate_product_cache


@pytest.mark.parametrize("route", ["/api/intelligence", "/api/combined"])
def test_bridge_profile_and_references_do_not_overclaim(seeded_client, route):
    invalidate_product_cache("demo")
    body = seeded_client.get(route).json()
    intelligence = body.get("intelligence", body)
    profile = intelligence["evidence_profile"]
    assert "merchant-confirmed" in profile["ledger_depth"]
    assert "not independently audited" in profile["ledger_depth"]
    assert "recurring" not in profile["expense_pattern"].lower()
    assert "credit sales" in profile["customer_concentration"]
    assert "receivables" not in profile["customer_concentration"]
    for match in intelligence["financing_matches"]:
        assert match["relevance"] == "low"
        assert match["match_reasons"] == []
        assert "no personalized fit" in match["grounded_summary"].lower()
        assert "appears to meet" not in match["program"]["eligibility_notes"]
