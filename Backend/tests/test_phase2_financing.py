"""Source provenance and preparation checks, without lending decisions."""
import asyncio
from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from app.ai.base import TextResult, ProviderError
from app.schemas.financing_workspace import ApplicantProfile, FinancingCatalogue, SchemeQuestion
from app.services.financing_workspace import (
    load_catalogue, catalogue_view, assess_profile, retrieve_scheme_facts,
    answer_scheme_question, is_financing_question, source_review_due,
)

TODAY = date(2026, 10, 23)


def get_program(response, short_id):
    return next(p for p in response.programs if short_id in p.program_id)


def test_current_snapshot_and_no_invented_deadlines():
    snapshot = catalogue_view(TODAY)
    assert len(snapshot["programs"]) == 5
    assert not snapshot["source_review_due"]
    assert all(p["availability"] == "confirm_with_institution" for p in snapshot["programs"])
    assert all(p["days_remaining"] is None and not p["deadline_passed"] for p in snapshot["programs"])
    assert all(p["application_deadline"] is None for p in snapshot["programs"])


@pytest.mark.parametrize("mutation", ["url", "source", "duplicate", "deadline", "range", "field"])
def test_catalogue_rejects_unsafe_or_untraceable_imports(mutation):
    data = load_catalogue().model_dump(mode="json")
    program = data["programs"][0]
    if mutation == "url":
        program["application_url"] = "https://pmybals.pmyp.gov.pk.evil.example/apply"
    elif mutation == "source":
        program["terms"][0]["source_id"] = "model-invented"
    elif mutation == "duplicate":
        data["programs"].append(program)
    elif mutation == "deadline":
        program["application_deadline"] = "2026-10-24"
    elif mutation == "range":
        program["criteria"][0]["minimum"] = 100
    else:
        program["criteria"][0]["field"] = "sales_fake_threshold"
    with pytest.raises(ValidationError):
        FinancingCatalogue.model_validate(data)


@pytest.mark.parametrize("url", ["http://www.hbl.com/", "https://secret@www.hbl.com/", "https://www.hbl.com:443/", "javascript:alert(1)"])
def test_catalogue_rejects_unsafe_links(url):
    data = load_catalogue().model_dump(mode="json")
    data["programs"][0]["sources"][0]["url"] = url
    with pytest.raises(ValidationError):
        FinancingCatalogue.model_validate(data)


@pytest.mark.parametrize("mutation", ["shared_source", "boolean_bounds", "missing_unit", "negative_bound"])
def test_update_contract_rejects_ambiguous_rules(mutation):
    data = load_catalogue().model_dump(mode="json")
    if mutation == "shared_source":
        data["programs"][1]["sources"][0]["id"] = "pmyp"
    elif mutation == "boolean_bounds":
        data["programs"][0]["criteria"][1]["minimum"] = 1
    elif mutation == "missing_unit":
        data["programs"][0]["criteria"][0]["unit"] = None
    else:
        data["programs"][0]["criteria"][0]["minimum"] = -1
    with pytest.raises(ValidationError):
        FinancingCatalogue.model_validate(data)


def test_unknown_is_not_false_or_zero():
    response = assess_profile(ApplicantProfile(), TODAY)
    for program in response.programs:
        assert program.preparation_pct == 0
        assert program.unknown_count == program.checkable_count
        assert program.declared_matches == program.attention_count == 0
        assert program.lender_check_count >= 1
        assert program.status == "details_needed"


def test_pm_age_exception_needs_sector_not_a_guess():
    profile = ApplicantProfile(age_years=19, resident_pakistani=True, requested_amount_rupees=500000)
    unknown = get_program(assess_profile(profile, TODAY), "pm-youth")
    assert unknown.unknown_count == 1
    it = get_program(assess_profile(profile.model_copy(update={"business_sector": "it_ecommerce"}), TODAY), "pm-youth")
    assert it.preparation_pct == 100 and it.status == "preparation_complete"
    retail = get_program(assess_profile(profile.model_copy(update={"business_sector": "retail"}), TODAY), "pm-youth")
    assert retail.attention_count == 1
    assert next(c for c in retail.checks if c.id == "age").gap_display.startswith("2 years")


def test_bop_is_not_unlocked_by_sales_or_receivables():
    result = get_program(assess_profile(ApplicantProfile(age_years=30, bop_relationship_months=8,
        bop_invited=False, requested_amount_rupees=500000), TODAY), "bop-")
    assert result.attention_count == 2 and result.preparation_pct == 50
    assert next(c for c in result.checks if c.id == "relationship").gap_display.startswith("4 months")
    assert next(c for c in result.checks if c.id == "dbr").state == "lender_check"


def test_hbl_does_not_use_recorded_history_as_business_age(seeded_client):
    body = seeded_client.post("/api/financing/assessment", json={"age_years": 30,
        "resident_pakistani": True, "bank_statement_months": 12, "requested_amount_rupees": 500000}).json()
    hbl = next(p for p in body["programs"] if p["program_id"] == "hbl-small-business-finance")
    assert next(c for c in hbl["checks"] if c["id"] == "business_age")["state"] == "unknown"
    assert hbl["preparation_pct"] == 80


def test_green_preparation_still_has_lender_checks():
    profile = ApplicantProfile(age_years=30, valid_cnic=True, two_non_family_guarantors=True,
                               within_akhuwat_branch_area=True)
    result = get_program(assess_profile(profile, TODAY), "akhuwat")
    assert result.preparation_pct == 100
    assert result.status == "preparation_complete" and result.lender_check_count == 1
    assert "approval probability" in assess_profile(profile, TODAY).disclosure


def test_both_no_relationship_declarations_are_explicit_for_meezan():
    profile = ApplicantProfile(meezan_existing_relationship=False, other_isaaf_financing=False,
                               requested_amount_rupees=500000)
    result = get_program(assess_profile(profile, TODAY), "meezan")
    assert result.preparation_pct == 100 and result.lender_check_count
    assert get_program(assess_profile(ApplicantProfile(), TODAY), "meezan").preparation_pct == 0


@pytest.mark.parametrize("payload", [{"age_years": True}, {"age_years": "30"}, {"age_years": -1},
    {"resident_pakistani": "yes"}, {"requested_amount_rupees": 0}, {"requested_amount_rupees": 1.5},
    {"sales": 999999999}, {"cnic_number": "never collect this"}])
def test_profile_input_is_typed_and_minimal(client, payload):
    assert client.post("/api/financing/assessment", json=payload).status_code == 422


def test_stale_and_future_snapshots_do_not_get_green_status():
    catalogue = load_catalogue()
    assert source_review_due(catalogue, TODAY + timedelta(days=30))
    assert source_review_due(catalogue, TODAY - timedelta(days=1))
    result = assess_profile(ApplicantProfile(), TODAY + timedelta(days=30))
    assert all(p.status == "source_review_due" for p in result.programs)
    catalogue.programs[0].sources[0].checked_on = TODAY - timedelta(days=31)
    assert source_review_due(catalogue, TODAY)


@pytest.mark.parametrize("question,program,topic", [
    ("PM Youth loan kitna milta hai?", "pm-youth", "amount"),
    ("BOP markup kya hai?", "bop-", "pricing"),
    ("HBL ke documents chahiye", "hbl-", "documents"),
    ("اخوت کے لیے ضامن چاہیے؟", "akhuwat", "criteria"),
    ("میزان قرض کی شرح کیا ہے؟", "meezan", "pricing"),
    ("Akhuwat ki last date?", "akhuwat", "availability"),
    ("Meezan repayment duration", "meezan", "tenor"),
    ("BOP processing fee?", "bop-", "tenor"),
    ("How old must my HBL business be?", "hbl-", "criteria"),
])
def test_multilingual_topic_retrieval(question, program, topic):
    data = retrieve_scheme_facts(SchemeQuestion(question=question), TODAY)
    assert data["status"] == "answered"
    assert any(topic == fact["topic"] for fact in data["facts"])
    assert all(program in fact["program_id"] for fact in data["facts"])
    assert data["sources"]


def test_comparison_has_both_programs_and_no_invented_rate():
    data = retrieve_scheme_facts(SchemeQuestion(question="Compare HBL and BOP rates"), TODAY)
    assert len({f["program_id"] for f in data["facts"]}) == 2
    hbl = next(f for f in data["facts"] if f["program_id"] == "hbl-small-business-finance")
    assert "No fixed rate" in hbl["text"]


def test_unknown_deadline_and_product_amount_are_honest():
    data = retrieve_scheme_facts(SchemeQuestion(question="Akhuwat loan amount and deadline"), TODAY)
    assert any("No verified application closing date" in f["text"] for f in data["facts"])
    assert any("does not establish" in f["text"] for f in data["facts"])


@pytest.mark.parametrize("question", ["Am I eligible for a loan?", "Mujhe loan chahiye"])
def test_unscoped_personal_questions_need_a_scheme(question):
    assert retrieve_scheme_facts(SchemeQuestion(question=question), TODAY)["status"] == "needs_clarification"


def test_no_accounting_mutation_or_customer_data_in_scheme_answers(seeded_client):
    before = seeded_client.get("/api/ledger/events").json()
    result = seeded_client.post("/api/ask", json={"question": "BOP loan markup kya hai?"}).json()
    assert result["answer_source"] == "reviewed_financing_sources"
    assert result["tool_used"] == "financing_sources"
    assert result["data"]["sources"][0]["url"].startswith("https://www.bop.com.pk/")
    assert "Ahmed" not in str(result)
    assert seeded_client.get("/api/ledger/events").json() == before


def test_ledger_question_and_bank_customer_not_hijacked():
    for q in ["Total udhaar kitna hai?", "HBL ka outstanding balance?", "Is month ki sales kitni?"]:
        assert not is_financing_question(q)
    assert is_financing_question("HBL loan requirements")


@pytest.mark.parametrize("output", ["{\"fact_ids\":[\"invented\"]}", "I approve your loan", "{\"fact_ids\":[],\"approval\":true}"])
def test_model_cannot_invent_a_fact_or_approval(monkeypatch, output):
    class FakeAdapter:
        async def compose_answer(self, *args):
            return TextResult(text=output)
    monkeypatch.setattr("app.services.financing_workspace.get_adapter", lambda: FakeAdapter())
    result = asyncio.run(answer_scheme_question(SchemeQuestion(question="BOP loan amount", use_ai=True), TODAY))
    assert result.data["retrieval_mode"] == "source_fallback"
    assert "I approve" not in result.answer and "3,500,000" in result.answer


def test_provider_failure_preserves_cited_sources(monkeypatch):
    class FailedAdapter:
        async def compose_answer(self, *args):
            raise ProviderError("unavailable")
    monkeypatch.setattr("app.services.financing_workspace.get_adapter", lambda: FailedAdapter())
    result = asyncio.run(answer_scheme_question(SchemeQuestion(question="BOP loan amount", use_ai=True), TODAY))
    assert result.data["retrieval_mode"] == "source_fallback" and result.data["sources"]


def test_slow_provider_has_a_bounded_source_fallback(monkeypatch):
    class SlowAdapter:
        async def compose_answer(self, *args):
            await asyncio.sleep(1)
            raise AssertionError("The selection should already be cancelled")
    monkeypatch.setattr("app.services.financing_workspace.get_adapter", lambda: SlowAdapter())
    monkeypatch.setattr("app.services.financing_workspace.AI_SELECTION_TIMEOUT", 0.001)
    result = asyncio.run(answer_scheme_question(SchemeQuestion(question="BOP amount", use_ai=True), TODAY))
    assert result.data["retrieval_mode"] == "source_fallback"
    assert "3,500,000" in result.answer


def test_model_cannot_suppress_a_compared_institution(monkeypatch):
    class PartialAdapter:
        async def compose_answer(self, *args):
            return TextResult(text='{"fact_ids":["bop-e-business-qarza:term:amount"]}')
    monkeypatch.setattr("app.services.financing_workspace.get_adapter", lambda: PartialAdapter())
    result = asyncio.run(answer_scheme_question(SchemeQuestion(question="Compare HBL and BOP amounts", use_ai=True), TODAY))
    assert result.data["retrieval_mode"] == "source_fallback"
    assert len({f["program_id"] for f in result.data["facts"]}) == 2


def test_model_only_selects_existing_ids_and_never_receives_profile(monkeypatch):
    class FakeAdapter:
        async def compose_answer(self, question, tool, data):
            assert tool == "financing_fact_selection"
            assert all(f["basis"] == "published_source" for f in data["facts"])
            assert "profile" not in data
            return TextResult(text='{"fact_ids":["bop-e-business-qarza:term:amount"]}')
    monkeypatch.setattr("app.services.financing_workspace.get_adapter", lambda: FakeAdapter())
    result = asyncio.run(answer_scheme_question(SchemeQuestion(question="BOP loan amount", use_ai=True,
        profile=ApplicantProfile(age_years=30)), TODAY))
    assert result.data["retrieval_mode"] == "ai_assisted_retrieval"
    assert "3,500,000" in result.answer


def test_new_personal_endpoints_stay_authenticated(client, monkeypatch):
    from app.main import app
    from app.auth import get_merchant_id
    from app.config import settings
    override = app.dependency_overrides.pop(get_merchant_id)
    monkeypatch.setattr(settings, "require_auth", True)
    try:
        assert client.post("/api/financing/assessment", json={}).status_code == 401
        assert client.post("/api/financing/questions", json={"question": "PM Youth amount"}).status_code == 401
        assert client.get("/api/financing/catalog").status_code == 200
    finally:
        app.dependency_overrides[get_merchant_id] = override


def test_schema_and_bad_program_input(client):
    assert client.get("/api/financing/catalog/schema").json()["properties"]["schema_version"]["const"] == 2
    assert client.post("/api/financing/questions", json={"question":"loan amount", "program_id":"missing"}).status_code == 422
