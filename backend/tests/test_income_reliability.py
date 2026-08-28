from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.core.vocabulary import Currency, EventSourceType, IncomeSourceCategory
from app.schemas.income_source import IncomePaymentObservationCreate, IncomeSourceCreate, IncomeSourceUpdate
from app.services import income_reliability

NOW = datetime(2026, 1, 15, tzinfo=timezone.utc)


def _create_source(db_session, user_id="user-1", **overrides):
    payload = dict(
        name="Client A",
        category=IncomeSourceCategory.FREELANCE_CLIENT,
        currency=Currency.INR,
        typical_amount=Decimal("20000"),
    )
    payload.update(overrides)
    source = income_reliability.create_income_source(db_session, user_id, IncomeSourceCreate.model_validate(payload))
    db_session.commit()
    return source


def _add_observation(
    db_session,
    source_id,
    *,
    days_late: int = 0,
    amount: str = "20000",
    expected_amount: str = "20000",
    was_received: bool = True,
    source_type: EventSourceType = EventSourceType.BANK_FEED,
):
    expected_date = NOW
    if was_received:
        payload = IncomePaymentObservationCreate(
            was_received=True,
            expected_date=expected_date,
            actual_date=expected_date + timedelta(days=days_late),
            expected_amount=Decimal(expected_amount),
            actual_amount=Decimal(amount),
            source_type=source_type,
        )
    else:
        payload = IncomePaymentObservationCreate(
            was_received=False,
            expected_date=expected_date,
            expected_amount=Decimal(expected_amount),
            source_type=source_type,
        )
    obs = income_reliability.record_observation(db_session, source_id, payload)
    db_session.commit()
    return obs


# --------------------------------------------------------------------- #
# Cold-start blend — required test cases at 1, 3, 10, 25 observations
# --------------------------------------------------------------------- #


def test_cold_start_below_3_observations_uses_category_default_only(db_session):
    source = _create_source(db_session)
    _add_observation(db_session, source.id)  # 1 observation, perfect payment

    result = income_reliability.get_reliability(db_session, source.id)

    assert result.observation_count == 1
    assert result.is_provisional is True
    assert result.blend_weight_on_observed == Decimal("0")
    # Even though the single observation is a flawless payment, it must
    # not move the score at all below the 3-observation floor.
    assert result.reliability_score == Decimal("0.55")  # FREELANCE_CLIENT default


def test_cold_start_at_3_observations_blends_30_percent_observed(db_session):
    source = _create_source(db_session)
    for _ in range(3):
        _add_observation(db_session, source.id)  # perfect payments -> observed_score == 1.0

    result = income_reliability.get_reliability(db_session, source.id)

    assert result.observation_count == 3
    assert result.is_provisional is True
    assert result.blend_weight_on_observed == Decimal("0.30")
    assert result.observed_score == Decimal("1.00")
    # 0.30 * 1.0 + 0.70 * 0.55 (category default) == 0.685
    assert result.reliability_score == Decimal("0.685")


def test_cold_start_at_10_observations_uses_observed_score_only(db_session):
    source = _create_source(db_session)
    for _ in range(10):
        _add_observation(db_session, source.id)  # perfect payments

    result = income_reliability.get_reliability(db_session, source.id)

    assert result.observation_count == 10
    assert result.is_provisional is False
    assert result.blend_weight_on_observed == Decimal("1")
    assert result.reliability_score == Decimal("1.00")


def test_cold_start_at_25_observations_still_fully_observed(db_session):
    source = _create_source(db_session)
    for _ in range(25):
        _add_observation(db_session, source.id)

    result = income_reliability.get_reliability(db_session, source.id)

    assert result.observation_count == 25
    assert result.is_provisional is False
    assert result.blend_weight_on_observed == Decimal("1")
    assert result.reliability_score == Decimal("1.00")


def test_blend_weight_ramps_linearly_between_3_and_10(db_session):
    # Spot-check the midpoint of the ramp explicitly, since the formula
    # itself is the thing under test here, not just its endpoints.
    weight_at_6 = income_reliability._blend_weight_for(6)
    # 0.30 + (6-3)/7 * 0.70 = 0.30 + 0.30 = 0.60
    assert weight_at_6 == Decimal("0.60")


# --------------------------------------------------------------------- #
# Sub-scores
# --------------------------------------------------------------------- #


def test_timeliness_scores_1_for_on_time_payment(db_session):
    source = _create_source(db_session)
    _add_observation(db_session, source.id, days_late=0)
    obs = income_reliability.list_observations(db_session, source.id)
    _, timeliness, _, _ = income_reliability.compute_observed_score(obs)
    assert timeliness == Decimal("1")


def test_timeliness_decays_linearly_with_lateness(db_session):
    source = _create_source(db_session)
    _add_observation(db_session, source.id, days_late=7)  # half the 14-day grace period
    obs = income_reliability.list_observations(db_session, source.id)
    _, timeliness, _, _ = income_reliability.compute_observed_score(obs)
    assert timeliness == Decimal("0.5")


def test_timeliness_floors_at_0_for_a_missed_payment(db_session):
    source = _create_source(db_session)
    _add_observation(db_session, source.id, was_received=False)
    obs = income_reliability.list_observations(db_session, source.id)
    _, timeliness, amount_consistency, _ = income_reliability.compute_observed_score(obs)
    assert timeliness == Decimal("0")
    assert amount_consistency == Decimal("0")


def test_amount_consistency_scores_1_for_exact_match(db_session):
    source = _create_source(db_session)
    _add_observation(db_session, source.id, amount="20000", expected_amount="20000")
    obs = income_reliability.list_observations(db_session, source.id)
    _, _, amount_consistency, _ = income_reliability.compute_observed_score(obs)
    assert amount_consistency == Decimal("1")


def test_amount_consistency_scores_0_at_or_beyond_the_deviation_cap(db_session):
    source = _create_source(db_session)
    # 50% deviation == the cap itself
    _add_observation(db_session, source.id, amount="30000", expected_amount="20000")
    obs = income_reliability.list_observations(db_session, source.id)
    _, _, amount_consistency, _ = income_reliability.compute_observed_score(obs)
    assert amount_consistency == Decimal("0")


def test_data_confidence_reflects_source_type(db_session):
    source = _create_source(db_session)
    _add_observation(db_session, source.id, source_type=EventSourceType.OCR_DOCUMENT)
    obs = income_reliability.list_observations(db_session, source.id)
    _, _, _, data_confidence = income_reliability.compute_observed_score(obs)
    assert data_confidence == Decimal("0.60")


def test_composite_weights_are_50_30_20(db_session):
    # A single observation with perfect timeliness, worst-case (capped)
    # amount deviation, and mid-tier data confidence isolates each term.
    source = _create_source(db_session)
    payload = IncomePaymentObservationCreate(
        was_received=True,
        expected_date=NOW,
        actual_date=NOW,  # perfect timeliness -> 1.0
        expected_amount=Decimal("20000"),
        actual_amount=Decimal("30000"),  # 50% deviation -> amount score 0.0
        source_type=EventSourceType.SMS_TEXT,  # data confidence 0.75
    )
    income_reliability.record_observation(db_session, source.id, payload)
    db_session.commit()

    obs = income_reliability.list_observations(db_session, source.id)
    composite, timeliness, amount_consistency, data_confidence = income_reliability.compute_observed_score(obs)

    assert timeliness == Decimal("1")
    assert amount_consistency == Decimal("0")
    assert data_confidence == Decimal("0.75")
    # 0.5*1 + 0.3*0 + 0.2*0.75 = 0.65
    assert composite == Decimal("0.65")


# --------------------------------------------------------------------- #
# Category defaults / cold-start defaults per category
# --------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "category,expected_default",
    [
        (IncomeSourceCategory.SALARIED_EMPLOYER, Decimal("0.90")),
        (IncomeSourceCategory.FREELANCE_CLIENT, Decimal("0.55")),
        (IncomeSourceCategory.PLATFORM_GIG, Decimal("0.60")),
        (IncomeSourceCategory.RENTAL_INCOME, Decimal("0.85")),
        (IncomeSourceCategory.INVESTMENT_RETURN, Decimal("0.75")),
        (IncomeSourceCategory.OTHER, Decimal("0.50")),
    ],
)
def test_new_source_uses_its_category_default(db_session, category, expected_default):
    source = _create_source(db_session, name="New source", category=category)
    result = income_reliability.get_reliability(db_session, source.id)
    assert result.observation_count == 0
    assert result.reliability_score == expected_default
    assert result.observed_score is None


# --------------------------------------------------------------------- #
# CRUD / persistence split
# --------------------------------------------------------------------- #


def test_get_reliability_does_not_persist_the_cache(db_session):
    source = _create_source(db_session)
    for _ in range(5):
        _add_observation(db_session, source.id)

    income_reliability.get_reliability(db_session, source.id)  # read-only
    refreshed = income_reliability.get_income_source(db_session, source.id)
    assert refreshed.cached_reliability_score is None
    assert refreshed.cached_observation_count == 0


def test_recalculate_persists_the_cache(db_session):
    source = _create_source(db_session)
    for _ in range(5):
        _add_observation(db_session, source.id)

    _, result = income_reliability.recalculate_and_persist(db_session, source.id)
    refreshed = income_reliability.get_income_source(db_session, source.id)

    assert refreshed.cached_reliability_score == result.reliability_score
    assert refreshed.cached_observation_count == 5
    assert refreshed.cached_is_provisional is True
    assert refreshed.cached_calculated_at is not None


def test_update_income_source_only_changes_supplied_fields(db_session):
    source = _create_source(db_session)
    updated = income_reliability.update_income_source(
        db_session, source.id, IncomeSourceUpdate(typical_amount=Decimal("25000"))
    )
    db_session.commit()
    assert updated.typical_amount == Decimal("25000")
    assert updated.name == "Client A"  # untouched


def test_recalculate_raises_for_unknown_source(db_session):
    with pytest.raises(LookupError):
        income_reliability.recalculate_and_persist(db_session, "does-not-exist")


def test_observation_missing_amount_falls_back_to_typical_amount(db_session):
    source = _create_source(db_session, typical_amount=Decimal("18000"))
    payload = IncomePaymentObservationCreate(
        was_received=True,
        actual_date=NOW,
        actual_amount=Decimal("18000"),
        source_type=EventSourceType.BANK_FEED,
    )
    obs = income_reliability.record_observation(db_session, source.id, payload)
    assert obs.expected_amount == Decimal("18000")
