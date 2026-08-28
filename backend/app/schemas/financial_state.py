"""
Phase 2 — Financial-state ("digital twin") schema.
Phase 4 — extends the same shape with obligations, discretionary
spending, and goal/reserve progress (see bottom of this file).

Scope note: Phase 2 defines the *shape* of the twin and a correct but
minimal rebuild (confirmed balance + a breakdown of pending amounts by
status). It deliberately does NOT classify obligations, detect recurrence,
or track goals/reserves — that intelligence is Phase 4's job. Building the
full rebuild here would mean re-deriving Phase 4's logic ad hoc and then
throwing it away, which is exactly the kind of phase-boundary drift the
project plan is trying to avoid.

The one invariant that must hold from Phase 2 onward: the twin is ALWAYS a
pure function of the event ledger (Phase 4 adds goal *targets* as a second,
still-external, input — see rebuild_financial_state's `goals` parameter —
but a goal's target is configuration, not history, the same way an
emergency policy is; see models/goal.py). There is no code path that
writes to financial state directly — see services/event_ledger.py, which
has no "update balance" method, only "append event" and "rebuild state
from events".
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from app.core.vocabulary import Currency, EventDirection, EventStatus, GoalType, ObligationCategory
from app.models.financial_event import FinancialEventORM
from app.models.goal import GoalORM
from app.services import goal_tracking, obligation_detection


class StatusBreakdown(BaseModel):
    """Net signed total (credits − debits) and event count for one
    EventStatus bucket, so confirmed/likely/uncertain money is never
    silently summed together."""

    status: EventStatus
    net_amount: Decimal
    event_count: int


class ObligationSummary(BaseModel):
    """Phase 4. One recurring obligation group — spec's "rent/EMI/utility/
    subscription" detection. `recurrence_group_id` is None when the group
    was formed by category alone (no explicit recurrence link was set
    during ingestion) — still a valid, displayable obligation, just
    without a per-biller split."""

    category: ObligationCategory
    recurrence_group_id: Optional[str]
    average_amount: Decimal
    occurrence_count: int
    last_event_date: datetime
    interval_days_estimate: Optional[int] = Field(
        default=None, description="Median days between occurrences; None until a 2nd occurrence is seen."
    )
    next_expected_date: Optional[datetime] = None


class DiscretionarySpendingSummary(BaseModel):
    """Phase 4. Trailing-30-day FLEXIBLE_SPENDING total — what a policy's
    `reduce flexible_spending by X%` action (spec 4.5) operates on."""

    window_days: int = 30
    total: Decimal = Decimal("0")
    event_count: int = 0
    average_transaction: Decimal = Decimal("0")


class GoalProgress(BaseModel):
    """Phase 4. One goal or reserve target plus its ledger-derived
    progress — see services/goal_tracking.compute_goal_progress for how
    `current_amount` is computed (never stored)."""

    goal_id: str
    name: str
    goal_type: GoalType
    linked_category: ObligationCategory
    target_amount: Decimal
    target_date: Optional[datetime]
    current_amount: Decimal
    percent_complete: float
    contributing_event_count: int = Field(
        description="0 for a reserve target, whose progress reads the account balance instead of tagged events."
    )


class FinancialState(BaseModel):
    """The rebuildable digital twin (spec 6.1, API #6:
    `GET /api/financial-state`, `POST /api/financial-state/rebuild`).

    Phase 2 scope: confirmed balance and a per-status breakdown, derived
    only from non-superseded events. Phase 4 adds obligations,
    discretionary_spending, and goals — additional fields, not a
    replacement of the Phase 2 shape; every Phase 2 field keeps its exact
    original meaning.
    """

    user_id: str
    currency: Currency
    confirmed_balance: Decimal = Field(
        ..., description="Net of all CONFIRMED events only — the one number that needs no discounting."
    )
    breakdown_by_status: list[StatusBreakdown]
    source_event_count: int = Field(..., description="Non-superseded events included in this rebuild.")
    excluded_superseded_count: int = Field(..., description="Corrected/replaced events excluded from the totals.")
    rebuilt_at: datetime

    # --- Phase 4 additions ---
    obligations: list[ObligationSummary] = Field(default_factory=list)
    discretionary_spending: DiscretionarySpendingSummary = Field(default_factory=DiscretionarySpendingSummary)
    goals: list[GoalProgress] = Field(default_factory=list)


def rebuild_financial_state(
    user_id: str,
    currency: Currency,
    events: list[FinancialEventORM],
    *,
    goals: Optional[list[GoalORM]] = None,
) -> FinancialState:
    """Pure function: ledger events (+ optional goal targets) in, current
    state out. No database writes happen here — this is what
    `POST /api/financial-state/rebuild` calls and persists as a cached
    snapshot, but the computation itself never depends on anything but its
    inputs.

    Only currency-matching, non-superseded events for this user are
    included; a superseded event is excluded even if it was once confirmed,
    since it no longer represents the truth.

    `goals` is optional and keyword-only precisely so Phase 2's original
    3-positional-argument call sites (and its own test suite) keep working
    unchanged — omitting it simply returns an empty `goals` list, exactly
    as Phase 2 behaved before this field existed.
    """
    superseded_ids = {e.supersedes_event_id for e in events if e.supersedes_event_id}

    relevant = [
        e for e in events
        if e.user_id == user_id
        and e.currency == currency.value
        and e.id not in superseded_ids
    ]
    excluded_count = len([e for e in events if e.user_id == user_id and e.id in superseded_ids])

    totals: dict[str, tuple[Decimal, int]] = {}
    for status in EventStatus:
        totals[status.value] = (Decimal("0"), 0)

    for event in relevant:
        signed = event.amount if event.direction == EventDirection.CREDIT.value else -event.amount
        prior_amount, prior_count = totals[event.status]
        totals[event.status] = (prior_amount + signed, prior_count + 1)

    breakdown = [
        StatusBreakdown(status=EventStatus(status), net_amount=amount, event_count=count)
        for status, (amount, count) in totals.items()
    ]

    confirmed_amount, _ = totals[EventStatus.CONFIRMED.value]

    obligation_results = obligation_detection.build_obligation_summaries(relevant)
    obligations = [
        ObligationSummary(
            category=r.category,
            recurrence_group_id=r.recurrence_group_id,
            average_amount=r.average_amount,
            occurrence_count=r.occurrence_count,
            last_event_date=r.last_event_date,
            interval_days_estimate=r.interval_days_estimate,
            next_expected_date=r.next_expected_date,
        )
        for r in obligation_results
    ]

    discretionary_result = obligation_detection.build_discretionary_summary(relevant)
    discretionary = DiscretionarySpendingSummary(
        total=discretionary_result.total,
        event_count=discretionary_result.event_count,
        average_transaction=discretionary_result.average_transaction,
    )

    goal_progress: list[GoalProgress] = []
    for goal in (goals or []):
        if goal.user_id != user_id or goal.currency != currency.value:
            continue
        progress = goal_tracking.compute_goal_progress(goal, relevant, confirmed_amount)
        goal_progress.append(
            GoalProgress(
                goal_id=goal.id,
                name=goal.name,
                goal_type=GoalType(goal.goal_type),
                linked_category=ObligationCategory(goal.linked_category),
                target_amount=goal.target_amount,
                target_date=goal.target_date,
                current_amount=progress.current_amount,
                percent_complete=progress.percent_complete,
                contributing_event_count=progress.contributing_event_count,
            )
        )

    return FinancialState(
        user_id=user_id,
        currency=currency,
        confirmed_balance=confirmed_amount,
        breakdown_by_status=breakdown,
        source_event_count=len(relevant),
        excluded_superseded_count=excluded_count,
        rebuilt_at=datetime.now(timezone.utc),
        obligations=obligations,
        discretionary_spending=discretionary,
        goals=goal_progress,
    )
