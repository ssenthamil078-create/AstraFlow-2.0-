from datetime import datetime, timedelta, timezone

from app.schemas.threshold import (
    AlertThresholdConfig,
    RiskSignal,
    TriggerReason,
    evaluate_alert,
)


def test_first_time_trigger_fires():
    signal = RiskSignal(
        reason=TriggerReason.EXPECTED_RUNWAY_BELOW_POLICY_TRIGGER,
        condition_id="runway-below-policy",
        current_value=9,
        triggered=True,
    )
    decisions = evaluate_alert([signal])
    assert decisions[0].should_fire is True
    assert decisions[0].suppressed_by_cooldown is False


def test_non_triggered_signal_never_fires():
    signal = RiskSignal(
        reason=TriggerReason.EXPECTED_RUNWAY_BELOW_POLICY_TRIGGER,
        condition_id="runway-below-policy",
        current_value=20,
        triggered=False,
    )
    decisions = evaluate_alert([signal])
    assert decisions[0].should_fire is False


def test_repeat_alert_suppressed_within_cooldown_and_small_change():
    now = datetime.now(timezone.utc)
    signal = RiskSignal(
        reason=TriggerReason.EXPECTED_RUNWAY_BELOW_POLICY_TRIGGER,
        condition_id="runway-below-policy",
        current_value=9.2,  # ~2% change from 9 -> under the 10% override
        triggered=True,
    )
    decisions = evaluate_alert(
        [signal],
        last_alert_at={"runway-below-policy": now - timedelta(hours=2)},
        last_alert_value={"runway-below-policy": 9.0},
        now=now,
    )
    assert decisions[0].should_fire is False
    assert decisions[0].suppressed_by_cooldown is True


def test_cooldown_overridden_when_change_exceeds_10_percent():
    now = datetime.now(timezone.utc)
    signal = RiskSignal(
        reason=TriggerReason.EXPECTED_RUNWAY_BELOW_POLICY_TRIGGER,
        condition_id="runway-below-policy",
        current_value=6.0,  # from 9.0 -> ~33% change, exceeds override threshold
        triggered=True,
    )
    decisions = evaluate_alert(
        [signal],
        last_alert_at={"runway-below-policy": now - timedelta(hours=2)},
        last_alert_value={"runway-below-policy": 9.0},
        now=now,
    )
    assert decisions[0].should_fire is True
    assert decisions[0].suppressed_by_cooldown is False


def test_alert_fires_again_after_cooldown_window_expires():
    now = datetime.now(timezone.utc)
    signal = RiskSignal(
        reason=TriggerReason.EXPECTED_RUNWAY_BELOW_POLICY_TRIGGER,
        condition_id="runway-below-policy",
        current_value=9.1,
        triggered=True,
    )
    decisions = evaluate_alert(
        [signal],
        last_alert_at={"runway-below-policy": now - timedelta(hours=25)},
        last_alert_value={"runway-below-policy": 9.0},
        now=now,
        config=AlertThresholdConfig(cooldown_hours=24),
    )
    assert decisions[0].should_fire is True
    assert decisions[0].suppressed_by_cooldown is False
