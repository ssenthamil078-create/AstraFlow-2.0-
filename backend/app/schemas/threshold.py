"""
Phase 1 — Material risk/opportunity threshold (spec section 4.6).

This was previously an implicit judgment call. It's now a concrete,
testable rule. Phase 1 defines the *rule and its config*; Phase 9 wires it
up against live runway/reliability/goal data. Keeping the definition here
(vs. inventing it inline in Phase 9) means the rule can't quietly change
shape once real data starts flowing through it.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional


class TriggerReason(str, Enum):
    """The five (and only five) reasons an action card may fire, verbatim
    from 4.6. The action card must always cite one of these plus the exact
    number/rule involved — never a vague "something changed"."""

    EXPECTED_RUNWAY_BELOW_POLICY_TRIGGER = "expected_runway_below_policy_trigger"
    STRESS_RUNWAY_BELOW_ZERO = "stress_runway_below_zero"
    RELIABILITY_SCORE_SHIFT = "reliability_score_shift"          # >= 15 points
    GOAL_UNREACHABLE = "goal_unreachable"
    RESTRICTION_LIFTABLE = "restriction_liftable"                # confirmed runway recovered


@dataclass(frozen=True)
class AlertThresholdConfig:
    """Configurable numbers behind the 4.6 rule. Defaults match the spec
    exactly; a user's policy may override `cooldown_hours` and the
    reliability-shift sensitivity, but not remove a trigger reason."""

    reliability_shift_points: float = 15.0
    cooldown_hours: int = 24
    cooldown_override_percent_change: float = 10.0
    # policy-level runway trigger (e.g. 14 days) lives on EmergencyPolicy.trigger,
    # not here — this config only holds the SYSTEM-WIDE constants from 4.6.


@dataclass(frozen=True)
class RiskSignal:
    """One raw, already-computed signal fed into the threshold check.
    Phase 9 is responsible for computing these from real runway/reliability
    output; this module only decides whether they cross the line."""

    reason: TriggerReason
    condition_id: str          # stable identifier for "same unresolved condition" cooldown tracking
    current_value: float
    triggered: bool


@dataclass(frozen=True)
class AlertDecision:
    should_fire: bool
    reason: Optional[TriggerReason]
    condition_id: Optional[str]
    suppressed_by_cooldown: bool = False


def evaluate_alert(
    signals: list[RiskSignal],
    *,
    last_alert_at: Optional[dict[str, datetime]] = None,
    last_alert_value: Optional[dict[str, float]] = None,
    now: Optional[datetime] = None,
    config: AlertThresholdConfig = AlertThresholdConfig(),
) -> list[AlertDecision]:
    """Reference implementation of the 4.6 rule, given already-computed
    signals. Real signal computation (runway numbers, reliability deltas,
    goal reachability) is Phase 6/Phase 9 work — this function only encodes
    the trigger-or-suppress decision, which is Phase 1's job to pin down.

    `last_alert_at` / `last_alert_value` key by `condition_id` and represent
    persisted state from the previous alert for that unresolved condition
    (Phase 9 will back this with a real store).
    """
    now = now or datetime.now(timezone.utc)
    last_alert_at = last_alert_at or {}
    last_alert_value = last_alert_value or {}

    decisions: list[AlertDecision] = []
    for signal in signals:
        if not signal.triggered:
            decisions.append(
                AlertDecision(should_fire=False, reason=None, condition_id=None)
            )
            continue

        prior_time = last_alert_at.get(signal.condition_id)
        prior_value = last_alert_value.get(signal.condition_id)

        within_cooldown = (
            prior_time is not None
            and (now - prior_time) < timedelta(hours=config.cooldown_hours)
        )

        if within_cooldown and prior_value is not None and prior_value != 0:
            percent_change = abs(signal.current_value - prior_value) / abs(prior_value) * 100
            if percent_change <= config.cooldown_override_percent_change:
                decisions.append(
                    AlertDecision(
                        should_fire=False,
                        reason=signal.reason,
                        condition_id=signal.condition_id,
                        suppressed_by_cooldown=True,
                    )
                )
                continue
            # underlying number moved enough to override the cooldown
            decisions.append(
                AlertDecision(
                    should_fire=True,
                    reason=signal.reason,
                    condition_id=signal.condition_id,
                )
            )
            continue

        decisions.append(
            AlertDecision(
                should_fire=True,
                reason=signal.reason,
                condition_id=signal.condition_id,
            )
        )

    return decisions
