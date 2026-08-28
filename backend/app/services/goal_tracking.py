"""
Phase 4 — Goal tracking service.

Two responsibilities, kept deliberately separate:
  1. CRUD on the goal's *target* (create/update/list) — a plain mutable
     row, since a target is configuration, not history.
  2. Computing a goal's *progress*, which is always derived fresh from
     the event ledger (+ current balance for reserves) — never stored,
     so progress can never drift out of sync with what actually happened.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.vocabulary import EventDirection, EventStatus, GoalType
from app.models.financial_event import FinancialEventORM
from app.models.goal import GoalORM
from app.schemas.goal import GoalCreate, GoalUpdate


def create_goal(session: Session, user_id: str, payload: GoalCreate) -> GoalORM:
    goal = GoalORM(
        user_id=user_id,
        name=payload.name,
        goal_type=payload.goal_type.value,
        currency=payload.currency.value,
        linked_category=payload.linked_category.value,
        target_amount=payload.target_amount,
        target_date=payload.target_date,
    )
    session.add(goal)
    session.flush()
    return goal


def update_goal(session: Session, goal_id: str, payload: GoalUpdate) -> GoalORM:
    goal = _get_or_raise(session, goal_id)
    if payload.name is not None:
        goal.name = payload.name
    if payload.target_amount is not None:
        goal.target_amount = payload.target_amount
    if payload.target_date is not None:
        goal.target_date = payload.target_date
    session.flush()
    return goal


def list_goals(session: Session, user_id: str) -> list[GoalORM]:
    stmt = select(GoalORM).where(GoalORM.user_id == user_id).order_by(GoalORM.created_at)
    return list(session.execute(stmt).scalars().all())


def get_goal(session: Session, goal_id: str) -> Optional[GoalORM]:
    return session.get(GoalORM, goal_id)


def _get_or_raise(session: Session, goal_id: str) -> GoalORM:
    goal = session.get(GoalORM, goal_id)
    if goal is None:
        raise LookupError(f"No goal with id={goal_id}")
    return goal


class GoalProgressResult:
    """Plain data holder so this module doesn't need to import the
    Pydantic GoalProgress model from schemas/financial_state.py (which
    would create a schemas<->services import cycle, since financial_state
    itself will call into this module)."""

    def __init__(
        self,
        *,
        current_amount: Decimal,
        contributing_event_count: int,
        percent_complete: float,
        is_reserve: bool,
    ) -> None:
        self.current_amount = current_amount
        self.contributing_event_count = contributing_event_count
        self.percent_complete = percent_complete
        self.is_reserve = is_reserve


def compute_goal_progress(
    goal: GoalORM,
    events: list[FinancialEventORM],
    confirmed_balance: Decimal,
) -> GoalProgressResult:
    """Pure function: goal + ledger events (+ current balance) in, progress
    out. Mirrors rebuild_financial_state's "always a pure function of the
    ledger" invariant — nothing about a goal's progress is stored.

    SAVINGS_TARGET: sums CONFIRMED, currency-matching CREDIT events whose
    category matches the goal's linked_category, from goal creation
    onward — only confirmed money counts toward a savings target, the
    same way only confirmed money counts toward the account balance.

    RESERVE_TARGET: progress is simply "how much of the current confirmed
    balance is available to cushion the target" — a reserve isn't
    something you accumulate via tagged events, it's a level the account
    balance either meets or doesn't right now.
    """
    if goal.goal_type == GoalType.RESERVE_TARGET.value:
        current = confirmed_balance
        percent = _percent(current, goal.target_amount)
        return GoalProgressResult(
            current_amount=current,
            contributing_event_count=0,
            percent_complete=percent,
            is_reserve=True,
        )

    contributing = [
        e
        for e in events
        if e.user_id == goal.user_id
        and e.currency == goal.currency
        and e.direction == EventDirection.CREDIT.value
        and e.status == EventStatus.CONFIRMED.value
        and e.category == goal.linked_category
        and e.event_date >= goal.created_at
    ]
    current = sum((e.amount for e in contributing), Decimal("0"))
    percent = _percent(current, goal.target_amount)
    return GoalProgressResult(
        current_amount=current,
        contributing_event_count=len(contributing),
        percent_complete=percent,
        is_reserve=False,
    )


def _percent(current: Decimal, target: Decimal) -> float:
    if target <= 0:
        return 0.0
    return float(min(current / target, Decimal("1")) * 100)
