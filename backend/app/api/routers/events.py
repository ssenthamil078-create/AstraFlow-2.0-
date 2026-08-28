"""
Phase 3 — Events review & confirmation API.

This is the "Confirmed / Likely / Uncertain" review surface plus the two
actions a human can take: confirm a pending event as-is, or merge it with
a duplicate that ingestion flagged. Both actions go through the Phase 2
event ledger service (services/event_ledger.py), never the ORM directly —
that's what keeps the ledger genuinely append-only.

Phase 6 — every endpoint now scopes to the authenticated caller
(app.api.deps.get_current_user) instead of a client-supplied `user_id`
query param. `confirm_event`/`merge_event` additionally check the target
event actually belongs to that caller, returning 404 (not 403) on a
mismatch so a wrong event_id can't be used to probe which ids exist.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.vocabulary import CorrectionReason, EventStatus
from app.models.user import UserORM
from app.schemas.event import FinancialEventCorrection, FinancialEventRead
from app.schemas.ingestion import MergeEventsRequest
from app.services import event_ledger

router = APIRouter(prefix="/api", tags=["events"])


@router.get("/events", response_model=list[FinancialEventRead])
def list_events(
    status: Optional[str] = Query(default=None, description="Filter to one review bucket."),
    current_user: UserORM = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    events = event_ledger.list_ledger(session, current_user.id)
    if status is not None and status.upper() != "ALL":
        events = [e for e in events if e.status.upper() == status.upper()]
    return [FinancialEventRead.model_validate(e) for e in events]


@router.get("/events/review")
def review_queue(current_user: UserORM = Depends(get_current_user), session: Session = Depends(get_db)):
    events = event_ledger.list_ledger(session, current_user.id)
    buckets: dict[str, list[FinancialEventRead]] = {s.value: [] for s in EventStatus}
    for e in events:
        buckets[e.status].append(FinancialEventRead.model_validate(e))
    return {
        "confirmed": buckets[EventStatus.CONFIRMED.value],
        "likely": buckets[EventStatus.LIKELY.value],
        "uncertain": buckets[EventStatus.UNCERTAIN.value],
        "rejected": buckets[EventStatus.REJECTED.value],
    }


@router.post("/events/{event_id}/confirm", response_model=FinancialEventRead)
def confirm_event(
    event_id: str, current_user: UserORM = Depends(get_current_user), session: Session = Depends(get_db)
):
    existing = event_ledger.get_event(session, event_id)
    if existing is None or existing.user_id != current_user.id:
        raise HTTPException(status_code=404, detail=f"No event with id={event_id}")

    try:
        event = event_ledger.confirm_event(session, event_id)
    except LookupError as exc:
        session.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except event_ledger.ImmutableEventError as exc:
        session.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    session.commit()
    return event


@router.post("/events/{event_id}/reject", response_model=FinancialEventRead)
def reject_event(
    event_id: str, current_user: UserORM = Depends(get_current_user), session: Session = Depends(get_db)
):
    existing = event_ledger.get_event(session, event_id)
    if existing is None or existing.user_id != current_user.id:
        raise HTTPException(status_code=404, detail=f"No event with id={event_id}")

    try:
        event = event_ledger.correct_event(
            session,
            event_id,
            FinancialEventCorrection(
                reason=CorrectionReason.USER_CORRECTION,
                status=EventStatus.REJECTED,
                confidence=Decimal("0"),
            ),
        )
    except LookupError as exc:
        session.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    session.commit()
    return event


@router.get("/events/{event_id}/evidence")
def get_event_evidence(
    event_id: str, current_user: UserORM = Depends(get_current_user), session: Session = Depends(get_db)
):
    existing = event_ledger.get_event(session, event_id)
    if existing is None or existing.user_id != current_user.id:
        raise HTTPException(status_code=404, detail=f"No event with id={event_id}")

    return {
        "eventId": existing.id,
        "title": existing.title,
        "rawEvidence": existing.raw_evidence or {
            "snippet": f"Transaction recorded on {existing.date_occurred}",
            "sourceId": existing.source,
            "timestamp": existing.created_at.isoformat(),
        },
        "status": existing.status,
        "confidence": float(existing.confidence),
        "source": existing.source,
    }


@router.post("/events/{event_id}/merge", response_model=FinancialEventRead)
def merge_event(
    event_id: str,
    request: MergeEventsRequest,
    current_user: UserORM = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    losing = event_ledger.get_event(session, event_id)
    if losing is None or losing.user_id != current_user.id:
        raise HTTPException(status_code=404, detail=f"No event with id={event_id}")

    surviving = event_ledger.get_event(session, request.surviving_event_id)
    if surviving is None or surviving.user_id != current_user.id:
        raise HTTPException(status_code=404, detail=f"No surviving event with id={request.surviving_event_id}")
    if surviving.id == losing.id:
        raise HTTPException(status_code=400, detail="surviving_event_id must differ from the event being merged.")

    try:
        superseded = event_ledger.correct_event(
            session,
            event_id,
            FinancialEventCorrection(
                reason=CorrectionReason.DUPLICATE_RESOLVED,
                status=EventStatus.REJECTED,
                confidence=Decimal("0"),
            ),
        )
    except LookupError as exc:
        session.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    session.commit()
    return superseded

