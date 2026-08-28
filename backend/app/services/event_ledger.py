"""
Phase 2 — Event ledger service.

This is the ONLY place in the codebase allowed to write to the
financial_events table. Phase 3's ingestion API calls into this, not into
the ORM directly, so "immutable ledger" is enforced by there being no other
door in, not just by convention.

Rules enforced here:
  1. A CONFIRMED event can never be updated in place.
  2. Correcting an event creates a NEW row referencing the old one via
     `supersedes_event_id` — the old row is untouched and stays in history.
  3. Provenance is always attached; a bank-feed/CSV/SMS/OCR source without a
     reference back to the original record is rejected at the schema layer
     (see SourceProvenance) before it ever reaches this service.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.vocabulary import EventStatus
from app.models.financial_event import FinancialEventORM
from app.schemas.event import FinancialEventCorrection, FinancialEventCreate


class ImmutableEventError(RuntimeError):
    """Raised when code attempts to mutate a confirmed event in place
    instead of going through correct_event()."""


def create_event(session: Session, payload: FinancialEventCreate) -> FinancialEventORM:
    """Append a new event to the ledger. This is the only way a new row
    is created — there is no bulk-insert bypass."""
    provenance = payload.provenance
    orm_event = FinancialEventORM(
        user_id=payload.user_id,
        event_type=payload.event_type.value,
        direction=payload.direction.value,
        amount=payload.amount,
        currency=payload.currency.value,
        event_date=payload.event_date,
        category=payload.category,
        status=payload.status.value,
        confidence=payload.confidence,
        source_type=provenance.source_type.value,
        source_reference=provenance.source_reference,
        raw_payload={
            "ingested_at": provenance.ingested_at.isoformat(),
            "extraction_method": provenance.extraction_method,
            "raw_excerpt": provenance.raw_excerpt,
        },
        recurrence_group_id=payload.recurrence_group_id,
        confirmed_at=None,
    )
    session.add(orm_event)
    session.flush()  # populate generated fields (id) without committing
    return orm_event


def confirm_event(session: Session, event_id: str) -> FinancialEventORM:
    """Move an event to CONFIRMED status. Allowed exactly once — confirming
    an already-confirmed event is a no-op error, since confirmation is a
    one-way transition, not a general-purpose update."""
    event = _get_or_raise(session, event_id)
    if event.status == EventStatus.CONFIRMED.value:
        raise ImmutableEventError(
            f"Event {event_id} is already confirmed; confirmation is one-way. "
            "Use correct_event() if the confirmed data needs to change."
        )
    from datetime import datetime, timezone

    event.status = EventStatus.CONFIRMED.value
    event.confidence = Decimal("1")
    event.confirmed_at = datetime.now(timezone.utc)
    session.flush()
    return event


def correct_event(
    session: Session,
    event_id: str,
    correction: FinancialEventCorrection,
) -> FinancialEventORM:
    """Supersede an existing event with a corrected copy. The original row
    is never modified — this is what makes the ledger genuinely append-only
    rather than just 'update-averse'."""
    original = _get_or_raise(session, event_id)

    new_event = FinancialEventORM(
        user_id=original.user_id,
        event_type=original.event_type,
        direction=original.direction,
        amount=correction.amount if correction.amount is not None else original.amount,
        currency=(correction.currency.value if correction.currency is not None else original.currency),
        event_date=correction.event_date if correction.event_date is not None else original.event_date,
        category=correction.category if correction.category is not None else original.category,
        status=(correction.status.value if correction.status is not None else original.status),
        confidence=correction.confidence if correction.confidence is not None else original.confidence,
        source_type=original.source_type,
        source_reference=original.source_reference,
        raw_payload=original.raw_payload,
        recurrence_group_id=original.recurrence_group_id,
        supersedes_event_id=original.id,
        correction_reason=correction.reason.value,
        confirmed_at=None,
    )
    session.add(new_event)
    session.flush()
    return new_event


def get_event(session: Session, event_id: str) -> Optional[FinancialEventORM]:
    return session.get(FinancialEventORM, event_id)


def list_ledger(
    session: Session,
    user_id: str,
    *,
    include_superseded: bool = False,
) -> list[FinancialEventORM]:
    """Every non-superseded event for a user, in event_date order. Passing
    include_superseded=True returns the full audit history instead."""
    stmt = select(FinancialEventORM).where(FinancialEventORM.user_id == user_id)
    all_events = list(session.execute(stmt).scalars().all())

    if include_superseded:
        return sorted(all_events, key=lambda e: e.event_date)

    superseded_ids = {e.supersedes_event_id for e in all_events if e.supersedes_event_id}
    return sorted(
        (e for e in all_events if e.id not in superseded_ids),
        key=lambda e: e.event_date,
    )


def _get_or_raise(session: Session, event_id: str) -> FinancialEventORM:
    event = session.get(FinancialEventORM, event_id)
    if event is None:
        raise LookupError(f"No financial event with id={event_id}")
    return event
