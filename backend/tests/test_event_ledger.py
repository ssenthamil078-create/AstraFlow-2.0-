from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.core.vocabulary import (
    CorrectionReason,
    Currency,
    EventDirection,
    EventSourceType,
    EventStatus,
    EventType,
)
from app.schemas.event import FinancialEventCorrection, FinancialEventCreate
from app.schemas.provenance import SourceProvenance
from app.services.event_ledger import (
    ImmutableEventError,
    confirm_event,
    correct_event,
    create_event,
    list_ledger,
)


def _create(db_session, **overrides):
    payload = dict(
        user_id="user-1",
        event_type=EventType.TRANSACTION,
        direction=EventDirection.CREDIT,
        amount=Decimal("5000.00"),
        currency=Currency.INR,
        event_date=datetime.now(timezone.utc),
        status=EventStatus.LIKELY,
        confidence=Decimal("0.7"),
        provenance=SourceProvenance(
            source_type=EventSourceType.CSV_UPLOAD,
            source_reference="row-1",
            ingested_at=datetime.now(timezone.utc),
        ),
    )
    payload.update(overrides)
    event_in = FinancialEventCreate.model_validate(payload)
    return create_event(db_session, event_in)


def test_create_event_persists(db_session):
    event = _create(db_session)
    db_session.commit()
    assert event.id is not None
    assert event.status == EventStatus.LIKELY.value


def test_confirm_event_sets_full_confidence(db_session):
    event = _create(db_session)
    db_session.commit()

    confirmed = confirm_event(db_session, event.id)
    db_session.commit()

    assert confirmed.status == EventStatus.CONFIRMED.value
    assert confirmed.confidence == Decimal("1")
    assert confirmed.confirmed_at is not None


def test_confirming_twice_raises(db_session):
    event = _create(db_session)
    db_session.commit()
    confirm_event(db_session, event.id)
    db_session.commit()

    with pytest.raises(ImmutableEventError):
        confirm_event(db_session, event.id)


def test_correct_event_creates_new_row_and_leaves_original_untouched(db_session):
    original = _create(db_session, amount=Decimal("1000.00"))
    db_session.commit()
    original_id = original.id
    original_amount = original.amount

    correction = FinancialEventCorrection(reason=CorrectionReason.AMOUNT_CORRECTED, amount=Decimal("1500.00"))
    corrected = correct_event(db_session, original_id, correction)
    db_session.commit()

    # original row is byte-for-byte untouched
    assert original.id == original_id
    assert original.amount == original_amount

    # new row supersedes it
    assert corrected.id != original_id
    assert corrected.supersedes_event_id == original_id
    assert corrected.amount == Decimal("1500.00")
    assert corrected.correction_reason == CorrectionReason.AMOUNT_CORRECTED.value


def test_list_ledger_excludes_superseded_events_by_default(db_session):
    original = _create(db_session, amount=Decimal("1000.00"))
    db_session.commit()
    correction = FinancialEventCorrection(reason=CorrectionReason.AMOUNT_CORRECTED, amount=Decimal("1500.00"))
    correct_event(db_session, original.id, correction)
    db_session.commit()

    active = list_ledger(db_session, "user-1")
    assert len(active) == 1
    assert active[0].amount == Decimal("1500.00")


def test_list_ledger_can_include_full_history(db_session):
    original = _create(db_session, amount=Decimal("1000.00"))
    db_session.commit()
    correction = FinancialEventCorrection(reason=CorrectionReason.AMOUNT_CORRECTED, amount=Decimal("1500.00"))
    correct_event(db_session, original.id, correction)
    db_session.commit()

    full_history = list_ledger(db_session, "user-1", include_superseded=True)
    assert len(full_history) == 2


def test_confirmed_event_cannot_be_corrected_into_a_silent_overwrite(db_session):
    # correct_event always creates a NEW row even for a confirmed original —
    # this test pins down that the original confirmed row is never mutated.
    event = _create(db_session)
    db_session.commit()
    confirm_event(db_session, event.id)
    db_session.commit()

    correction = FinancialEventCorrection(reason=CorrectionReason.CATEGORY_RECLASSIFIED, category="rent")
    new_event = correct_event(db_session, event.id, correction)
    db_session.commit()

    assert event.status == EventStatus.CONFIRMED.value  # untouched
    assert new_event.status == EventStatus.CONFIRMED.value  # copied forward
    assert new_event.category == "rent"
