import pytest

from app.core.boundaries import (
    MoneyMovementNotSupportedError,
    forbid_money_movement,
    is_forbidden,
)


def test_forbid_money_movement_always_raises():
    with pytest.raises(MoneyMovementNotSupportedError):
        forbid_money_movement("cancel_sip")


def test_is_forbidden_recognizes_money_movement_actions():
    assert is_forbidden("transfer_funds") is True
    assert is_forbidden("place_trade") is True


def test_is_forbidden_false_for_recommendation_actions():
    # accept/modify/ignore/ask_why are user RESPONSES to a card, not money
    # movement, and must never be in the forbidden set.
    assert is_forbidden("accept") is False
    assert is_forbidden("modify") is False
    assert is_forbidden("ignore") is False
    assert is_forbidden("ask_why") is False
