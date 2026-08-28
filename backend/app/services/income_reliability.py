"""
Phase 5 — Income reliability score.

Implements spec 4.3 exactly:

    reliability = 50% payment-timeliness score
                + 30% amount-consistency score
                + 20% data-confidence score

    cold-start blend:
        observations < 3           -> category default only
        3 <= observations < 10     -> weighted average of (observed, category
                                       default), weight on observed rising
                                       linearly from 30% to 100%
        observations >= 10         -> observed score only

Every function here is a pure computation over a list of
`IncomePaymentObservationORM` rows plus an `IncomeSourceCategory` — no
database access happens in this module except in the thin
create/list/record/persist helpers at the bottom, which mirror the
Phase 4 goal_tracking.py split ("CRUD is separate from the pure scoring
math").
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.vocabulary import (
    INCOME_SOURCE_CATEGORY_DEFAULT_RELIABILITY,
    EventSourceType,
    IncomeSourceCategory,
)
from app.models.income_payment_observation import IncomePaymentObservationORM
from app.models.income_source import IncomeSourceORM
from app.schemas.income_source import IncomePaymentObservationCreate, IncomeSourceCreate, IncomeSourceUpdate

# --- composite weights (spec 4.3) ---
WEIGHT_TIMELINESS = Decimal("0.50")
WEIGHT_AMOUNT_CONSISTENCY = Decimal("0.30")
WEIGHT_DATA_CONFIDENCE = Decimal("0.20")

# --- cold-start thresholds (spec 4.3) ---
COLD_START_MIN_OBSERVATIONS = 3    # below this: category default only
COLD_START_FULL_TRUST_OBSERVATIONS = 10  # at/above this: observed score only
_COLD_START_BLEND_SPAN = COLD_START_FULL_TRUST_OBSERVATIONS - COLD_START_MIN_OBSERVATIONS  # 7
_COLD_START_MIN_BLEND_WEIGHT = Decimal("0.30")   # weight on observed score at exactly 3 observations
_COLD_START_MAX_BLEND_WEIGHT = Decimal("1.00")   # weight on observed score at 10+ observations

# --- timeliness sub-score ---
# A payment that arrives on or before its expected date scores 1.0.
# Lateness decays linearly to 0.0 over this many days, chosen so a
# payment more than two weeks late reads as fully unreliable timing
# rather than merely "a bit late" — this is the number the runway's
# stress scenario (Phase 6) needs to be conservative about.
TIMELINESS_LATE_GRACE_DAYS = Decimal("14")

# --- amount-consistency sub-score ---
# The fractional deviation from the expected amount at which the
# amount-consistency score bottoms out at 0.0. A payment exactly on the
# expected amount scores 1.0; deviation is capped here rather than
# scoring negative-but-clamped, so one wildly-off invoice can't make the
# sub-score meaningless by comparison to the rest.
AMOUNT_DEVIATION_CAP = Decimal("0.50")

# --- data-confidence sub-score (spec 4.3: "source of the record — bank
# feed vs. OCR'd SMS vs. manual entry") ---
DATA_CONFIDENCE_BY_SOURCE_TYPE: dict[EventSourceType, Decimal] = {
    EventSourceType.BANK_FEED: Decimal("1.00"),
    EventSourceType.CSV_UPLOAD: Decimal("0.90"),
    EventSourceType.SMS_TEXT: Decimal("0.75"),
    EventSourceType.OCR_DOCUMENT: Decimal("0.60"),
    EventSourceType.MANUAL_ENTRY: Decimal("0.50"),
}


@dataclass
class ReliabilityResult:
    """Full breakdown behind one reliability number — every field the
    spec asks to be displayed alongside the bare score (observation
    count, provisional flag) plus enough of the working to make the
    number explainable end to end."""

    reliability_score: Decimal
    observation_count: int
    is_provisional: bool
    category_default_used: Decimal
    blend_weight_on_observed: Decimal
    observed_score: Optional[Decimal]
    timeliness_score: Optional[Decimal]
    amount_consistency_score: Optional[Decimal]
    data_confidence_score: Optional[Decimal]
    calculated_at: datetime


def _clamp01(value: Decimal) -> Decimal:
    if value < 0:
        return Decimal("0")
    if value > 1:
        return Decimal("1")
    return value


def _timeliness_sub_score(observation: IncomePaymentObservationORM) -> Decimal:
    """1.0 for on-time-or-early; 0.0 for a payment that never arrived;
    linear decay to 0.0 over TIMELINESS_LATE_GRACE_DAYS when late;
    neutral (1.0) when there's no expected_date to judge lateness
    against, since a source can't be penalized for a timing claim that
    was never made."""
    if not observation.was_received:
        return Decimal("0")
    if observation.expected_date is None or observation.actual_date is None:
        return Decimal("1")

    days_late = (observation.actual_date - observation.expected_date).total_seconds() / 86400
    if days_late <= 0:
        return Decimal("1")

    days_late_decimal = Decimal(str(days_late))
    return _clamp01(Decimal("1") - (days_late_decimal / TIMELINESS_LATE_GRACE_DAYS))


def _amount_consistency_sub_score(observation: IncomePaymentObservationORM) -> Decimal:
    """1.0 for an exact amount match; 0.0 for a missed payment or a
    deviation at/beyond AMOUNT_DEVIATION_CAP; linear in between."""
    if not observation.was_received:
        return Decimal("0")
    if observation.expected_amount is None or observation.expected_amount == 0:
        # No baseline to compare against — can't judge consistency, so
        # this observation contributes a neutral score rather than
        # dragging the average down for a data gap that isn't the
        # payer's fault.
        return Decimal("1")

    deviation = abs(observation.actual_amount - observation.expected_amount) / observation.expected_amount
    return _clamp01(Decimal("1") - (deviation / AMOUNT_DEVIATION_CAP))


def _data_confidence_sub_score(observation: IncomePaymentObservationORM) -> Decimal:
    return DATA_CONFIDENCE_BY_SOURCE_TYPE[EventSourceType(observation.source_type)]


def _average(values: list[Decimal]) -> Decimal:
    return sum(values, Decimal("0")) / len(values)


def compute_observed_score(
    observations: list[IncomePaymentObservationORM],
) -> Optional[tuple[Decimal, Decimal, Decimal, Decimal]]:
    """Returns (composite, timeliness, amount_consistency, data_confidence)
    computed purely from this source's own observation history, or None
    if there are no observations at all (nothing to observe yet)."""
    if not observations:
        return None

    timeliness = _average([_timeliness_sub_score(o) for o in observations])
    amount_consistency = _average([_amount_consistency_sub_score(o) for o in observations])
    data_confidence = _average([_data_confidence_sub_score(o) for o in observations])

    composite = (
        WEIGHT_TIMELINESS * timeliness
        + WEIGHT_AMOUNT_CONSISTENCY * amount_consistency
        + WEIGHT_DATA_CONFIDENCE * data_confidence
    )
    return composite, timeliness, amount_consistency, data_confidence


def _blend_weight_for(observation_count: int) -> Decimal:
    """The weight put on the observed score at a given observation
    count (spec 4.3's linear 30% -> 100% ramp from 3 to 10
    observations)."""
    if observation_count < COLD_START_MIN_OBSERVATIONS:
        return Decimal("0")
    if observation_count >= COLD_START_FULL_TRUST_OBSERVATIONS:
        return Decimal("1")

    steps_into_ramp = Decimal(observation_count - COLD_START_MIN_OBSERVATIONS)
    span = Decimal(_COLD_START_BLEND_SPAN)
    return _COLD_START_MIN_BLEND_WEIGHT + (steps_into_ramp / span) * (
        _COLD_START_MAX_BLEND_WEIGHT - _COLD_START_MIN_BLEND_WEIGHT
    )


def compute_reliability(
    category: IncomeSourceCategory,
    observations: list[IncomePaymentObservationORM],
) -> ReliabilityResult:
    """Pure function: category + observation history in, a fully
    explainable ReliabilityResult out. No database access — this is what
    both the live `GET .../reliability` read and the persisted
    `POST .../recalculate` write call underneath."""
    category_default = Decimal(str(INCOME_SOURCE_CATEGORY_DEFAULT_RELIABILITY[category]))
    observation_count = len(observations)

    observed = compute_observed_score(observations)
    if observed is None:
        observed_score = timeliness = amount_consistency = data_confidence = None
    else:
        observed_score, timeliness, amount_consistency, data_confidence = observed

    weight_on_observed = _blend_weight_for(observation_count)

    if observed_score is None:
        # No history at all: the category default IS the score, and the
        # blend weight is definitionally 0 regardless of what the ramp
        # formula would say (it agrees for observation_count < 3 anyway).
        final_score = category_default
        weight_on_observed = Decimal("0")
    else:
        final_score = (weight_on_observed * observed_score) + ((Decimal("1") - weight_on_observed) * category_default)

    return ReliabilityResult(
        reliability_score=_clamp01(final_score),
        observation_count=observation_count,
        is_provisional=observation_count < COLD_START_FULL_TRUST_OBSERVATIONS,
        category_default_used=category_default,
        blend_weight_on_observed=weight_on_observed,
        observed_score=observed_score,
        timeliness_score=timeliness,
        amount_consistency_score=amount_consistency,
        data_confidence_score=data_confidence,
        calculated_at=datetime.now(timezone.utc),
    )


# --------------------------------------------------------------------- #
# CRUD / persistence helpers (thin — the math above stays DB-free)
# --------------------------------------------------------------------- #


def create_income_source(session: Session, user_id: str, payload: IncomeSourceCreate) -> IncomeSourceORM:
    source = IncomeSourceORM(
        user_id=user_id,
        name=payload.name,
        category=payload.category.value,
        currency=payload.currency.value,
        typical_amount=payload.typical_amount,
    )
    session.add(source)
    session.flush()
    return source


def update_income_source(session: Session, income_source_id: str, payload: IncomeSourceUpdate) -> IncomeSourceORM:
    source = _get_source_or_raise(session, income_source_id)
    if payload.name is not None:
        source.name = payload.name
    if payload.typical_amount is not None:
        source.typical_amount = payload.typical_amount
    session.flush()
    return source


def list_income_sources(session: Session, user_id: str) -> list[IncomeSourceORM]:
    stmt = select(IncomeSourceORM).where(IncomeSourceORM.user_id == user_id).order_by(IncomeSourceORM.created_at)
    return list(session.execute(stmt).scalars().all())


def get_income_source(session: Session, income_source_id: str) -> Optional[IncomeSourceORM]:
    return session.get(IncomeSourceORM, income_source_id)


def get_income_source_or_raise(session: Session, income_source_id: str) -> IncomeSourceORM:
    """Public counterpart to get_income_source() for call sites (routers)
    that want a LookupError -> 404 instead of a bare None check."""
    source = session.get(IncomeSourceORM, income_source_id)
    if source is None:
        raise LookupError(f"No income source with id={income_source_id}")
    return source


# Internal alias kept for readability at call sites within this module.
_get_source_or_raise = get_income_source_or_raise


def record_observation(
    session: Session, income_source_id: str, payload: IncomePaymentObservationCreate
) -> IncomePaymentObservationORM:
    source = _get_source_or_raise(session, income_source_id)
    observation = IncomePaymentObservationORM(
        income_source_id=source.id,
        user_id=source.user_id,
        was_received=payload.was_received,
        expected_date=payload.expected_date,
        actual_date=payload.actual_date,
        expected_amount=payload.expected_amount if payload.expected_amount is not None else source.typical_amount,
        actual_amount=payload.actual_amount,
        source_type=payload.source_type.value,
        source_event_id=payload.source_event_id,
    )
    session.add(observation)
    session.flush()
    return observation


def list_observations(session: Session, income_source_id: str) -> list[IncomePaymentObservationORM]:
    stmt = (
        select(IncomePaymentObservationORM)
        .where(IncomePaymentObservationORM.income_source_id == income_source_id)
        .order_by(IncomePaymentObservationORM.created_at)
    )
    return list(session.execute(stmt).scalars().all())


def get_reliability(session: Session, income_source_id: str) -> ReliabilityResult:
    """Live, read-only computation — never writes the cache. This is
    what `GET /api/income-sources/{id}/reliability` calls, mirroring
    Phase 4's `GET /api/financial-state` being a pure read."""
    source = _get_source_or_raise(session, income_source_id)
    observations = list_observations(session, income_source_id)
    return compute_reliability(IncomeSourceCategory(source.category), observations)


def recalculate_and_persist(session: Session, income_source_id: str) -> tuple[IncomeSourceORM, ReliabilityResult]:
    """The one write path — recomputes and caches the score onto the
    IncomeSourceORM row, the same way `POST /api/financial-state/rebuild`
    is the only path that persists a twin snapshot."""
    source = _get_source_or_raise(session, income_source_id)
    result = get_reliability(session, income_source_id)

    source.cached_reliability_score = result.reliability_score
    source.cached_observation_count = result.observation_count
    source.cached_is_provisional = result.is_provisional
    source.cached_calculated_at = result.calculated_at
    session.flush()
    return source, result
