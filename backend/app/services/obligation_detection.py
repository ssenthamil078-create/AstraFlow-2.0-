"""
Phase 4 — Obligation detection & discretionary-spending classification.

Every DEBIT event eventually needs exactly one ObligationCategory so the
digital twin can answer "what does the user owe regularly, and what's
left over as discretionary spending" (spec section 4, Phase 4 goal).
This module is the only place that decides that category:

  1. `classify_event_category()` — a deterministic keyword classifier
     over the event's provenance text (never an LLM: this is exactly the
     kind of number the spec's Phase 8 rationale says must stay
     deterministic, and a mis-classified obligation would corrupt the
     runway calculation two phases downstream). Anything that doesn't
     match a recognized obligation keyword falls through to
     FLEXIBLE_SPENDING — the closed vocabulary's own "everything else"
     bucket, which is also what a policy's `reduce` action targets
     (spec 4.5 example).

  2. `apply_classification()` — persists the decision. Because the
     ledger is append-only, "setting" a category is a correction
     (CorrectionReason.CATEGORY_RECLASSIFIED) that supersedes the
     original event, never an in-place field update.

  3. `build_obligation_summaries()` / `build_discretionary_summary()` —
     pure read models over already-classified events, used by the
     extended FinancialState (schemas/financial_state.py).

Recall target (spec Phase 4 definition of done): >=90% recall on a
labelled demo dataset for rent/EMI/utility/subscription records — see
tests/test_obligation_detection.py for the labelled set this is measured
against. Precision is intentionally not the primary metric: a bill
mis-tagged as FLEXIBLE_SPENDING silently inflates "discretionary" and
never reaches the emergency policy's protected-obligations list, so
recall failures are the dangerous direction to guard against; a handful
of ordinary purchases getting swept into an obligation category is a
lower-stakes false positive a user corrects on the review screen.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from statistics import median
from typing import Optional

from sqlalchemy.orm import Session

from app.core.vocabulary import CorrectionReason, EventDirection, EventStatus, ObligationCategory
from app.models.financial_event import FinancialEventORM
from app.schemas.event import FinancialEventCorrection
from app.services import event_ledger

# Keyword -> category, checked in this order (first match wins) so a more
# specific term (e.g. "loan emi") is never shadowed by a generic one.
# Kept lowercase; matching is done against a lowercased search string.
_KEYWORD_RULES: list[tuple[ObligationCategory, tuple[str, ...]]] = [
    (
        ObligationCategory.RENT,
        ("rent payment", "house rent", "rent to landlord", " rent ", "rent-", "landlord", "lease payment"),
    ),
    (
        ObligationCategory.EMI,
        ("emi", "loan installment", "loan instalment", "installment payment", "instalment payment"),
    ),
    (
        ObligationCategory.DEBT_PAYMENTS,
        ("credit card bill", "credit card payment", "card outstanding", "loan repayment"),
    ),
    (
        ObligationCategory.INSURANCE,
        ("insurance premium", "insurance payment", " insurance", "policy premium"),
    ),
    (
        ObligationCategory.UTILITIES,
        (
            "electricity bill", "power bill", "water bill", "gas bill", "utility bill", "utilities",
            "internet bill", "broadband bill", "wifi bill", "mobile bill", "phone bill", "dth recharge",
            # subscriptions: the closed vocabulary has no dedicated
            # SUBSCRIPTION category, so a recurring content/software
            # subscription is treated as a utility-style recurring bill —
            # see docs/phase4_financial_digital_twin.md for the rationale.
            "subscription", "netflix", "spotify", "prime video", "hotstar", "youtube premium",
        ),
    ),
]


def _search_text(event: FinancialEventORM) -> str:
    parts = [
        (event.raw_payload or {}).get("raw_excerpt") or "",
        event.source_reference or "",
    ]
    return f" {' '.join(parts).lower()} "


def classify_event_category(event: FinancialEventORM) -> Optional[ObligationCategory]:
    """Returns the matched obligation category, or None for a CREDIT event
    (income isn't an obligation — Phase 5 scores income separately) or an
    UNCERTAIN/REJECTED event (classifying data we don't yet trust would
    let a duplicate or misread row pollute the obligation summary)."""
    if event.direction != EventDirection.DEBIT.value:
        return None
    if event.status in (EventStatus.UNCERTAIN.value, EventStatus.REJECTED.value):
        return None

    text = _search_text(event)
    for category, keywords in _KEYWORD_RULES:
        if any(keyword in text for keyword in keywords):
            return category
    return ObligationCategory.FLEXIBLE_SPENDING


def apply_classification(session: Session, user_id: str) -> list[FinancialEventORM]:
    """Classifies every not-yet-categorized, classifiable DEBIT event for
    a user and persists the result as a correction. Idempotent: an event
    whose category already matches what the classifier would assign is
    left untouched, so re-running this on an unchanged ledger creates no
    new correction rows.

    Returns the events that were actually reclassified this run (empty on
    a stable ledger).
    """
    active_events = event_ledger.list_ledger(session, user_id)
    reclassified: list[FinancialEventORM] = []

    for event in active_events:
        new_category = classify_event_category(event)
        if new_category is None:
            continue
        if event.category == new_category.value:
            continue
        updated = event_ledger.correct_event(
            session,
            event.id,
            FinancialEventCorrection(
                reason=CorrectionReason.CATEGORY_RECLASSIFIED,
                category=new_category.value,
            ),
        )
        reclassified.append(updated)

    return reclassified


class ObligationSummaryResult:
    """Plain data holder (mirrors GoalProgressResult) so this service has
    no dependency on the Pydantic schema that wraps it for the API."""

    def __init__(
        self,
        *,
        category: ObligationCategory,
        recurrence_group_id: Optional[str],
        average_amount: Decimal,
        occurrence_count: int,
        last_event_date: datetime,
        interval_days_estimate: Optional[int],
        next_expected_date: Optional[datetime],
    ) -> None:
        self.category = category
        self.recurrence_group_id = recurrence_group_id
        self.average_amount = average_amount
        self.occurrence_count = occurrence_count
        self.last_event_date = last_event_date
        self.interval_days_estimate = interval_days_estimate
        self.next_expected_date = next_expected_date


_OBLIGATION_CATEGORIES = {
    ObligationCategory.RENT,
    ObligationCategory.EMI,
    ObligationCategory.UTILITIES,
    ObligationCategory.INSURANCE,
    ObligationCategory.DEBT_PAYMENTS,
}


def build_obligation_summaries(events: list[FinancialEventORM]) -> list[ObligationSummaryResult]:
    """Groups already-classified obligation events by (category,
    recurrence_group_id) — or by category alone when no recurrence group
    was assigned during ingestion — and estimates a payment interval from
    the gaps between occurrences. Two or more occurrences are needed to
    estimate an interval; a single occurrence is still reported (so a
    first-ever rent payment shows up immediately) with
    interval_days_estimate=None.
    """
    groups: dict[tuple[str, Optional[str]], list[FinancialEventORM]] = defaultdict(list)
    for event in events:
        if event.category not in {c.value for c in _OBLIGATION_CATEGORIES}:
            continue
        groups[(event.category, event.recurrence_group_id)].append(event)

    summaries: list[ObligationSummaryResult] = []
    for (category_value, recurrence_group_id), group_events in groups.items():
        group_events.sort(key=lambda e: e.event_date)
        amounts = [e.amount for e in group_events]
        average_amount = sum(amounts, Decimal("0")) / len(amounts)
        last_event_date = group_events[-1].event_date

        interval_estimate: Optional[int] = None
        next_expected: Optional[datetime] = None
        if len(group_events) >= 2:
            gaps = [
                (group_events[i].event_date - group_events[i - 1].event_date).days
                for i in range(1, len(group_events))
            ]
            interval_estimate = round(median(gaps))
            next_expected = last_event_date + timedelta(days=interval_estimate)

        summaries.append(
            ObligationSummaryResult(
                category=ObligationCategory(category_value),
                recurrence_group_id=recurrence_group_id,
                average_amount=average_amount,
                occurrence_count=len(group_events),
                last_event_date=last_event_date,
                interval_days_estimate=interval_estimate,
                next_expected_date=next_expected,
            )
        )

    return sorted(summaries, key=lambda s: (s.category.value, s.recurrence_group_id or ""))


class DiscretionarySpendingResult:
    def __init__(self, *, total: Decimal, event_count: int, average_transaction: Decimal) -> None:
        self.total = total
        self.event_count = event_count
        self.average_transaction = average_transaction


def build_discretionary_summary(
    events: list[FinancialEventORM],
    *,
    window_days: int = 30,
    as_of: Optional[datetime] = None,
) -> DiscretionarySpendingResult:
    """Total FLEXIBLE_SPENDING debit spend in the trailing `window_days`
    (default 30) up to `as_of` (default: now). This is the number a
    policy's `reduce flexible_spending by X%` action (spec 4.5) acts on."""
    reference = as_of or datetime.now(timezone.utc)
    window_start = reference - timedelta(days=window_days)

    matching = [
        e
        for e in events
        if e.category == ObligationCategory.FLEXIBLE_SPENDING.value
        and e.direction == EventDirection.DEBIT.value
        and window_start <= (
            e.event_date.replace(tzinfo=timezone.utc)
            if e.event_date.tzinfo is None
            else e.event_date
        ) <= reference
    ]
    total = sum((e.amount for e in matching), Decimal("0"))
    average = (total / len(matching)) if matching else Decimal("0")
    return DiscretionarySpendingResult(total=total, event_count=len(matching), average_transaction=average)
