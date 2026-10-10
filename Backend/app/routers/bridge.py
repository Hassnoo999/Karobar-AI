"""Frontend-compatible adapter endpoints.

Translates between the frontend's expected API shapes (rupee floats, sale/credit_given
event types, combined intelligence response) and the backend's internal models (paisa
integers, cash_sale/credit_sale, separate passport + readiness endpoints).

This router MUST be registered before demo.py in ALL_ROUTERS so that its POST
/demo/seed endpoint takes priority over the simpler one in demo.py.
"""
from __future__ import annotations

import logging
import time as _time
import uuid
from datetime import date, datetime

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.ai import get_adapter
from app.ai.base import ProviderError
from app.auth import get_merchant_id
from app.config import settings
from app.data.seed import load_seed
from app.db import get_db, pkt_today
from app.errors import AIUnavailableError, DomainValidationError
from app.models import BusinessEvent, Customer
from app.schemas.events import EventCreate, EventType, PaymentStatus, SourceType, VerificationStatus
from app.schemas.product import ProductEventCreate
from app.services.product_cache import combined_cache as _combined_cache
from app.services.ledger import (
    confirm_event,
    customer_oldest_unpaid,
    customer_outstanding_paisa,
    event_to_out,
    find_customer_by_name,
    normalize_name,
)
from app.services.matching import evaluate_readiness, load_programs
from app.services.metrics import dashboard_bundle
from app.services.metrics import _fetch_confirmed_events, _fetch_customers
from app.services.money import format_pkr
from app.services.passport import compute_passport
from app.routers.demo import require_local_demo

router = APIRouter(tags=["bridge"])

# In-memory cache for the combined endpoint (30 s TTL per merchant)
_CACHE_TTL = 30  # local only; deployed instances cannot invalidate one another

# ---------------------------------------------------------------------------
# Type translation tables
# ---------------------------------------------------------------------------

# Backend -> Frontend event type
_FE_EVENT_TYPE = {
    "cash_sale": "sale",
    "credit_sale": "credit_given",
    "payment_received": "credit_received",
    "expense": "expense",
}

# Frontend -> Backend event type
_BE_EVENT_TYPE = {
    "sale": "cash_sale",
    "expense": "expense",
    "credit_given": "credit_sale",
    "credit_received": "payment_received",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _event_to_fe(event: BusinessEvent, customer_name: str | None) -> dict:
    """Convert a backend BusinessEvent to the frontend's StoredLedgerEvent shape."""
    name = customer_name or getattr(event, "counterparty_raw", None)
    be_type = event.event_type.value if hasattr(event.event_type, "value") else event.event_type
    source = event.source_type.value if hasattr(event.source_type, "value") else event.source_type
    et = _FE_EVENT_TYPE.get(be_type)
    return {
        "id": event.id,
        "event_type": et,
        "payment_type": "credit" if et in ("credit_given", "credit_received") else "cash",
        "customer_name": name or ("Business expense" if et == "expense" else "Walk-in"),
        "amount": round(event.amount_paisa / 100, 2),
        "currency": "PKR",
        "date": event.occurred_at.isoformat(),
        "confidence": event.ai_confidence,
        "source": "photo" if source == "receipt" else source,
        "raw_input": event.raw_input or "",
        "status": "validated",
        "validation_notes": [],
        "customer_id": event.customer_id,
        "remaining_amount": round((event.amount_paisa - event.settled_paisa) / 100, 2) if be_type == "credit_sale" else None,
        "ai_provider": event.ai_provider,
        "evidence_filename": event.evidence_filename,
        "notes": event.notes,
        "created_at": event.created_at.isoformat() if event.created_at else datetime.now().isoformat(),
    }


def _draft_to_fe_event(draft, raw_text: str | None = None) -> dict:
    """Convert a backend DraftEvent to the frontend's LedgerEvent shape."""
    et = _FE_EVENT_TYPE.get(draft.event_type.value) if draft.event_type else None
    amount = round(draft.amount_paisa / 100, 2) if draft.amount_paisa is not None else None
    missing = list(draft.missing_fields) if draft.missing_fields else []
    status = "validated" if not missing else "pending_validation"
    return {
        "event_type": et,
        "payment_type": "credit" if et in ("credit_given", "credit_received") else "cash",
        "customer_name": draft.customer_name or draft.counterparty or None,
        "amount": amount,
        "currency": "PKR",
        "date": draft.occurred_at.isoformat() if draft.occurred_at else None,
        "confidence": draft.confidence,
        "source": "photo" if draft.source_type == SourceType.receipt else draft.source_type.value,
        "raw_input": draft.raw_input or raw_text or "",
        "status": status,
        "validation_notes": missing,
        "evidence_filename": draft.evidence_filename,
        "ai_provider": draft.provider,
        "possible_duplicate": draft.possible_duplicate,
        "duplicate_of": draft.duplicate_of,
        "notes": draft.notes,
    }


def _summary_from_dashboard(dash, *, record_count: int | None = None) -> dict:
    """Convert a DashboardResponse to the frontend's LedgerSummary shape."""
    total_sales = round(dash.month_sales_paisa / 100, 2)
    total_expenses = round(dash.month_expenses_paisa / 100, 2)
    total_receivables = round(dash.outstanding_total_paisa / 100, 2)
    total_payables = round(dash.overdue_total_paisa / 100, 2)

    recent = [_event_to_fe(ev, ev.customer_name) for ev in dash.recent_events]

    return {
        "total_sales": total_sales,
        "total_expenses": total_expenses,
        "total_receivables": total_receivables,
        "total_payables": total_payables,
        "total_recovered": round(dash.month_recovered_paisa / 100, 2),
        "net_cash": round(total_sales - total_expenses, 2),
        "record_count": record_count if record_count is not None else len(dash.recent_events),
        "recent_events": recent,
    }


def _find_customer_in_text(db: Session, text: str, merchant_id: str = "demo") -> Customer | None:
    """Try to find a known customer mentioned in the transcript text."""
    normalized = normalize_name(text)
    # Exact match first
    exact = find_customer_by_name(db, text.strip(), merchant_id=merchant_id)
    if exact:
        return exact
    # Substring match: check if any customer name appears in the transcript
    for customer in db.query(Customer).filter(Customer.merchant_id == merchant_id).all():
        if customer.name_normalized in normalized:
            return customer
    return None


# ---------------------------------------------------------------------------
# GET /config/ai-provider
# ---------------------------------------------------------------------------


@router.get("/config/ai-provider")
async def get_config():
    chain = settings.provider_chain()
    selected = chain[0] if chain else "demo"

    # The frontend references "alibaba" as a legacy provider name;
    # we map our actual providers to the shape it expects.
    fe_selected = "groq" if selected == "groq" else ("demo" if selected == "demo" else "groq")

    return {
        "selected_provider": fe_selected,
        "mode": settings.ai_provider,
        "configured": {
            "alibaba": False,
            "groq": bool(settings.groq_api_key),
        },
        "models": {
            "alibaba": None,
            "groq_text": settings.groq_text_model,
            "groq_vision": settings.groq_vision_model,
            "groq_transcribe": settings.groq_audio_model,
        },
        "missing_required_env": [] if settings.groq_api_key else ["GROQ_API_KEY"],
        "message": f"Active chain: {' → '.join(chain)}",
    }


# ---------------------------------------------------------------------------
# POST /understand/voice  —  transcribe + extract in one call
# ---------------------------------------------------------------------------

MAX_AUDIO_BYTES = 4 * 1024 * 1024


@router.post("/understand/voice")
async def understand_voice(
    db: Session = Depends(get_db),
    file: UploadFile = File(..., description="Audio recording"),
    merchant_id: str = Depends(get_merchant_id),
):
    audio = await file.read(MAX_AUDIO_BYTES + 1)
    if not audio:
        raise DomainValidationError("audio file is empty")
    if len(audio) > MAX_AUDIO_BYTES:
        raise DomainValidationError("audio file too large (max 4 MB; use a short voice note)")
    mime = (file.content_type or "audio/webm").split(";")[0].strip().lower()
    if not (mime.startswith("audio/") or mime == "video/webm"):
        raise DomainValidationError(f"unsupported audio type: {mime}")

    adapter = get_adapter()
    today = pkt_today()

    # Step 1: transcribe
    try:
        transcript_result = await adapter.transcribe_audio(audio, mime)
    except ProviderError as exc:
        raise AIUnavailableError(str(exc)) from exc

    # Step 2: extract structured event from transcript
    try:
        extraction = await adapter.extract_event_from_text(transcript_result.text, today)
    except ProviderError as exc:
        raise AIUnavailableError(str(exc)) from exc

    from app.services.ledger import build_draft

    draft = await run_in_threadpool(build_draft,
        db, extraction,
        source_type=SourceType.voice,
        raw_input=transcript_result.text,
        evidence_filename=None,
        merchant_id=merchant_id,
    )

    return {
        "capture": {
            "capture_id": uuid.uuid4().hex,
            "kind": "voice",
            "filename": None,
            "content_type": mime,
            "size_bytes": len(audio),
            "stored": False,
            "received_at": datetime.now().isoformat(),
            "next_step": "Review the extracted event and confirm.",
        },
        "provider": draft.provider,
        "event": _draft_to_fe_event(draft, transcript_result.text),
    }


# ---------------------------------------------------------------------------
# POST /understand/receipt  —  save image + extract in one call
# ---------------------------------------------------------------------------

MAX_IMAGE_BYTES = 4 * 1024 * 1024

_IMAGE_EXTS = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/heic": ".heic",
    "image/heif": ".heif",
}


@router.post("/understand/receipt")
async def understand_receipt(
    db: Session = Depends(get_db),
    file: UploadFile = File(..., description="Receipt photo"),
    merchant_id: str = Depends(get_merchant_id),
):
    image = await file.read(MAX_IMAGE_BYTES + 1)
    if not image:
        raise DomainValidationError("image file is empty")
    if len(image) > MAX_IMAGE_BYTES:
        raise DomainValidationError("image file too large (max 4 MB)")
    mime = (file.content_type or "").split(";")[0].strip().lower()
    if mime not in _IMAGE_EXTS:
        raise DomainValidationError(f"unsupported image type: {mime}")

    from app.services.evidence_storage import discard_receipt, store_receipt

    from starlette.concurrency import run_in_threadpool
    filename = await run_in_threadpool(store_receipt, image, _IMAGE_EXTS[mime], merchant_id)

    adapter = get_adapter()
    today = pkt_today()

    try:
        extraction = await adapter.extract_event_from_image(image, mime, today)
    except ProviderError as exc:
        await run_in_threadpool(discard_receipt, filename, merchant_id)
        raise AIUnavailableError(str(exc)) from exc

    from app.services.ledger import build_draft

    draft = await run_in_threadpool(build_draft,
        db, extraction,
        source_type=SourceType.receipt,
        raw_input=None,
        evidence_filename=filename,
        merchant_id=merchant_id,
    )

    return {
        "capture": {
            "capture_id": uuid.uuid4().hex,
            "kind": "receipt",
            "filename": filename,
            "content_type": mime,
            "size_bytes": len(image),
            "stored": True,
            "received_at": datetime.now().isoformat(),
            "path": f"/api/evidence/files/{filename}",
            "next_step": "Review the extracted event and confirm.",
        },
        "provider": draft.provider,
        "event": _draft_to_fe_event(draft),
    }


# ---------------------------------------------------------------------------
# GET /ledger/summary
# ---------------------------------------------------------------------------


@router.get("/ledger/summary")
def ledger_summary(db: Session = Depends(get_db), merchant_id: str = Depends(get_merchant_id)):
    dash = dashboard_bundle(db, merchant_id=merchant_id)
    record_count = int(
        db.query(BusinessEvent)
        .filter(
            BusinessEvent.merchant_id == merchant_id,
            BusinessEvent.verification_status == VerificationStatus.confirmed.value,
        )
        .count()
    )
    return _summary_from_dashboard(dash, record_count=record_count)


# ---------------------------------------------------------------------------
# GET /ledger/events
# ---------------------------------------------------------------------------


@router.get("/ledger/events")
def ledger_events(db: Session = Depends(get_db), merchant_id: str = Depends(get_merchant_id)):
    rows = (
        db.query(BusinessEvent, Customer.display_name)
        .outerjoin(Customer, BusinessEvent.customer_id == Customer.id)
        .filter(
            BusinessEvent.merchant_id == merchant_id,
            BusinessEvent.verification_status == VerificationStatus.confirmed.value,
        )
        .order_by(BusinessEvent.occurred_at.desc(), BusinessEvent.id.desc())
        .limit(200)
        .all()
    )
    return [_event_to_fe(ev, name) for ev, name in rows]


# ---------------------------------------------------------------------------
# POST /ledger/events  —  save a frontend-shaped event to the ledger
# ---------------------------------------------------------------------------


@router.post("/ledger/events", status_code=201)
def save_ledger_event(payload: ProductEventCreate, db: Session = Depends(get_db), merchant_id: str = Depends(get_merchant_id)):
    be_type = _BE_EVENT_TYPE[payload.event_type]
    # Input allows two decimal places, so this conversion is exact, not float rounding.
    amount_paisa = int(payload.amount * 100)
    counterparty = (payload.customer_name or "").strip() or None

    event_create = EventCreate(
        event_type=EventType(be_type),
        counterparty=counterparty,
        amount_paisa=amount_paisa,
        occurred_at=payload.date,
        payment_status=(
            PaymentStatus.outstanding if be_type == "credit_sale"
            else PaymentStatus.paid if be_type in ("cash_sale", "expense")
            else None
        ),
        source_type=SourceType.receipt if payload.source == "photo" else SourceType(payload.source),
        raw_input=payload.raw_input,
        ai_confidence=payload.confidence,
        ai_provider=payload.ai_provider,
        evidence_filename=payload.evidence_filename,
        notes=payload.notes,
    )

    event, _ = confirm_event(db, event_create, merchant_id=merchant_id)
    _combined_cache.pop(merchant_id, None)  # invalidate combined cache
    out = event_to_out(event)
    return _event_to_fe(event, out.customer_name)


# ---------------------------------------------------------------------------
# GET /intelligence  —  evidence profile + financing matches + summary
# ---------------------------------------------------------------------------


def _evidence_profile(passport) -> dict:
    """Describe the same canonical facts on both bridge read endpoints."""
    return {
        "documentation_coverage": f"{passport.evidence_coverage_pct}% of confirmed activity includes a receipt attachment",
        "income_consistency": f"Sales recorded across {passport.history_months} months — {passport.revenue_consistency}",
        "receivable_discipline": (
            f"{passport.recovery_rate_pct:.1f}% repayments relative to recorded credit sales"
            if passport.recovery_rate_pct is not None else "No credit sales recorded yet"
        ),
        "expense_pattern": "Expense entries are recorded activity; cost patterns have not been established",
        "customer_concentration": (
            f"Largest customer's share of all recorded credit sales: {passport.customer_concentration_pct:.1f}%"
            if passport.customer_concentration_pct is not None else "No credit customers yet"
        ),
        "ledger_depth": f"{passport.total_recorded_events} merchant-confirmed records across {passport.history_months} months; not independently audited",
        "trust_notes": [
            "Only confirmed entries count; sample and manual sources remain labeled",
            "Attachments are not independently authenticated documents",
            "No personalized financing fit or qualification is inferred",
        ],
    }


def _financing_references(readiness) -> list[dict]:
    """Legacy frontend shape retained; unsupported fit badges are removed."""
    return [{
        "program": {
            "id": item.program.id, "name": item.program.program_name,
            "institution": item.program.provider, "product_type": "small business finance reference",
            "target_customer": item.program.target_user,
            "eligibility_notes": "Reference only. Confirm current conditions directly with the institution; no personalized fit is inferred.",
            "loan_range": "Confirm current amounts and terms with the institution",
            "required_documents": [requirement.label for requirement in item.not_verifiable],
            "source_url": item.program.source_url, "last_checked": item.program.last_verified,
            "matching_hints": ["Official reference only; manual confirmation required"],
        },
        "relevance": "low", "match_reasons": [],
        "gaps": [requirement.next_step or requirement.label for requirement in item.not_verifiable],
        "grounded_summary": item.summary_line,
    } for item in readiness]


@router.get("/intelligence")
def intelligence(db: Session = Depends(get_db), merchant_id: str = Depends(get_merchant_id)):
    passport = compute_passport(db, merchant_id=merchant_id)
    readiness = evaluate_readiness(db, merchant_id=merchant_id, passport=passport)
    dash = dashboard_bundle(db, merchant_id=merchant_id)
    summary = _summary_from_dashboard(dash, record_count=passport.total_recorded_events)

    evidence_profile = _evidence_profile(passport)
    financing_matches = _financing_references(readiness)

    return {
        "evidence_profile": evidence_profile,
        "financing_matches": financing_matches,
        "summary": summary,
    }


# ---------------------------------------------------------------------------
# POST /actions/reminder/draft  —  voice-based reminder flow
# ---------------------------------------------------------------------------


def _voice_reminder_context(db: Session, command_text: str, merchant_id: str):
    """No ORM objects/connection are carried across the provider await."""
    try:
        customer = _find_customer_in_text(db, command_text, merchant_id=merchant_id)
        if customer is None:
            return None
        outstanding = customer_outstanding_paisa(db, customer.id)
        oldest_unpaid = customer_oldest_unpaid(db, customer.id) if outstanding > 0 else None
        event_count = int(db.query(BusinessEvent).filter(
            BusinessEvent.merchant_id == merchant_id,
            BusinessEvent.customer_id == customer.id,
            BusinessEvent.verification_status == VerificationStatus.confirmed.value,
        ).count() or 0) if outstanding > 0 else 0
        return customer.display_name, outstanding, oldest_unpaid, event_count
    finally:
        db.close()


@router.post("/actions/reminder/draft")
async def reminder_draft(
    db: Session = Depends(get_db),
    file: UploadFile = File(..., description="Voice command audio"),
    merchant_id: str = Depends(get_merchant_id),
):
    audio = await file.read(MAX_AUDIO_BYTES + 1)
    if not audio:
        raise DomainValidationError("audio file is empty")
    if len(audio) > MAX_AUDIO_BYTES:
        raise DomainValidationError("audio file too large (max 4 MB; use a short voice note)")
    mime = (file.content_type or "audio/webm").split(";")[0].strip().lower()

    adapter = get_adapter()

    # Step 1: transcribe the voice command
    try:
        transcript_result = await adapter.transcribe_audio(audio, mime)
    except ProviderError as exc:
        raise AIUnavailableError(str(exc)) from exc

    command_text = transcript_result.text

    # Step 2: find the customer mentioned in the command
    context = await run_in_threadpool(_voice_reminder_context, db, command_text, merchant_id)
    if context is None:
        return {
            "command_text": command_text,
            "customer_name": None,
            "balance": None,
            "draft_message": None,
            "status": "not_found",
            "channel": "draft_on_screen",
            "notes": ["Could not identify a customer from the voice command."],
        }

    # Step 3: check outstanding balance
    customer_name, outstanding, oldest_unpaid, event_count = context
    if outstanding <= 0:
        return {
            "command_text": command_text,
            "customer_name": customer_name,
            "balance": {
                "customer_name": customer_name,
                "receivable_balance": 0,
                "currency": "PKR",
                "event_count": 0,
            },
            "draft_message": None,
            "status": "no_balance",
            "channel": "draft_on_screen",
            "notes": [f"{customer_name} has no outstanding udhaar."],
        }

    # Step 4: draft the reminder message via AI
    try:
        result = await adapter.draft_reminder(
            customer_name, outstanding, oldest_unpaid, tone="friendly"
        )
    except ProviderError:
        # Fallback draft message if AI is unavailable
        rupees = outstanding / 100
        draft_msg = (
            f"Assalam o Alaikum {customer_name} bhai, "
            f"aap ke zimay PKR {rupees:,.0f} baqi hain. "
            f"Barah-e-karam jab mumkin ho payment kar dein. Shukriya."
        )
        provider_name = "fallback"
    else:
        draft_msg = result.text
        provider_name = result.provider

    return {
        "command_text": command_text,
        "customer_name": customer_name,
        "balance": {
            "customer_name": customer_name,
            "receivable_balance": round(outstanding / 100, 2),
            "currency": "PKR",
            "event_count": event_count,
        },
        "draft_message": draft_msg,
        "status": "drafted",
        "channel": "draft_on_screen",
        "notes": [
            f"Oldest unpaid entry: {oldest_unpaid.isoformat()}" if oldest_unpaid else "No specific unpaid date found.",
            f"Draft prepared using {provider_name} provider.",
        ],
    }


# ---------------------------------------------------------------------------
# POST /demo/seed  —  seed and return events in frontend shape
# ---------------------------------------------------------------------------


@router.post("/demo/seed", dependencies=[Depends(require_local_demo)])
def demo_seed(db: Session = Depends(get_db), merchant_id: str = Depends(get_merchant_id)):
    load_seed(db, merchant_id=merchant_id)
    _combined_cache.pop(merchant_id, None)  # invalidate combined cache
    rows = (
        db.query(BusinessEvent, Customer.display_name)
        .outerjoin(Customer, BusinessEvent.customer_id == Customer.id)
        .filter(
            BusinessEvent.merchant_id == merchant_id,
            BusinessEvent.verification_status == VerificationStatus.confirmed.value,
        )
        .order_by(BusinessEvent.occurred_at.desc(), BusinessEvent.id.desc())
        .all()
    )
    return [_event_to_fe(ev, name) for ev, name in rows]


# ---------------------------------------------------------------------------
# GET /combined  —  single-request data load (summary + events + intelligence)
# ---------------------------------------------------------------------------


@router.get("/combined")
def combined_data(db: Session = Depends(get_db), merchant_id: str = Depends(get_merchant_id)):
    """Return ALL data in a single request to eliminate 3x network round-trips.

    Results are cached for 30 seconds per merchant.  The cache is invalidated
    when a new event is saved (POST /ledger/events).
    """
    # Check cache first (skip DB work on cache hit)
    now = _time.time()
    cached = _combined_cache.get(merchant_id)
    if not settings.deployed and cached and now - cached[0] < _CACHE_TTL:
        return cached[1]

    # ── Fetch events + customers ONCE, reuse across all computations ──
    raw_events = _fetch_confirmed_events(db, merchant_id)
    customers = _fetch_customers(db, merchant_id)

    # Build frontend events list (sorted, limited)
    sorted_events = sorted(raw_events, key=lambda e: (e.occurred_at, e.id), reverse=True)[:200]
    fe_events = [
        _event_to_fe(ev, customers.get(ev.customer_id))
        for ev in sorted_events
    ]

    # ── Dashboard summary (reuses pre-fetched events + customers) ────
    dash = dashboard_bundle(db, merchant_id=merchant_id, _events=raw_events, _customers=customers)
    summary = _summary_from_dashboard(dash, record_count=len(raw_events))

    # ── Passport + readiness (reuses pre-fetched events) ──────────────
    passport = compute_passport(db, merchant_id=merchant_id, _events=raw_events)
    readiness = evaluate_readiness(db, merchant_id=merchant_id, passport=passport)

    evidence_profile = _evidence_profile(passport)
    financing_matches = _financing_references(readiness)

    result = {
        "summary": summary,
        "events": fe_events,
        "intelligence": {
            "evidence_profile": evidence_profile,
            "financing_matches": financing_matches,
        },
        # Reuse already fetched confirmed rows; no extra remote-DB round trips.
        "dashboard": dash.model_dump(mode="json"),
        "passport": passport.model_dump(mode="json"),
        "customers": _product_customers(raw_events, customers),
        "source_counts": {source: sum(ev.source_type == source for ev in raw_events) for source in ("voice", "receipt", "manual", "seed")},
    }
    if not settings.deployed:
        _combined_cache[merchant_id] = (_time.time(), result)
    return result


def _product_customers(events: list[BusinessEvent], names: dict[int, str]) -> list[dict]:
    """Expose settled balances from full history, never from the latest 200 rows."""
    result = {cid: {"id": cid, "name": name, "outstanding_paisa": 0,
                    "oldest_unpaid": None, "event_count": 0} for cid, name in names.items()}
    for event in events:
        customer = result.get(event.customer_id)
        if customer is None:
            continue
        customer["event_count"] += 1
        if event.event_type == "credit_sale" and event.amount_paisa > event.settled_paisa:
            customer["outstanding_paisa"] += event.amount_paisa - event.settled_paisa
            oldest = customer["oldest_unpaid"]
            customer["oldest_unpaid"] = min(oldest, event.occurred_at.isoformat()) if oldest else event.occurred_at.isoformat()
    return sorted(result.values(), key=lambda customer: (-customer["outstanding_paisa"], customer["name"].lower()))
