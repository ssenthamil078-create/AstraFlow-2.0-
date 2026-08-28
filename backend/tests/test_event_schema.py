from datetime import datetime, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

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


def _provenance(**overrides) -> dict:
    base = dict(
        source_type=EventSourceType.CSV_UPLOAD,
        source_reference="row-42",
        ingested_at=datetime.now(timezone.utc),
    )
    base.update(overrides)
    return base


def _event(**overrides) -> dict:
    base = dict(
        user_id="user-1",
        event_type=EventType.TRANSACTION,
        direction=EventDirection.CREDIT,
        amount=Decimal("1000.00"),
        currency=Currency.INR,
        event_date=datetime.now(timezone.utc),
        status=EventStatus.LIKELY,
        confidence=Decimal("0.8"),
        provenance=_provenance(),
    )
    base.update(overrides)
    return base


def test_valid_event_passes():
    event = FinancialEventCreate.model_validate(_event())
    assert event.amount == Decimal("1000.00")
    assert event.provenance.source_type == EventSourceType.CSV_UPLOAD


def test_amount_must_be_positive():
    with pytest.raises(ValidationError):
        FinancialEventCreate.model_validate(_event(amount=Decimal("-5")))


def test_confirmed_status_requires_full_confidence():
    with pytest.raises(ValidationError):
        FinancialEventCreate.model_validate(
            _event(status=EventStatus.CONFIRMED, confidence=Decimal("0.9"))
        )


def test_confirmed_status_with_full_confidence_is_valid():
    event = FinancialEventCreate.model_validate(
        _event(status=EventStatus.CONFIRMED, confidence=Decimal("1"))
    )
    assert event.status == EventStatus.CONFIRMED


def test_likely_status_cannot_claim_full_confidence():
    with pytest.raises(ValidationError):
        FinancialEventCreate.model_validate(
            _event(status=EventStatus.LIKELY, confidence=Decimal("1"))
        )


def test_non_manual_source_requires_reference():
    with pytest.raises(ValidationError):
        SourceProvenance.model_validate(
            _provenance(source_type=EventSourceType.BANK_FEED, source_reference=None)
        )


def test_manual_entry_source_may_omit_reference():
    provenance = SourceProvenance.model_validate(
        _provenance(source_type=EventSourceType.MANUAL_ENTRY, source_reference=None)
    )
    assert provenance.source_reference is None


def test_correction_requires_at_least_one_changed_field():
    with pytest.raises(ValidationError):
        FinancialEventCorrection.model_validate({"reason": CorrectionReason.AMOUNT_CORRECTED.value})


def test_correction_with_a_changed_field_is_valid():
    correction = FinancialEventCorrection.model_validate(
        {"reason": CorrectionReason.AMOUNT_CORRECTED.value, "amount": "1200.00"}
    )
    assert correction.amount == Decimal("1200.00")
