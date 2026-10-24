"""Financing programs and readiness matching (ledger-verifiable vs manual requirements)."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import get_merchant_id
from app.db import get_db
from app.schemas.financing import ProgramReadiness, ProgramSummary
from app.services.matching import evaluate_readiness, load_programs
from app.schemas.ask import AskResponse
from app.schemas.financing_workspace import ApplicantProfile, AssessmentResponse, FinancingCatalogue, SchemeQuestion
from app.services.financing_workspace import catalogue_view, assess_profile, answer_scheme_question

router = APIRouter(prefix="/financing", tags=["financing"])


@router.get("/programs", response_model=list[ProgramSummary])
async def programs() -> list[Any]:
    return [ProgramSummary.model_validate(program) for program in load_programs()]


@router.get("/readiness", response_model=list[ProgramReadiness])
def readiness(db: Session = Depends(get_db), merchant_id: str = Depends(get_merchant_id)):
    return evaluate_readiness(db, merchant_id=merchant_id)


@router.get("/catalog")
def catalogue():
    """Public, reviewed institution facts; no merchant data or paid model call."""
    return catalogue_view()


@router.get("/catalog/schema")
def catalogue_schema():
    """Machine-readable import contract for a future reviewed updater."""
    return FinancingCatalogue.model_json_schema()


@router.post("/assessment", response_model=AssessmentResponse)
def assessment(profile: ApplicantProfile, merchant_id: str = Depends(get_merchant_id)):
    """Ephemeral self-declarations. Never persist or infer a lending decision."""
    return assess_profile(profile)


@router.post("/questions", response_model=AskResponse)
async def scheme_question(payload: SchemeQuestion, merchant_id: str = Depends(get_merchant_id)):
    return await answer_scheme_question(payload)
