"""
Phase 5 — Income source & reliability schemas (Pydantic).

Request/response contracts for the income-source and reliability APIs.
As with Phase 4's goal.py/financial_state.py split: *configuration*
(IncomeSourceCreate/Read) lives here alongside the raw observation
contracts, while the *computed* reliability breakdown
(IncomeReliabilityRead) is also here but is always derived — nothing in
this file is itself persisted as the reliability score except via the
explicit cache fields on IncomeSourceRead.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from app.core.vocabulary import Currency, EventSourceType, IncomeSourceCategory


class IncomeSourceCreate(BaseModel):
    """Phase 6: no `user_id` field — the source's owner is always the
    authenticated caller (see api/routers/income_sources.py)."""

    name: str = Field(..., min_length=1, max_length=120)
    category: IncomeSourceCategory
    currency: Currency
    typical_amount: Optional[Decimal] = Field(default=None, gt=0)


class IncomeSourceUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    typical_amount: Optional[Decimal] = Field(default=None, gt=0)


class IncomeSourceRead(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    user_id: str
    name: str
    category: IncomeSourceCategory
    currency: Currency
    typical_amount: Optional[Decimal]
    cached_reliability_score: Optional[Decimal]
    cached_observation_count: int
    cached_is_provisional: Optional[bool]
    cached_calculated_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class IncomePaymentObservationCreate(BaseModel):
    """Input for recording one expected-vs-actual payment outcome.

    `was_received=False` records a miss (invoice never paid, payment
    cancelled) — `actual_date`/`actual_amount` must be omitted in that
    case; both are required when the payment *was* received, enforced
    below the same way the ORM's check constraint enforces it at the
    database layer.
    """

    was_received: bool = True
    expected_date: Optional[datetime] = None
    actual_date: Optional[datetime] = None
    expected_amount: Optional[Decimal] = Field(default=None, gt=0)
    actual_amount: Optional[Decimal] = Field(default=None, gt=0)
    source_type: EventSourceType
    source_event_id: Optional[str] = None

    @model_validator(mode="after")
    def _actuals_match_received_flag(self) -> "IncomePaymentObservationCreate":
        if self.was_received:
            if self.actual_date is None or self.actual_amount is None:
                raise ValueError("actual_date and actual_amount are required when was_received is true.")
        else:
            if self.actual_date is not None or self.actual_amount is not None:
                raise ValueError("actual_date/actual_amount must be omitted when was_received is false.")
        return self


class IncomePaymentObservationRead(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    income_source_id: str
    user_id: str
    was_received: bool
    expected_date: Optional[datetime]
    actual_date: Optional[datetime]
    expected_amount: Optional[Decimal]
    actual_amount: Optional[Decimal]
    source_type: EventSourceType
    source_event_id: Optional[str]
    created_at: datetime


class IncomeReliabilityRead(BaseModel):
    """Output of `GET /api/income-sources/{id}/reliability` (spec 4.3).

    Always carries `observation_count` and `is_provisional` alongside the
    score itself — the spec is explicit that "82% reliable (24 payments)"
    and "60% reliable (2 payments, provisional)" must stay visibly
    distinct claims, never conflated into a bare percentage.
    """

    income_source_id: str
    category: IncomeSourceCategory
    reliability_score: Decimal = Field(..., ge=0, le=1)
    observation_count: int
    is_provisional: bool = Field(
        description="True while observation_count < COLD_START_FULL_TRUST_OBSERVATIONS (10) — "
        "the score still includes some weight on the category default."
    )
    category_default_used: Decimal = Field(
        description="The category default this score is blended against (or fully equal to, below 3 observations)."
    )
    observed_score: Optional[Decimal] = Field(
        default=None,
        description="The raw score computed purely from this source's own history "
        "(None until at least 1 observation exists).",
    )
    blend_weight_on_observed: Decimal = Field(
        description="0.0 below 3 observations, rising linearly to 1.0 at 10+ (spec 4.3 cold-start ramp)."
    )
    timeliness_score: Optional[Decimal] = Field(default=None, description="50% weight sub-score.")
    amount_consistency_score: Optional[Decimal] = Field(default=None, description="30% weight sub-score.")
    data_confidence_score: Optional[Decimal] = Field(default=None, description="20% weight sub-score.")
    calculated_at: datetime
