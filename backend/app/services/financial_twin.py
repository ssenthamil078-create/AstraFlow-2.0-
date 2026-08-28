"""
Phase 4 — Financial twin orchestration.

Ties together the pieces that stay separate at the module level (event
ledger, obligation classification, goal tracking, state rebuild) for the
four `/api/financial-state...` endpoints. Nothing in this module computes
anything itself beyond simple grouping for the provenance report — the
actual math lives in schemas/financial_state.py and
services/obligation_detection.py / goal_tracking.py, which stay usable and
testable independent of any HTTP concern.

Only `rebuild_and_persist` has a side effect (classification corrections
+ a persisted snapshot row). `get_current_state` and `build_provenance`
are read-only, so a plain `GET /api/financial-state` can never quietly
reclassify events a human hasn't reviewed — reclassification only happens
when `POST /api/financial-state/rebuild` is explicitly called.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.vocabulary import Currency, EventStatus, GoalType, ObligationCategory
from app.models.financial_event import FinancialEventORM
from app.models.financial_state_snapshot import FinancialStateSnapshotORM
from app.schemas.financial_state import FinancialState, rebuild_financial_state
from app.schemas.provenance_report import FinancialStateProvenance, ProvenanceEventRef
from app.services import event_ledger, goal_tracking, obligation_detection

_OBLIGATION_CATEGORY_VALUES = {
    ObligationCategory.RENT.value,
    ObligationCategory.EMI.value,
    ObligationCategory.UTILITIES.value,
    ObligationCategory.INSURANCE.value,
    ObligationCategory.DEBT_PAYMENTS.value,
}


def _load(session: Session, user_id: str, currency: Currency) -> tuple[list[FinancialEventORM], list]:
    events = event_ledger.list_ledger(session, user_id)
    goals = [g for g in goal_tracking.list_goals(session, user_id) if g.currency == currency.value]
    return events, goals


def get_current_state(session: Session, user_id: str, currency: Currency) -> FinancialState:
    events, goals = _load(session, user_id, currency)
    return rebuild_financial_state(user_id, currency, events, goals=goals)


def rebuild_and_persist(
    session: Session, user_id: str, currency: Currency
) -> tuple[FinancialState, FinancialStateSnapshotORM]:
    """Classifies any newly-ingested obligation/discretionary events
    (idempotent — see obligation_detection.apply_classification), rebuilds
    the twin, and persists a snapshot for the timeline."""
    obligation_detection.apply_classification(session, user_id)
    events, goals = _load(session, user_id, currency)
    state = rebuild_financial_state(user_id, currency, events, goals=goals)

    snapshot = FinancialStateSnapshotORM(
        user_id=user_id,
        currency=currency.value,
        confirmed_balance=state.confirmed_balance,
        state_json=state.model_dump(mode="json"),
    )
    session.add(snapshot)
    session.flush()
    return state, snapshot


def list_timeline(
    session: Session, user_id: str, currency: Currency, *, limit: int = 50
) -> list[FinancialStateSnapshotORM]:
    stmt = (
        select(FinancialStateSnapshotORM)
        .where(
            FinancialStateSnapshotORM.user_id == user_id,
            FinancialStateSnapshotORM.currency == currency.value,
        )
        .order_by(FinancialStateSnapshotORM.rebuilt_at.desc())
        .limit(limit)
    )
    return list(session.execute(stmt).scalars().all())


def _ref(event: FinancialEventORM) -> ProvenanceEventRef:
    return ProvenanceEventRef(
        event_id=event.id,
        source_type=event.source_type,
        status=event.status,
        confidence=event.confidence,
        direction=event.direction,
        amount=event.amount,
        event_date=event.event_date,
    )


def build_provenance(session: Session, user_id: str, currency: Currency) -> FinancialStateProvenance:
    events, goals = _load(session, user_id, currency)
    relevant = [
        e for e in events
        if e.user_id == user_id and e.currency == currency.value
    ]

    confirmed_refs = [_ref(e) for e in relevant if e.status == EventStatus.CONFIRMED.value]

    obligation_groups: dict[str, list[ProvenanceEventRef]] = defaultdict(list)
    for e in relevant:
        if e.category not in _OBLIGATION_CATEGORY_VALUES:
            continue
        key = e.category if not e.recurrence_group_id else f"{e.category}:{e.recurrence_group_id}"
        obligation_groups[key].append(_ref(e))

    goal_refs: dict[str, list[ProvenanceEventRef]] = {}
    for goal in goals:
        if goal.goal_type == GoalType.RESERVE_TARGET.value:
            # A reserve's progress is read off the confirmed balance, so
            # the same confirmed-CREDIT/DEBIT events that back the balance
            # are its provenance too.
            goal_refs[goal.id] = confirmed_refs
        else:
            goal_refs[goal.id] = [
                _ref(e)
                for e in relevant
                if e.category == goal.linked_category
                and e.status == EventStatus.CONFIRMED.value
                and e.event_date >= goal.created_at
            ]

    return FinancialStateProvenance(
        user_id=user_id,
        currency=currency,
        generated_at=datetime.now(timezone.utc),
        confirmed_balance_events=confirmed_refs,
        obligations=dict(obligation_groups),
        goals=goal_refs,
    )
