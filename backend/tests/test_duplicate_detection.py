from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

from app.services.duplicate_detection import (
    DuplicateMatchType,
    find_potential_duplicates,
    has_any_match,
)


def _existing(amount, direction="debit", days_ago=0, source_type="csv_upload", event_id="existing-1"):
    return SimpleNamespace(
        id=event_id,
        amount=Decimal(amount),
        direction=direction,
        event_date=datetime.now(timezone.utc) - timedelta(days=days_ago),
        source_type=source_type,
    )


def test_exact_match_same_amount_same_day():
    now = datetime.now(timezone.utc)
    existing = [_existing("500.00", days_ago=0)]
    matches = find_potential_duplicates(Decimal("500.00"), "debit", now, existing)
    assert len(matches) == 1
    assert matches[0].match_type == DuplicateMatchType.EXACT


def test_near_match_same_amount_within_window():
    now = datetime.now(timezone.utc)
    existing = [_existing("1250.50", days_ago=2)]
    matches = find_potential_duplicates(Decimal("1250.50"), "debit", now, existing)
    assert len(matches) == 1
    assert matches[0].match_type == DuplicateMatchType.NEAR


def test_no_match_outside_date_window():
    now = datetime.now(timezone.utc)
    existing = [_existing("1250.50", days_ago=10)]
    matches = find_potential_duplicates(Decimal("1250.50"), "debit", now, existing)
    assert matches == []


def test_no_match_different_direction():
    now = datetime.now(timezone.utc)
    existing = [_existing("500.00", direction="credit", days_ago=0)]
    matches = find_potential_duplicates(Decimal("500.00"), "debit", now, existing)
    assert matches == []


def test_no_false_positive_different_amount_and_date():
    now = datetime.now(timezone.utc)
    existing = [_existing("500.00", days_ago=0)]
    matches = find_potential_duplicates(Decimal("75.00"), "debit", now - timedelta(days=5), existing)
    assert matches == []


def test_conflicting_match_same_day_different_amount():
    now = datetime.now(timezone.utc)
    existing = [_existing("500.00", days_ago=0)]
    matches = find_potential_duplicates(Decimal("520.00"), "debit", now, existing)
    assert len(matches) == 1
    assert matches[0].match_type == DuplicateMatchType.CONFLICTING


def test_conflicting_amount_outside_conflict_window_is_ignored():
    now = datetime.now(timezone.utc)
    # 2 days apart is within DATE_WINDOW_DAYS (3) but outside
    # CONFLICT_DATE_WINDOW_DAYS (1) -> since amounts differ, no match at all.
    existing = [_existing("500.00", days_ago=2)]
    matches = find_potential_duplicates(Decimal("520.00"), "debit", now, existing)
    assert matches == []


def test_has_any_match_helper():
    now = datetime.now(timezone.utc)
    existing = [_existing("500.00", days_ago=0)]
    matches = find_potential_duplicates(Decimal("500.00"), "debit", now, existing)
    assert has_any_match(matches) is True
    assert has_any_match([]) is False


def test_multiple_existing_events_can_all_match():
    now = datetime.now(timezone.utc)
    existing = [
        _existing("500.00", days_ago=0, event_id="a"),
        _existing("500.00", days_ago=1, event_id="b"),
    ]
    matches = find_potential_duplicates(Decimal("500.00"), "debit", now, existing)
    assert len(matches) == 2
    assert {m.existing_event_id for m in matches} == {"a", "b"}
