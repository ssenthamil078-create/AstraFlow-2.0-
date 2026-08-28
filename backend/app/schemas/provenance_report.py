"""
Phase 4 — Financial-state provenance report.

Backs `GET /api/financial-state/provenance` (spec 6.1, API #6). Every
number the twin shows (confirmed balance, each obligation, each goal's
progress) is traceable back to the exact events that produced it — this
is the "explainability" half of the spec's success metrics table, applied
to the twin itself rather than to a risk action card.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.core.vocabulary import Currency, EventDirection, EventSourceType, EventStatus


class ProvenanceEventRef(BaseModel):
    model_config = {"from_attributes": True}

    event_id: str
    source_type: EventSourceType
    status: EventStatus
    confidence: Decimal
    direction: EventDirection
    amount: Decimal
    event_date: datetime


class FinancialStateProvenance(BaseModel):
    user_id: str
    currency: Currency
    generated_at: datetime
    confirmed_balance_events: list[ProvenanceEventRef]
    obligations: dict[str, list[ProvenanceEventRef]]
    goals: dict[str, list[ProvenanceEventRef]]
