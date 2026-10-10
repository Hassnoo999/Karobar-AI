"""Guarded interpretation → existing SQL tool → deterministic financial wording."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.ai import get_adapter
from app.ai.base import ProviderError
from app.auth import get_merchant_id
from app.db import get_db, pkt_today
from app.errors import AIUnavailableError
from app.schemas.ask import AskRequest, AskResponse
from app.services.ask_engine import SUGGESTIONS, SUPPORTED_TOOLS, run_tool
from app.services.ask_resolver import resolve_question, resolve_customer_alias, validate_model_call
from app.services.ask_answers import render_answer
from app.models import Customer

router = APIRouter(prefix="/ask", tags=["ask"])


@router.get("/suggestions")
async def suggestions():
    """Starter questions the frontend can show when the input is empty."""
    return {"suggestions": SUGGESTIONS, "supported_tools": list(SUPPORTED_TOOLS)}


@router.post("", response_model=AskResponse)
async def ask(payload: AskRequest, db: Session = Depends(get_db), merchant_id: str = Depends(get_merchant_id)):
    today = pkt_today()
    tool_call = resolve_question(payload.question, today)
    if tool_call is None:
        try:
            proposed = await get_adapter().interpret_question(payload.question, today)
            tool_call = validate_model_call(payload.question, proposed, today)
        except ProviderError as exc:
            raise AIUnavailableError("Question interpretation is unavailable. Try a supported example.") from exc

    ambiguous = []
    if tool_call.tool == "customer_outstanding" and tool_call.args.get("name"):
        names = [row[0] for row in db.query(Customer.display_name).filter(Customer.merchant_id == merchant_id).all()]
        name, ambiguous = resolve_customer_alias(tool_call.args["name"], names)
        tool_call.args = {"name": name}

    # Step 2: compute the answer deterministically from the confirmed ledger.
    data = {"status": "ambiguous", "candidates": ambiguous} if ambiguous else run_tool(db, tool_call.tool, tool_call.args, today, merchant_id=merchant_id)
    if tool_call.tool == "unsupported" and tool_call.args.get("reason"):
        data["reason"] = tool_call.args["reason"]
        if tool_call.args.get("clarify"):
            data["status"] = "needs_clarification"
    return AskResponse(answer=render_answer(payload.question, tool_call.tool, data), tool_used=tool_call.tool, provider=tool_call.provider or "rules", data=data)
