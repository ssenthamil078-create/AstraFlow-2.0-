"""
Phase 3 — Duplicate / conflict detection.

Runs against the already-ingested, non-superseded events for the same user
*before* a new candidate event is written to the ledger. This module never
rejects or silently discards a candidate — it only reports what it found.
The caller (csv_ingestion.py, sms_ingestion.py, ocr_ingestion.py) decides
what EventStatus that earns, and the human review screen
(Confirmed / Likely / Uncertain, spec 6.1) is where the actual accept/merge
decision gets made. Keeping "detect" and "decide" separate here is what
lets Phase 3's definition of done — "OCR output is never auto-confirmed" —
hold structurally instead of by convention.

Matching strategy (deliberately simple and explainable, not ML-based):
a new event is compared against existing events with the same direction
and a nearby event_date, using an amount tolerance. Three outcomes:

  EXACT       — same amount (to the cent/paisa) on the same calendar date.
                Almost certainly the same transaction entering twice
                (e.g. a CSV re-upload, or the same purchase from both a
                CSV row and an SMS alert).
  NEAR        — same amount, date within the matching window. Likely the
                same transaction, dated slightly differently by two
                sources (bank posting date vs. SMS timestamp vs. receipt
                date).
  CONFLICTING — same direction, same/adjacent date, but the amount
                differs. Could be a partial refund, a split payment, or
                genuinely two different transactions — a human should
                look, which is exactly what "Uncertain" status is for.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Sequence

from app.models.financial_event import FinancialEventORM

# Tolerances chosen to catch the common "same transaction, two sources"
# cases without flagging every same-day, same-amount coincidence (e.g. two
# separate ₹100 coffees) as a duplicate of each other. CONFLICTING casts a
# narrower net (1 day) than NEAR (DATE_WINDOW_DAYS) since an amount
# mismatch is only worth a human's attention when the dates are very close.
AMOUNT_ABS_TOLERANCE = Decimal("0.01")
DATE_WINDOW_DAYS = 3
CONFLICT_DATE_WINDOW_DAYS = 1


class DuplicateMatchType(str, Enum):
    EXACT = "exact"
    NEAR = "near"
    CONFLICTING = "conflicting"


@dataclass(frozen=True)
class DuplicateMatch:
    existing_event_id: str
    match_type: DuplicateMatchType
    reason: str


def find_potential_duplicates(
    candidate_amount: Decimal,
    candidate_direction: str,
    candidate_event_date: datetime,
    existing_events: Sequence[FinancialEventORM],
) -> list[DuplicateMatch]:
    """Compare one not-yet-written candidate against a user's existing,
    non-superseded ledger events. Pure function — no DB access — so
    ingestion services can call it once per row/message without a fresh
    query each time."""
    matches: list[DuplicateMatch] = []

    for existing in existing_events:
        if existing.direction != candidate_direction:
            continue

        day_gap = abs((candidate_event_date.date() - existing.event_date.date()).days)
        if day_gap > DATE_WINDOW_DAYS:
            continue

        amount_gap = abs(Decimal(existing.amount) - candidate_amount)

        if amount_gap <= AMOUNT_ABS_TOLERANCE and day_gap == 0:
            matches.append(
                DuplicateMatch(
                    existing_event_id=existing.id,
                    match_type=DuplicateMatchType.EXACT,
                    reason=(
                        f"Same amount ({candidate_amount}) and date as existing event "
                        f"{existing.id[:8]} (source={existing.source_type})."
                    ),
                )
            )
        elif amount_gap <= AMOUNT_ABS_TOLERANCE:
            matches.append(
                DuplicateMatch(
                    existing_event_id=existing.id,
                    match_type=DuplicateMatchType.NEAR,
                    reason=(
                        f"Same amount ({candidate_amount}) within {day_gap} day(s) of existing "
                        f"event {existing.id[:8]} (source={existing.source_type})."
                    ),
                )
            )
        elif day_gap <= CONFLICT_DATE_WINDOW_DAYS:
            matches.append(
                DuplicateMatch(
                    existing_event_id=existing.id,
                    match_type=DuplicateMatchType.CONFLICTING,
                    reason=(
                        f"Same direction within {day_gap} day(s) of existing event "
                        f"{existing.id[:8]} but amount differs ({candidate_amount} vs {existing.amount})."
                    ),
                )
            )

    return matches


def has_any_match(matches: Sequence[DuplicateMatch]) -> bool:
    return len(matches) > 0
