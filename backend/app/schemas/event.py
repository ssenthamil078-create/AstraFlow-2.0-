"""
Phase 2 — Financial event schemas (Pydantic).

These are the request/response contracts the ingestion APIs (Phase 3) will
use, and what every later phase reads events back as. The ORM model
(models/financial_event.py) is the storage shape; these are the validated
shape at the boundary — kept deliberately separate so a storage-layer detail
never leaks into the API contract.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from app.core.vocabulary import (
    CorrectionReason,
    Currency,
    EventDirection,
    EventSourceType,
    EventStatus,
    EventType,
)
from app.schemas.provenance import SourceProvenance


class FinancialEventCreate(BaseModel):
    """Input shape for creating a new event. Every ingestion path in Phase 3
    (CSV row, pasted SMS, OCR'd document) normalizes into this before it
    reaches the event ledger service."""

    user_id: str = Field(..., min_length=1)
    event_type: EventType
    direction: EventDirection
    amount: Decimal = Field(..., gt=0, description="Always a positive magnitude; direction carries the sign.")
    currency: Currency
    event_date: datetime
    category: Optional[str] = None
    status: EventStatus = EventStatus.LIKELY
    confidence: Decimal = Field(..., ge=0, le=1)
    provenance: SourceProvenance
    recurrence_group_id: Optional[str] = None

    @model_validator(mode="after")
    def _confidence_matches_status(self) -> "FinancialEventCreate":
        # A CONFIRMED event is, by definition, fully trusted — its confidence
        # can't be anything other than 1.0. An UNCERTAIN/LIKELY event can't
        # claim full confidence, or it should have been marked CONFIRMED.
        if self.status == EventStatus.CONFIRMED and self.confidence != Decimal("1"):
            raise ValueError("A CONFIRMED event must have confidence == 1.0.")
        if self.status in (EventStatus.LIKELY, EventStatus.UNCERTAIN) and self.confidence == Decimal("1"):
            raise ValueError(
                f"An event with status={self.status.value} cannot have confidence == 1.0; "
                "mark it CONFIRMED instead if it's fully trusted."
            )
        return self


class FinancialEventRead(BaseModel):
    """Output shape — what API #1 (`GET /api/events`, Phase 3) returns."""

    model_config = {"from_attributes": True}

    id: str
    user_id: str
    event_type: EventType
    direction: EventDirection
    amount: Decimal
    currency: Currency
    event_date: datetime
    category: Optional[str]
    status: EventStatus
    confidence: Decimal
    source_type: EventSourceType
    source_reference: Optional[str]
    recurrence_group_id: Optional[str]
    supersedes_event_id: Optional[str]
    correction_reason: Optional[CorrectionReason]
    created_at: datetime
    confirmed_at: Optional[datetime]


class FinancialEventCorrection(BaseModel):
    """Input shape for correcting an existing event (spec: ledger is
    immutable, so this creates a NEW event that supersedes the old one —
    see services/event_ledger.py::correct_event). Only the fields that
    changed need to be supplied; everything else is copied from the
    original."""

    reason: CorrectionReason
    amount: Optional[Decimal] = Field(default=None, gt=0)
    currency: Optional[Currency] = None
    event_date: Optional[datetime] = None
    category: Optional[str] = None
    status: Optional[EventStatus] = None
    confidence: Optional[Decimal] = Field(default=None, ge=0, le=1)

    @model_validator(mode="after")
    def _at_least_one_field_changed(self) -> "FinancialEventCorrection":
        changed = any(
            getattr(self, f) is not None
            for f in ("amount", "currency", "event_date", "category", "status", "confidence")
        )
        if not changed:
            raise ValueError("A correction must change at least one field.")
        return self
