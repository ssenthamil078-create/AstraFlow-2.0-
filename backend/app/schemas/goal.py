"""
Phase 4 — Goal schemas (Pydantic).

Request/response contracts for goal creation and updates. Goal *progress*
is not part of this module — it's derived from the ledger and lives in
schemas/financial_state.py (GoalProgress), since progress is a read model
over the twin, not something a goal stores about itself.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from app.core.vocabulary import Currency, GoalType, ObligationCategory


class GoalCreate(BaseModel):
    """Phase 6: no `user_id` field — the goal's owner is always the
    authenticated caller (see api/routers/goals.py)."""

    name: str = Field(..., min_length=1, max_length=120)
    goal_type: GoalType
    currency: Currency
    linked_category: ObligationCategory
    target_amount: Decimal = Field(..., gt=0)
    target_date: Optional[datetime] = None


class GoalUpdate(BaseModel):
    """Only a target changing — the user's mind about how much/when they
    want to save — not a correction to history, so this is a plain
    in-place update, unlike a financial event."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    target_amount: Optional[Decimal] = Field(default=None, gt=0)
    target_date: Optional[datetime] = None


class GoalRead(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    user_id: str
    name: str
    goal_type: GoalType
    currency: Currency
    linked_category: ObligationCategory
    target_amount: Decimal
    target_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
