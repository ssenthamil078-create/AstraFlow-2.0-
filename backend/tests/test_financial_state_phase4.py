from datetime import datetime, timedelta, timezone
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
from app.schemas.financial_state import rebuild_financial_state
from app.schemas.goal import GoalCreate
from app.schemas.provenance import SourceProvenance
from app.services import goal_tracking, obligation_detection
from app.services.event_ledger import confirm_event, create_event, list_ledger


def _event(db_session, *, direction, amount, category=None, raw_excerpt=None,
           status=EventStatus.LIKELY, confidence=Decimal("0.6"), confirmed=False, days_ago=0):
    payload = FinancialEventCreate(
        user_id="user-1",
        event_type=EventType.TRANSACTION,
        direction=direction,
        amount=Decimal(amount),
        currency=Currency.INR,
        event_date=datetime.now(timezone.utc) - timedelta(days=days_ago),
        category=category,
        status=status,
        confidence=confidence,
        provenance=SourceProvenance(
            source_type=EventSourceType.CSV_UPLOAD,
            source_reference=f"row-{days_ago}",
            ingested_at=datetime.now(timezone.utc),
            raw_excerpt=raw_excerpt,
        ),
    )
    event = create_event(db_session, payload)
    if confirmed:
        event = confirm_event(db_session, event.id)
    db_session.commit()
    return event


def test_phase2_call_signature_still_works_unchanged(db_session):
    """The exact 3-positional-arg call from Phase 2's own test suite must
    keep working after Phase 4's additions."""
    _event(db_session, direction=EventDirection.CREDIT, amount="1000",
           status=EventStatus.CONFIRMED, confidence=Decimal("1"), confirmed=False)
    events = list_ledger(db_session, "user-1")

    state = rebuild_financial_state("user-1", Currency.INR, events)

    assert state.confirmed_balance == Decimal("1000")
    assert state.obligations == []
    assert state.goals == []
    assert state.discretionary_spending.total == Decimal("0")


def test_rebuild_includes_obligation_summaries_after_classification(db_session):
    _event(db_session, direction=EventDirection.DEBIT, amount="20000",
           raw_excerpt="House rent payment")
    obligation_detection.apply_classification(db_session, "user-1")
    events = list_ledger(db_session, "user-1")

    state = rebuild_financial_state("user-1", Currency.INR, events)

    assert len(state.obligations) == 1
    assert state.obligations[0].category == ObligationCategory.RENT
    assert state.obligations[0].occurrence_count == 1


def test_rebuild_includes_discretionary_spending(db_session):
    _event(db_session, direction=EventDirection.DEBIT, amount="750",
           raw_excerpt="Amazon purchase")
    obligation_detection.apply_classification(db_session, "user-1")
    events = list_ledger(db_session, "user-1")

    state = rebuild_financial_state("user-1", Currency.INR, events)

    assert state.discretionary_spending.total == Decimal("750")
    assert state.discretionary_spending.event_count == 1


def test_rebuild_includes_goal_progress(db_session):
    goal = goal_tracking.create_goal(
        db_session,
        "user-1",
        GoalCreate(
            name="Emergency fund",
            goal_type=GoalType.SAVINGS_TARGET,
            currency=Currency.INR,
            linked_category=ObligationCategory.EMERGENCY_SAVINGS,
            target_amount=Decimal("20000"),
        ),
    )
    db_session.commit()
    _event(db_session, direction=EventDirection.CREDIT, amount="5000",
           category="emergency_savings", status=EventStatus.CONFIRMED, confidence=Decimal("1"))

    events = list_ledger(db_session, "user-1")
    state = rebuild_financial_state("user-1", Currency.INR, events, goals=[goal])

    assert len(state.goals) == 1
    assert state.goals[0].goal_id == goal.id
    assert state.goals[0].current_amount == Decimal("5000")
    assert state.goals[0].percent_complete == 25.0


def test_goals_from_a_different_currency_are_excluded(db_session):
    usd_goal = goal_tracking.create_goal(
        db_session,
        "user-1",
        GoalCreate(
            name="USD fund",
            goal_type=GoalType.SAVINGS_TARGET,
            currency=Currency.USD,
            linked_category=ObligationCategory.EMERGENCY_SAVINGS,
            target_amount=Decimal("1000"),
        ),
    )
    db_session.commit()
    events = list_ledger(db_session, "user-1")

    state = rebuild_financial_state("user-1", Currency.INR, events, goals=[usd_goal])

    assert state.goals == []
