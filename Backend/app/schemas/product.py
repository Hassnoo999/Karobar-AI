"""Strict input contract for the existing rupee-shaped product bridge."""
from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class ProductEventCreate(BaseModel):
    event_type: Literal["sale", "expense", "credit_given", "credit_received"]
    amount: Decimal = Field(gt=0, allow_inf_nan=False, max_digits=15, decimal_places=2)
    date: date
    customer_name: str | None = Field(None, max_length=120)
    source: Literal["voice", "photo", "manual", "seed"] = "manual"
    confidence: float | None = Field(None, ge=0, le=1)
    raw_input: str | None = None
    ai_provider: str | None = Field(None, max_length=16)
    evidence_filename: str | None = None
    notes: str | None = None
