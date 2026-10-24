"""A reviewed public catalogue and ephemeral applicant preparation checks.

No credit score, bank-verified identity, application decision or stored profile.
"""
from __future__ import annotations

from datetime import date
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, field_validator, model_validator

OFFICIAL_HOSTS = {
    "pmybals.pmyp.gov.pk", "pmyp.gov.pk", "www.bop.com.pk", "www.hbl.com",
    "www.meezanbank.com", "akhuwat.org.pk", "donate.akhuwat.org.pk",
}


def official_url(value: str) -> str:
    parsed = urlsplit(value)
    if parsed.scheme != "https" or parsed.hostname not in OFFICIAL_HOSTS or parsed.username or parsed.password or parsed.port:
        raise ValueError("Use a reviewed HTTPS official institution URL")
    return value


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class FinancingSource(StrictModel):
    id: str
    title: str
    url: str
    checked_on: date
    note: str = "Page reviewed; current intake and funding still need institution confirmation."

    _check_url = field_validator("url")(official_url)


class FinancingTerm(StrictModel):
    id: str
    label: str
    value: str
    source_id: str
    topic: Literal["amount", "pricing", "tenor", "documents", "application", "security", "availability"]


ProfileField = Literal[
    "age_years", "resident_pakistani", "valid_cnic", "business_operating_months",
    "bank_statement_months", "bop_relationship_months", "bop_invited",
    "two_non_family_guarantors", "within_akhuwat_branch_area", "acceptable_property",
    "meezan_existing_relationship", "other_isaaf_financing", "requested_amount_rupees",
]


class FinancingCriterion(StrictModel):
    id: str
    label: str
    requirement: str
    source_id: str
    kind: Literal["range", "boolean", "lender"]
    field: ProfileField | None = None
    minimum: StrictInt | None = None
    maximum: StrictInt | None = None
    expected: StrictBool | None = None
    unit: Literal["years", "months", "PKR"] | None = None
    it_minimum: StrictInt | None = None

    @model_validator(mode="after")
    def valid_rule(self):
        if self.kind == "lender":
            if any(v is not None for v in (self.field, self.minimum, self.maximum, self.expected, self.it_minimum)):
                raise ValueError("Lender-only checks cannot contain executable rules")
        elif self.kind == "range":
            if self.field not in {"age_years", "business_operating_months", "bank_statement_months", "bop_relationship_months", "requested_amount_rupees"}:
                raise ValueError("Numeric checks require an allowed numeric profile field")
            if self.minimum is None and self.maximum is None:
                raise ValueError("Numeric check needs a bound")
            if self.minimum is not None and self.maximum is not None and self.minimum > self.maximum:
                raise ValueError("Invalid range")
            if self.unit is None or any(v is not None and v < 0 for v in (self.minimum, self.maximum, self.it_minimum)):
                raise ValueError("Numeric checks require units and non-negative bounds")
            if self.expected is not None or (self.it_minimum is not None and self.field != "age_years"):
                raise ValueError("Invalid numeric rule options")
        elif self.field in {None, "age_years", "business_operating_months", "bank_statement_months", "bop_relationship_months", "requested_amount_rupees"} or self.expected is None:
            raise ValueError("Boolean check needs a boolean field and expectation")
        elif any(v is not None for v in (self.minimum, self.maximum, self.it_minimum, self.unit)):
            raise ValueError("Boolean checks cannot contain numeric rules")
        return self


class FinancingScheme(StrictModel):
    id: str
    short_name: str
    name: str
    institution: str
    aliases: list[str]
    description: str
    application_url: str
    availability: Literal["confirm_with_institution", "open", "closed"] = "confirm_with_institution"
    availability_note: str
    application_deadline: date | None = None
    deadline_source_id: str | None = None
    sources: list[FinancingSource] = Field(min_length=1)
    terms: list[FinancingTerm] = Field(min_length=1)
    criteria: list[FinancingCriterion] = Field(min_length=1)

    _check_application = field_validator("application_url")(official_url)

    @model_validator(mode="after")
    def consistent_sources(self):
        ids = [source.id for source in self.sources]
        if len(set(ids)) != len(ids):
            raise ValueError("Duplicate source IDs")
        if len({c.id for c in self.criteria}) != len(self.criteria) or len({t.id for t in self.terms}) != len(self.terms):
            raise ValueError("Duplicate fact/check IDs")
        for fact in [*self.terms, *self.criteria]:
            if fact.source_id not in ids:
                raise ValueError("Fact references a missing source")
        if self.application_deadline is not None and self.deadline_source_id not in ids:
            raise ValueError("A deadline needs an explicit published source")
        if self.availability != "confirm_with_institution" and not any(t.topic == "availability" for t in self.terms):
            raise ValueError("Open/closed claims need a sourced availability fact")
        return self


class FinancingCatalogue(StrictModel):
    schema_version: Literal[2]
    version: str
    reviewed_on: date
    review_after_days: int = Field(default=30, ge=1, le=365)
    programs: list[FinancingScheme] = Field(min_length=1, max_length=30)

    @model_validator(mode="after")
    def unique_and_dated(self):
        if len({p.id for p in self.programs}) != len(self.programs):
            raise ValueError("Duplicate program IDs")
        source_ids = [s.id for p in self.programs for s in p.sources]
        if len(set(source_ids)) != len(source_ids):
            raise ValueError("Source IDs must be unique across the catalogue")
        for program in self.programs:
            if any(s.checked_on > self.reviewed_on for s in program.sources):
                raise ValueError("Source check cannot follow catalogue review")
        return self


class ApplicantProfile(StrictModel):
    age_years: StrictInt | None = Field(default=None, ge=0, le=120)
    business_sector: Literal["retail", "it_ecommerce", "other"] | None = None
    resident_pakistani: StrictBool | None = None
    valid_cnic: StrictBool | None = None
    business_operating_months: StrictInt | None = Field(default=None, ge=0, le=1200)
    bank_statement_months: StrictInt | None = Field(default=None, ge=0, le=600)
    bop_relationship_months: StrictInt | None = Field(default=None, ge=0, le=600)
    bop_invited: StrictBool | None = None
    two_non_family_guarantors: StrictBool | None = None
    within_akhuwat_branch_area: StrictBool | None = None
    acceptable_property: StrictBool | None = None
    meezan_existing_relationship: StrictBool | None = None
    other_isaaf_financing: StrictBool | None = None
    requested_amount_rupees: StrictInt | None = Field(default=None, ge=1, le=100_000_000)


class PreparationCheck(StrictModel):
    id: str
    label: str
    requirement: str
    source_id: str
    state: Literal["declared_match", "needs_attention", "unknown", "lender_check"]
    current_display: str
    gap_display: str | None = None


class SchemeAssessment(StrictModel):
    program_id: str
    preparation_pct: int
    declared_matches: int
    checkable_count: int
    unknown_count: int
    attention_count: int
    lender_check_count: int
    status: Literal["details_needed", "review_gaps", "preparation_complete", "source_review_due"]
    checks: list[PreparationCheck]


class AssessmentResponse(StrictModel):
    catalogue_version: str
    source_review_due: bool
    generated_on: date
    programs: list[SchemeAssessment]
    disclosure: str = "Preparation checks use your declarations. They are not document verification, a credit score, approval probability or a lending decision."


class SchemeQuestion(StrictModel):
    question: str = Field(min_length=2, max_length=500)
    program_id: str | None = Field(default=None, max_length=80)
    profile: ApplicantProfile | None = None
    use_ai: bool = False

    @field_validator("question", mode="before")
    @classmethod
    def clean_question(cls, value):
        return value.strip() if isinstance(value, str) else value
