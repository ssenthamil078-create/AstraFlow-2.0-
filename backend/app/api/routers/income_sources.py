"""
Phase 5 — Income Reliability Score API.

Spec 6.1 (API #7) numbers only three endpoints:
    GET  /api/income-sources
    GET  /api/income-sources/{id}/reliability
    POST /api/income-sources/{id}/recalculate

As with Phase 4's goals router, creating a source and recording a payment
observation aren't separately numbered in the master spec, but without
them there is no way to ever populate the three endpoints above with
real data — so this router adds POST /api/income-sources and the
observation endpoints, the same "usability addition on top of the
numbered contract" pattern goals.py already established.

Phase 6 — every endpoint now scopes to the authenticated caller
(app.api.deps.get_current_user) instead of a client-supplied `user_id`.
Endpoints addressed by `income_source_id` check that the source belongs
to the caller, returning 404 (not 403) on a mismatch.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import UserORM
from app.schemas.income_source import (
    IncomePaymentObservationCreate,
    IncomePaymentObservationRead,
    IncomeReliabilityRead,
    IncomeSourceCreate,
    IncomeSourceRead,
    IncomeSourceUpdate,
)
from app.services import income_reliability

router = APIRouter(prefix="/api/income-sources", tags=["income-sources"])


def _owned_source_or_404(session: Session, income_source_id: str, current_user: UserORM):
    source = income_reliability.get_income_source(session, income_source_id)
    if source is None or source.user_id != current_user.id:
        raise HTTPException(status_code=404, detail=f"No income source with id={income_source_id}")
    return source


@router.post("", response_model=IncomeSourceRead)
def create_income_source(
    payload: IncomeSourceCreate,
    current_user: UserORM = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    source = income_reliability.create_income_source(session, current_user.id, payload)
    session.commit()
    return source


@router.get("", response_model=list[IncomeSourceRead])
def list_income_sources(current_user: UserORM = Depends(get_current_user), session: Session = Depends(get_db)):
    return income_reliability.list_income_sources(session, current_user.id)


@router.patch("/{income_source_id}", response_model=IncomeSourceRead)
def update_income_source(
    income_source_id: str,
    payload: IncomeSourceUpdate,
    current_user: UserORM = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    _owned_source_or_404(session, income_source_id, current_user)
    try:
        source = income_reliability.update_income_source(session, income_source_id, payload)
    except LookupError as exc:
        session.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    session.commit()
    return source


@router.post("/{income_source_id}/observations", response_model=IncomePaymentObservationRead)
def record_observation(
    income_source_id: str,
    payload: IncomePaymentObservationCreate,
    current_user: UserORM = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    _owned_source_or_404(session, income_source_id, current_user)
    try:
        observation = income_reliability.record_observation(session, income_source_id, payload)
    except LookupError as exc:
        session.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    session.commit()
    return observation


@router.get("/{income_source_id}/observations", response_model=list[IncomePaymentObservationRead])
def list_observations(
    income_source_id: str,
    current_user: UserORM = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    _owned_source_or_404(session, income_source_id, current_user)
    return income_reliability.list_observations(session, income_source_id)


@router.get("/{income_source_id}/reliability", response_model=IncomeReliabilityRead)
def get_reliability(
    income_source_id: str,
    current_user: UserORM = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    source = _owned_source_or_404(session, income_source_id, current_user)
    try:
        result = income_reliability.get_reliability(session, income_source_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return IncomeReliabilityRead(
        income_source_id=income_source_id,
        category=source.category,
        reliability_score=result.reliability_score,
        observation_count=result.observation_count,
        is_provisional=result.is_provisional,
        category_default_used=result.category_default_used,
        observed_score=result.observed_score,
        blend_weight_on_observed=result.blend_weight_on_observed,
        timeliness_score=result.timeliness_score,
        amount_consistency_score=result.amount_consistency_score,
        data_confidence_score=result.data_confidence_score,
        calculated_at=result.calculated_at,
    )


@router.post("/{income_source_id}/recalculate", response_model=IncomeReliabilityRead)
def recalculate_reliability(
    income_source_id: str,
    current_user: UserORM = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    _owned_source_or_404(session, income_source_id, current_user)
    try:
        source, result = income_reliability.recalculate_and_persist(session, income_source_id)
    except LookupError as exc:
        session.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    session.commit()

    return IncomeReliabilityRead(
        income_source_id=income_source_id,
        category=source.category,
        reliability_score=result.reliability_score,
        observation_count=result.observation_count,
        is_provisional=result.is_provisional,
        category_default_used=result.category_default_used,
        observed_score=result.observed_score,
        blend_weight_on_observed=result.blend_weight_on_observed,
        timeliness_score=result.timeliness_score,
        amount_consistency_score=result.amount_consistency_score,
        data_confidence_score=result.data_confidence_score,
        calculated_at=result.calculated_at,
    )


