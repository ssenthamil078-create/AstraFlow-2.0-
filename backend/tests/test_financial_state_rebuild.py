from datetime import datetime, timezone
from decimal import Decimal

from app.core.vocabulary import (
    CorrectionReason,
    Currency,
    EventDirection,
    EventSourceType,
    EventStatus,
    EventType,
)
from app.schemas.event import FinancialEventCorrection, FinancialEventCreate
from app.schemas.financial_state import rebuild_financial_state
from app.schemas.provenance import SourceProvenance
from app.services.event_ledger import confirm_event, correct_event, create_event, list_ledger


def _create(db_session, **overrides):
    payload = dict(
        user_id="user-1",
        event_type=EventType.TRANSACTION,
        direction=EventDirection.CREDIT,
        amount=Decimal("1000.00"),
        currency=Currency.INR,
        event_date=datetime.now(timezone.utc),
        status=EventStatus.LIKELY,
        confidence=Decimal("0.6"),
        provenance=SourceProvenance(
            source_type=EventSourceType.CSV_UPLOAD,
            source_reference="row-1",
            ingested_at=datetime.now(timezone.utc),
        ),
    )
    payload.update(overrides)
    return create_event(db_session, FinancialEventCreate.model_validate(payload))


def test_confirmed_balance_only_counts_confirmed_events(db_session):
    confirmed = _create(db_session, amount=Decimal("5000"))
    confirm_event(db_session, confirmed.id)
    _create(db_session, amount=Decimal("2000"), status=EventStatus.LIKELY, confidence=Decimal("0.5"))
    db_session.commit()

    events = list_ledger(db_session, "user-1")
    state = rebuild_financial_state("user-1", Currency.INR, events)

    assert state.confirmed_balance == Decimal("5000")
    assert state.source_event_count == 2


def test_debit_events_reduce_balance(db_session):
    income = _create(db_session, amount=Decimal("5000"), direction=EventDirection.CREDIT)
    confirm_event(db_session, income.id)
    expense = _create(db_session, amount=Decimal("1200"), direction=EventDirection.DEBIT,
                       status=EventStatus.LIKELY, confidence=Decimal("0.6"))
    confirm_event(db_session, expense.id)
    db_session.commit()

    events = list_ledger(db_session, "user-1")
    state = rebuild_financial_state("user-1", Currency.INR, events)

    assert state.confirmed_balance == Decimal("3800")


def test_breakdown_by_status_keeps_uncertain_money_separate(db_session):
    _create(db_session, amount=Decimal("1000"), status=EventStatus.CONFIRMED, confidence=Decimal("1"))
    _create(db_session, amount=Decimal("2000"), status=EventStatus.LIKELY, confidence=Decimal("0.6"))
    _create(db_session, amount=Decimal("3000"), status=EventStatus.UNCERTAIN, confidence=Decimal("0.3"))
    db_session.commit()

    events = list_ledger(db_session, "user-1")
    state = rebuild_financial_state("user-1", Currency.INR, events)

    by_status = {b.status: b.net_amount for b in state.breakdown_by_status}
    assert by_status[EventStatus.CONFIRMED] == Decimal("1000")
    assert by_status[EventStatus.LIKELY] == Decimal("2000")
    assert by_status[EventStatus.UNCERTAIN] == Decimal("3000")


def test_superseded_events_excluded_from_rebuild(db_session):
    original = _create(db_session, amount=Decimal("1000"), status=EventStatus.CONFIRMED, confidence=Decimal("1"))
    correction = FinancialEventCorrection(reason=CorrectionReason.AMOUNT_CORRECTED, amount=Decimal("1800"))
    correct_event(db_session, original.id, correction)
    db_session.commit()

    # include_superseded=True so we can prove the rebuild itself does the
    # excluding, not list_ledger.
    events = list_ledger(db_session, "user-1", include_superseded=True)
    state = rebuild_financial_state("user-1", Currency.INR, events)

    assert state.confirmed_balance == Decimal("1800")
    assert state.source_event_count == 1
    assert state.excluded_superseded_count == 1


def test_rebuild_only_includes_matching_currency(db_session):
    _create(db_session, amount=Decimal("1000"), currency=Currency.INR,
            status=EventStatus.CONFIRMED, confidence=Decimal("1"))
    _create(db_session, amount=Decimal("50"), currency=Currency.USD,
            status=EventStatus.CONFIRMED, confidence=Decimal("1"))
    db_session.commit()

    events = list_ledger(db_session, "user-1")
    state = rebuild_financial_state("user-1", Currency.INR, events)

    assert state.confirmed_balance == Decimal("1000")
    assert state.source_event_count == 1
