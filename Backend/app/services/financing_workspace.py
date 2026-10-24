"""Reviewed catalogue, deterministic preparation and bounded source retrieval.

No internet fetch, eval, arbitrary URL, ledger mutation or profile persistence.
The optional model may select existing fact IDs; it cannot write loan terms.
"""
from __future__ import annotations

import asyncio
import re
import unicodedata
from datetime import date, timedelta
from pathlib import Path

from app.ai import get_adapter
from app.ai.base import ProviderError, parse_json_object
from app.db import pkt_today
from app.errors import DomainValidationError
from app.schemas.ask import AskResponse
from app.schemas.financing_workspace import (
    ApplicantProfile, AssessmentResponse, FinancingCatalogue, PreparationCheck,
    SchemeAssessment, SchemeQuestion,
)

CATALOGUE_PATH = Path(__file__).resolve().parent.parent / "data" / "financing_catalog_v2.json"
AI_SELECTION_TIMEOUT = 15.0


def load_catalogue(path: Path | None = None) -> FinancingCatalogue:
    # Deliberately reread the small snapshot so reviewed file updates cannot leave
    # a stale in-process catalogue. A deployment still pins its source snapshot.
    return FinancingCatalogue.model_validate_json((path or CATALOGUE_PATH).read_text(encoding="utf-8"))


def source_review_due(catalogue: FinancingCatalogue, today: date) -> bool:
    dates = [catalogue.reviewed_on, *(s.checked_on for p in catalogue.programs for s in p.sources)]
    return today < max(dates) or today >= min(dates) + timedelta(days=catalogue.review_after_days)


def catalogue_view(today: date | None = None) -> dict:
    today = today or pkt_today()
    catalogue = load_catalogue()
    body = catalogue.model_dump(mode="json")
    body["source_review_due"] = source_review_due(catalogue, today)
    body["generated_on"] = today.isoformat()
    for program in body["programs"]:
        deadline = date.fromisoformat(program["application_deadline"]) if program["application_deadline"] else None
        program["days_remaining"] = max(0, (deadline - today).days) if deadline else None
        program["deadline_passed"] = bool(deadline and deadline < today)
    return body


def assess_profile(profile: ApplicantProfile, today: date | None = None) -> AssessmentResponse:
    today = today or pkt_today()
    catalogue = load_catalogue()
    due = source_review_due(catalogue, today)
    assessments = []
    for program in catalogue.programs:
        checks = []
        for criterion in program.criteria:
            current = getattr(profile, criterion.field) if criterion.field else None
            state = "lender_check" if criterion.kind == "lender" else "unknown"
            display = "Institution must verify" if criterion.kind == "lender" else "Not supplied"
            gap = None
            if criterion.kind == "boolean" and current is not None:
                state = "declared_match" if current == criterion.expected else "needs_attention"
                display = "Yes (your declaration)" if current else "No (your declaration)"
            elif criterion.kind == "range" and current is not None:
                minimum = criterion.minimum
                if criterion.it_minimum is not None and profile.business_sector == "it_ecommerce":
                    minimum = criterion.it_minimum
                # If the sector is unknown, do not assume the stricter or easier age floor.
                if criterion.it_minimum is not None and profile.business_sector is None and criterion.it_minimum <= current < (minimum or 0):
                    state, gap = "unknown", "Add the business sector to check the age exception."
                else:
                    low = minimum is not None and current < minimum
                    high = criterion.maximum is not None and current > criterion.maximum
                    state = "needs_attention" if low or high else "declared_match"
                    if low:
                        gap = f"{minimum - current:,} {criterion.unit or ''} below the published minimum."
                    elif high:
                        gap = f"{current - criterion.maximum:,} {criterion.unit or ''} above the published maximum."
                display = f"{current:,} {criterion.unit or ''} (your declaration)"
            checks.append(PreparationCheck(
                id=criterion.id, label=criterion.label, requirement=criterion.requirement,
                source_id=criterion.source_id, state=state, current_display=display, gap_display=gap,
            ))
        matches = sum(c.state == "declared_match" for c in checks)
        unknown = sum(c.state == "unknown" for c in checks)
        attention = sum(c.state == "needs_attention" for c in checks)
        lender = sum(c.state == "lender_check" for c in checks)
        count = len(checks) - lender
        status = "source_review_due" if due else "review_gaps" if attention else "details_needed" if unknown else "preparation_complete"
        assessments.append(SchemeAssessment(
            program_id=program.id, preparation_pct=round(matches * 100 / count) if count else 0,
            declared_matches=matches, checkable_count=count, unknown_count=unknown,
            attention_count=attention, lender_check_count=lender, status=status, checks=checks,
        ))
    return AssessmentResponse(catalogue_version=catalogue.version, generated_on=today, source_review_due=due, programs=assessments)


def _normalized(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


def _mentions(text: str, alias: str) -> bool:
    return re.search(r"(?<!\w)" + re.escape(alias.casefold()) + r"(?!\w)", text) is not None


def is_financing_question(question: str) -> bool:
    text = _normalized(question)
    if re.search(r"\b(loan|loans|financing|finance|scheme|schemes|qar[sz]a|eligib\w*|guarantor\w*)\b|قرض|اسکیم|فنانس|اخوت|میزان", text):
        return True
    if any(_mentions(text, alias) for p in load_catalogue().programs for alias in p.aliases):
        # A bank name may also be a customer in the ordinary ledger.
        return not re.search(r"\b(udhaar|udhar|outstanding|balance|baqi|baki)\b", text)
    return False


_TOPICS = {
    "pricing": r"markup|mark.up|interest|pricing|profit.rate|\brates?\b|sood|sud\b|سود|شرح",
    "documents": r"document|statement|cnic|guarant|zamin|ضامن|دستاویز|شناخت|کاغذ",
    "application": r"apply|application|process|kahan|kaise|درخواست|طریقہ",
    "availability": r"deadline|last.date|closing|days.left|kab.tak|aakhri|akhri|available|open|بند|آخری|دستیاب",
    "tenor": r"tenor|repay|duration|instal|muddat|\bterm\b|fees?|charges?|processing|واپس|مدت|قسط|فیس",
    "security": r"collateral|security|mortgage|property|guarantee|رہن|ضمانت",
    "criteria": r"eligib|criteria|requirement|\bage\b|how.old|umar|umr|relationship|business.age|ready|readiness|progress|profile|qualif|chahiye|need|شرائط|عمر|تیاری|اہل",
    "amount": r"amount|how.much|kitn[aei]|limit|million|lakh|کتن|رقم",
}


def retrieve_scheme_facts(payload: SchemeQuestion, today: date | None = None) -> dict:
    today = today or pkt_today()
    catalogue = load_catalogue()
    text = _normalized(payload.question)
    mentioned = [p for p in catalogue.programs if any(_mentions(text, alias) for alias in p.aliases)]
    context = next((p for p in catalogue.programs if p.id == payload.program_id), None)
    if payload.program_id and context is None:
        raise DomainValidationError("Choose a financing program from the current catalogue.")
    selected = mentioned or ([context] if context else [])
    topics = {topic for topic, pattern in _TOPICS.items() if re.search(pattern, text)}
    comparative = bool(re.search(r"compar|difference|which|kon.?sa|konsa|muqabla|موازن|کون", text))
    general = bool(re.search(r"scheme|program|financing|loan|qar[sz]a|اسکیم|قرض", text))
    if not selected:
        if comparative or (topics and "criteria" not in topics):
            selected = catalogue.programs
        else:
            return {"status": "needs_clarification", "facts": [], "sources": [], "catalogue_version": catalogue.version,
                    "source_review_due": source_review_due(catalogue, today), "reviewed_on": str(catalogue.reviewed_on)}
    if not topics:
        if general or comparative or any(_normalized(payload.question) == _normalized(a) for p in selected for a in p.aliases):
            topics = {"amount", "application"}
        elif not payload.use_ai:
            return {"status": "not_in_sources", "facts": [], "sources": [], "catalogue_version": catalogue.version,
                    "source_review_due": source_review_due(catalogue, today), "reviewed_on": str(catalogue.reviewed_on)}
        else:
            topics = {"amount", "pricing", "tenor", "documents", "criteria", "application", "security", "availability"}
    facts = []
    sources = []
    assessment = assess_profile(payload.profile, today) if payload.profile else None
    for program in selected:
        program_facts = []
        for term in program.terms:
            if term.topic in topics or ("security" in topics and term.topic == "amount"):
                program_facts.append({"id": f"{program.id}:term:{term.id}", "program_id": program.id,
                                      "program_name": program.short_name, "topic": term.topic,
                                      "text": term.value, "source_id": term.source_id, "basis": "published_source"})
        if topics.intersection({"criteria", "documents", "security"}):
            criteria = program.criteria
            if "criteria" not in topics:
                matches = [c for c in criteria if re.search(r"guarant|cnic|statement|document|property|security", c.label, re.I)]
                criteria = matches or [c for c in criteria if c.kind == "lender"]
            for criterion in criteria:
                program_facts.append({"id": f"{program.id}:check:{criterion.id}", "program_id": program.id,
                                      "program_name": program.short_name, "topic": "criteria",
                                      "text": criterion.requirement, "source_id": criterion.source_id, "basis": "published_source"})
        if "availability" in topics:
            deadline = f"Published closing date: {program.application_deadline}." if program.application_deadline else "No verified application closing date is recorded; days remaining cannot be calculated."
            program_facts.append({"id": f"{program.id}:availability", "program_id": program.id,
                                  "program_name": program.short_name, "topic": "availability",
                                  "text": f"{program.availability_note} {deadline}", "source_id": program.sources[0].id,
                                  "basis": "snapshot_limit"})
        # A missing rate/document fact must remain visibly unknown, not be filled
        # from another bank or the model's training data.
        for topic in sorted(topics - {f["topic"] for f in program_facts} - {"criteria", "security"}):
            program_facts.append({"id": f"{program.id}:unknown:{topic}", "program_id": program.id,
                                  "program_name": program.short_name, "topic": topic,
                                  "text": f"A verified {topic} detail is not recorded for this program. Confirm it with the institution.",
                                  "source_id": program.sources[0].id, "basis": "snapshot_limit"})
        if assessment and "criteria" in topics:
            check = next(a for a in assessment.programs if a.program_id == program.id)
            program_facts.insert(0, {"id": f"{program.id}:preparation", "program_id": program.id,
                                    "program_name": program.short_name, "topic": "preparation",
                                    "text": f"Your declarations match {check.declared_matches} of {check.checkable_count} preparation checks; {check.unknown_count} details unknown, {check.attention_count} need attention and {check.lender_check_count} institution checks remain. This is not verified qualification.",
                                    "source_id": program.sources[0].id, "basis": "user_declaration"})
        # Keep every selected program represented for comparisons.
        facts.extend(program_facts[:8])
        sources.extend(s.model_dump(mode="json") for s in program.sources)
    return {"status": "answered", "facts": facts[:40], "sources": sources, "topics": sorted(topics),
            "catalogue_version": catalogue.version, "reviewed_on": str(catalogue.reviewed_on),
            "source_review_due": source_review_due(catalogue, today)}


async def answer_scheme_question(payload: SchemeQuestion, today: date | None = None) -> AskResponse:
    data = retrieve_scheme_facts(payload, today)
    facts = data["facts"]
    mode = "curated_retrieval"
    if payload.use_ai and facts:
        public_facts = [f for f in facts if f["basis"] == "published_source"]
        if public_facts:
            try:
                result = await asyncio.wait_for(get_adapter().compose_answer(
                    payload.question, "financing_fact_selection", {"facts": public_facts}), timeout=AI_SELECTION_TIMEOUT)
                selection = parse_json_object(result.text)
                ids = selection.get("fact_ids")
                allowed = {fact["id"] for fact in public_facts}
                if set(selection) != {"fact_ids"} or not isinstance(ids, list) or not ids or len(ids) > 12 or any(not isinstance(i, str) or i not in allowed for i in ids):
                    raise ValueError("Only retrieved fact IDs may be selected")
                selected_ids = set(ids)
                # Never suppress a requested bank or the app's known-unknowns.
                covered = {f["program_id"] for f in public_facts if f["id"] in selected_ids}
                if covered != {f["program_id"] for f in public_facts}:
                    raise ValueError("Selection omitted a compared program")
                facts = [f for f in facts if f["id"] in selected_ids or f["basis"] != "published_source"]
                mode = "ai_assisted_retrieval"
            except (ProviderError, ValueError, TypeError, TimeoutError):
                mode = "source_fallback"
    data["facts"] = facts
    data["retrieval_mode"] = mode
    used_sources = {f["source_id"] for f in facts}
    data["sources"] = [s for s in data["sources"] if s["id"] in used_sources]
    roman = bool(re.search(r"\b(kitna|kitni|kitne|kya|kaise|chahiye|qarza|umar|hai|hain)\b", _normalized(payload.question)))
    urdu = bool(re.search(r"[\u0600-\u06ff]", payload.question))
    if data["status"] == "needs_clarification":
        answer = "Which program do you mean: PM Youth, Akhuwat, BOP e-Business, HBL Business or Meezan I-SAAF? You can compare their amounts, pricing, requirements or application routes."
    elif not facts:
        answer = "That detail is not established by this reviewed catalogue. Ask about a program's published amounts, pricing, documents, applicant checks or application route, and confirm unlisted details with the institution."
    else:
        intro = "Yeh reviewed official sources ki maloomat hai:" if roman else "جائزہ لیے گئے سرکاری ذرائع کے مطابق:" if urdu else "From the reviewed official sources:"
        groups = []
        for name in dict.fromkeys(f["program_name"] for f in facts):
            groups.append(name + "\n" + "\n".join("• " + f["text"] for f in facts if f["program_name"] == name))
        answer = intro + "\n\n" + "\n\n".join(groups)
        if "criteria" in data.get("topics", []) and not payload.profile:
            answer += "\n\nOpen Financing and add your applicant details for a preparation comparison. The ledger cannot prove your age, identity or banking relationship."
    answer += "\n\nSource snapshot: " + data["reviewed_on"] + ". Confirm current terms and availability with the institution. This is not a lending decision."
    if data["source_review_due"]:
        answer = "Source review is due; these terms may be outdated.\n\n" + answer
    return AskResponse(answer=answer, tool_used="financing_sources", provider="curated_sources",
                       answer_source="reviewed_financing_sources", data=data)
