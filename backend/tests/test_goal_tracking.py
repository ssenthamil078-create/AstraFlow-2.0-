from datetime import datetime, timezone
from decimal import Decimal

from app.core.vocabulary import (
    Currency,
    EventDirection,
    EventSourceType,
    EventStatus,
    EventType,
    GoalType,
    ObligationCategory,
)
from app.schemas.event import FinancialEventCreate
from app.schemas.goal import GoalCreate, GoalUpdate
from app.schemas.provenance import SourceProvenance
from app.services import goal_tracking
from app.services.event_ledger import confirm_event, create_event, list_ledger


def _create_goal(db_session, user_id="user-1", **overrides):
    payload = dict(
        name="Emergency fund",
        goal_type=GoalType.SAVINGS_TARGET,
        currency=Currency.INR,
        linked_category=ObligationCategory.EMERGENCY_SAVINGS,
        target_amount=Decimal("50000"),
        target_date=None,
    )
    payload.update(overrides)
    goal = goal_tracking.create_goal(db_session, user_id, GoalCreate.model_validate(payload))
    db_session.commit()
    return goal


def _credit_event(db_session, amount: str, category: str, *, confirmed: bool = True):
    payload = FinancialEventCreate(
        user_id="user-1",
        event_type=EventType.TRANSACTION,
        direction=EventDirection.CREDIT,
        amount=Decimal(amount),
        currency=Currency.INR,
        event_date=datetime.now(timezone.utc),
        category=category,
        status=EventStatus.LIKELY,
        confidence=Decimal("0.6"),
        provenance=SourceProvenance(
            source_type=EventSourceType.MANUAL_ENTRY,
            ingested_at=datetime.now(timezone.utc),
        ),
    )
    event = create_event(db_session, payload)
    if confirmed:
        event = confirm_event(db_session, event.id)
    db_session.commit()
    return event


def test_create_and_update_goal(db_session):
    goal = _create_goal(db_session, target_amount=Decimal("30000"))
    assert goal.target_amount == Decimal("30000")

    updated = goal_tracking.update_goal(
        db_session, goal.id, GoalUpdate(target_amount=Decimal("40000"))
    )
    db_session.commit()
    assert updated.target_amount == Decimal("40000")
    assert updated.name == "Emergency fund"  # untouched field stays as-is


def test_savings_target_progress_counts_only_confirmed_matching_category(db_session):
    goal = _create_goal(db_session, target_amount=Decimal("10000"))
    _credit_event(db_session, "4000", "emergency_savings", confirmed=True)
    _credit_event(db_session, "1000", "emergency_savings", confirmed=False)   # not confirmed — excluded
    _credit_event(db_session, "9000", "flexible_spending", confirmed=True)     # wrong category — excluded

    events = list_ledger(db_session, "user-1")
    progress = goal_tracking.compute_goal_progress(goal, events, confirmed_balance=Decimal("13000"))

    assert progress.current_amount == Decimal("4000")
    assert progress.contributing_event_count == 1
    assert progress.percent_complete == 40.0
    assert progress.is_reserve is False


def test_reserve_target_progress_reads_confirmed_balance(db_session):
    goal = _create_goal(
        db_session,
        name="Minimum reserve",
        goal_type=GoalType.RESERVE_TARGET,
        linked_category=ObligationCategory.MIN_CASH_RESERVE,
        target_amount=Decimal("50000"),
    )
    progress = goal_tracking.compute_goal_progress(goal, events=[], confirmed_balance=Decimal("32000"))

    assert progress.is_reserve is True
    assert progress.current_amount == Decimal("32000")
    assert progress.percent_complete == 64.0
    assert progress.contributing_event_count == 0


def test_goal_progress_caps_at_100_percent(db_session):
    goal = _create_goal(db_session, target_amount=Decimal("1000"))

    _credit_event(db_session, "5000", "emergency_savings", confirmed=True)
    events = list_ledger(db_session, "user-1")

    progress = goal_tracking.compute_goal_progress(goal, events, confirmed_balance=Decimal("5000"))
    assert progress.percent_complete == 100.0
