from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.core.vocabulary import (
    Currency,
    EventDirection,
    EventSourceType,
    EventStatus,
    EventType,
    ObligationCategory,
)
from app.schemas.event import FinancialEventCreate
from app.schemas.provenance import SourceProvenance
from app.services import obligation_detection
from app.services.event_ledger import create_event, list_ledger

# Labelled demo dataset: (raw_excerpt, expected_category). Mirrors the kind
# of free-text description CSV/SMS/OCR ingestion actually produces (see
# csv_ingestion.py, which writes the CSV "description" column straight into
# raw_excerpt). Deliberately includes varied real-world phrasing per
# category, not just the exact keyword, since a classifier that only
# recognizes its own keyword list verbatim wouldn't earn its recall claim.
LABELLED_DATASET = [
    ("Monthly rent payment to landlord", ObligationCategory.RENT),
    ("Rent - March", ObligationCategory.RENT),
    ("House rent NEFT transfer", ObligationCategory.RENT),
    ("Rent payment via UPI", ObligationCategory.RENT),
    ("Home loan EMI - HDFC", ObligationCategory.EMI),
    ("Car loan EMI debited", ObligationCategory.EMI),
    ("Loan installment auto-debit", ObligationCategory.EMI),
    ("EMI payment for personal loan", ObligationCategory.EMI),
    ("Electricity bill - BESCOM", ObligationCategory.UTILITIES),
    ("Water bill payment", ObligationCategory.UTILITIES),
    ("Internet bill - ACT Fibernet", ObligationCategory.UTILITIES),
    ("Mobile bill - Airtel postpaid", ObligationCategory.UTILITIES),
    ("Netflix subscription renewal", ObligationCategory.UTILITIES),
    ("Spotify subscription", ObligationCategory.UTILITIES),
    ("Broadband bill - Jio Fiber", ObligationCategory.UTILITIES),
    ("Insurance premium - LIC policy", ObligationCategory.INSURANCE),
    ("Health insurance premium payment", ObligationCategory.INSURANCE),
    ("Credit card bill payment", ObligationCategory.DEBT_PAYMENTS),
    ("Credit card outstanding payment", ObligationCategory.DEBT_PAYMENTS),
    ("Gas bill - Indane", ObligationCategory.UTILITIES),
]


def _debit_event_orm(db_session, raw_excerpt: str, amount: str = "1000", days_ago: int = 0):
    payload = FinancialEventCreate(
        user_id="user-1",
        event_type=EventType.TRANSACTION,
        direction=EventDirection.DEBIT,
        amount=Decimal(amount),
        currency=Currency.INR,
        event_date=datetime.now(timezone.utc) - timedelta(days=days_ago),
        status=EventStatus.LIKELY,
        confidence=Decimal("0.6"),
        provenance=SourceProvenance(
            source_type=EventSourceType.CSV_UPLOAD,
            source_reference=f"row-{days_ago}-{raw_excerpt[:5]}",
            ingested_at=datetime.now(timezone.utc),
            raw_excerpt=raw_excerpt,
        ),
    )
    event = create_event(db_session, payload)
    db_session.commit()
    return event


def test_recall_on_labelled_dataset_is_at_least_90_percent():
    correct = 0
    for raw_excerpt, expected in LABELLED_DATASET:
        # classify_event_category is pure — build a throwaway ORM-shaped
        # object rather than round-tripping through the DB for every case.
        class _Fake:
            direction = EventDirection.DEBIT.value
            status = EventStatus.LIKELY.value
            raw_payload = {"raw_excerpt": raw_excerpt}
            source_reference = None

        result = obligation_detection.classify_event_category(_Fake())
        if result == expected:
            correct += 1

    recall = correct / len(LABELLED_DATASET)
    assert recall >= 0.90, f"recall was {recall:.2%}, expected >= 90%"


def test_unmatched_debit_falls_back_to_flexible_spending():
    class _Fake:
        direction = EventDirection.DEBIT.value
        status = EventStatus.LIKELY.value
        raw_payload = {"raw_excerpt": "Amazon purchase - headphones"}
        source_reference = None

    assert obligation_detection.classify_event_category(_Fake()) == ObligationCategory.FLEXIBLE_SPENDING


def test_credit_events_are_never_classified_as_obligations():
    class _Fake:
        direction = EventDirection.CREDIT.value
        status = EventStatus.LIKELY.value
        raw_payload = {"raw_excerpt": "Rent refund from landlord"}
        source_reference = None

    assert obligation_detection.classify_event_category(_Fake()) is None


def test_uncertain_events_are_not_classified():
    class _Fake:
        direction = EventDirection.DEBIT.value
        status = EventStatus.UNCERTAIN.value
        raw_payload = {"raw_excerpt": "Rent payment to landlord"}
        source_reference = None

    assert obligation_detection.classify_event_category(_Fake()) is None


def test_apply_classification_persists_via_correction(db_session):
    event = _debit_event_orm(db_session, "Electricity bill - BESCOM")
    assert event.category is None

    reclassified = obligation_detection.apply_classification(db_session, "user-1")
    db_session.commit()

    assert len(reclassified) == 1
    assert reclassified[0].category == ObligationCategory.UTILITIES.value
    # Original row is untouched — the ledger stays append-only.
    assert event.category is None
    assert reclassified[0].supersedes_event_id == event.id


def test_apply_classification_is_idempotent(db_session):
    _debit_event_orm(db_session, "Home loan EMI - HDFC")

    first_run = obligation_detection.apply_classification(db_session, "user-1")
    db_session.commit()
    assert len(first_run) == 1

    second_run = obligation_detection.apply_classification(db_session, "user-1")
    db_session.commit()
    assert second_run == []  # already classified — nothing new to correct

    active_events = list_ledger(db_session, "user-1")
    assert len(active_events) == 1  # no duplicate correction chain


def test_build_obligation_summaries_estimates_interval_from_recurrence():
    events = [
        _fake_classified_event(ObligationCategory.RENT, amount="20000", days_ago=60, group="rent-group"),
        _fake_classified_event(ObligationCategory.RENT, amount="20000", days_ago=30, group="rent-group"),
        _fake_classified_event(ObligationCategory.RENT, amount="20000", days_ago=0, group="rent-group"),
    ]
    summaries = obligation_detection.build_obligation_summaries(events)

    assert len(summaries) == 1
    summary = summaries[0]
    assert summary.category == ObligationCategory.RENT
    assert summary.occurrence_count == 3
    assert summary.interval_days_estimate == 30
    assert summary.next_expected_date is not None


def test_build_discretionary_summary_only_counts_flexible_spending_window():
    in_window = _fake_classified_event(ObligationCategory.FLEXIBLE_SPENDING, amount="500", days_ago=5)
    out_of_window = _fake_classified_event(ObligationCategory.FLEXIBLE_SPENDING, amount="9999", days_ago=90)
    obligation = _fake_classified_event(ObligationCategory.RENT, amount="20000", days_ago=1)

    summary = obligation_detection.build_discretionary_summary(
        [in_window, out_of_window, obligation], as_of=datetime.now(timezone.utc)
    )

    assert summary.total == Decimal("500")
    assert summary.event_count == 1


def _fake_classified_event(category: ObligationCategory, *, amount: str, days_ago: int, group: str = None):
    class _Fake:
        pass

    e = _Fake()
    e.category = category.value
    e.direction = EventDirection.DEBIT.value
    e.amount = Decimal(amount)
    e.event_date = datetime.now(timezone.utc) - timedelta(days=days_ago)
    e.recurrence_group_id = group
    return e
