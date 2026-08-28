import pytest
from pydantic import ValidationError

from app.schemas.policy import EmergencyPolicy


VALID_POLICY = {
    "trigger": {"safe_runway_days_below": 14},
    "priority_order": ["rent", "emi", "utilities", "min_cash_reserve"],
    "actions": [
        {"type": "pause", "target": "optional_investments"},
        {"type": "reduce", "target": "flexible_spending", "by_percent": 30},
        {"type": "protect", "target": "emergency_savings"},
        {"type": "require_confirmation", "target": "debt_payments"},
    ],
}


def test_spec_example_policy_is_valid():
    policy = EmergencyPolicy.model_validate(VALID_POLICY)
    assert policy.trigger.safe_runway_days_below == 14
    assert len(policy.priority_order) == 4


def test_duplicate_priority_order_rejected():
    bad = {**VALID_POLICY, "priority_order": ["rent", "rent", "emi"]}
    with pytest.raises(ValidationError):
        EmergencyPolicy.model_validate(bad)


def test_reduce_without_by_percent_rejected():
    bad = {
        **VALID_POLICY,
        "actions": [{"type": "reduce", "target": "flexible_spending"}],
    }
    with pytest.raises(ValidationError):
        EmergencyPolicy.model_validate(bad)


def test_by_percent_on_non_reduce_rejected():
    bad = {
        **VALID_POLICY,
        "actions": [
            {"type": "pause", "target": "optional_investments", "by_percent": 10}
        ],
    }
    with pytest.raises(ValidationError):
        EmergencyPolicy.model_validate(bad)


def test_protect_target_need_not_be_in_priority_order():
    # Matches the spec's own example: "emergency_savings" is protected but
    # is a reserve, not a competing obligation, so it's deliberately absent
    # from priority_order.
    policy = EmergencyPolicy.model_validate(
        {
            **VALID_POLICY,
            "priority_order": ["rent"],
            "actions": [{"type": "protect", "target": "emergency_savings"}],
        }
    )
    assert policy.priority_order == ["rent"]


def test_invalid_action_type_rejected():
    bad = {
        **VALID_POLICY,
        "actions": [{"type": "delete_everything", "target": "rent"}],
    }
    with pytest.raises(ValidationError):
        EmergencyPolicy.model_validate(bad)


def test_trigger_days_must_be_positive():
    bad = {**VALID_POLICY, "trigger": {"safe_runway_days_below": 0}}
    with pytest.raises(ValidationError):
        EmergencyPolicy.model_validate(bad)


def test_action_for_lookup():
    policy = EmergencyPolicy.model_validate(VALID_POLICY)
    from app.core.vocabulary import ObligationCategory

    action = policy.action_for(ObligationCategory.FLEXIBLE_SPENDING)
    assert action is not None
    assert action.by_percent == 30
    assert policy.action_for(ObligationCategory.RENT) is None
