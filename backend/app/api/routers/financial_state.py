"""
Phase 4 — Financial-state API (spec 6.1, API #6).

`GET /api/financial-state` is a pure read — computing the twin never has
side effects. `POST /api/financial-state/rebuild` is the only endpoint
that classifies newly-ingested events and persists a snapshot; it's the
one a client calls after ingestion (Phase 3) to bring obligations/
discretionary spending up to date.

Phase 6 — every endpoint now scopes to the authenticated caller
(app.api.deps.get_current_user) instead of a client-supplied `user_id`
query param.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.vocabulary import Currency
from app.models.user import UserORM
from app.schemas.financial_state import FinancialState
from app.schemas.provenance_report import FinancialStateProvenance
from app.services import financial_twin

router = APIRouter(prefix="/api/financial-state", tags=["financial-state"])


@router.get("", response_model=FinancialState)
def get_financial_state(
    currency: Currency = Query(default=Currency.INR),
    current_user: UserORM = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    return financial_twin.get_current_state(session, current_user.id, currency)


@router.post("/rebuild", response_model=FinancialState)
def rebuild_financial_state_endpoint(
    currency: Currency = Query(default=Currency.INR),
    current_user: UserORM = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    state, _snapshot = financial_twin.rebuild_and_persist(session, current_user.id, currency)
    session.commit()
    return state


@router.get("/timeline")
def financial_state_timeline(
    currency: Currency = Query(default=Currency.INR),
    limit: int = Query(default=50, ge=1, le=500),
    current_user: UserORM = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    snapshots = financial_twin.list_timeline(session, current_user.id, currency, limit=limit)
    return [
        {
            "id": s.id,
            "confirmed_balance": s.confirmed_balance,
            "rebuilt_at": s.rebuilt_at,
            "state": s.state_json,
        }
        for s in snapshots
    ]


@router.get("/provenance", response_model=FinancialStateProvenance)
def financial_state_provenance(
    currency: Currency = Query(default=Currency.INR),
    current_user: UserORM = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    return financial_twin.build_provenance(session, current_user.id, currency)
