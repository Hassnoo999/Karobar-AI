"""Ask Karobaar contracts."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator


class AskRequest(BaseModel):
    question: str = Field(min_length=2, max_length=500)

    @field_validator("question", mode="before")
    @classmethod
    def trim_question(cls, value):
        return value.strip() if isinstance(value, str) else value


class AskResponse(BaseModel):
    answer: str
    tool_used: str
    provider: str
    answer_source: str = "deterministic_ledger"
    data: dict[str, Any] = Field(default_factory=dict)
