"""
Phase 1 — Recommendation-only boundary.

AstraFlow never moves money, places trades, or authorizes a payment. It
produces recommendations a human must accept, modify, ignore, or ask about
(see RecommendationUserResponse in vocabulary.py). This module makes that a
structural guarantee rather than a paragraph in a doc that later code can
drift away from: any function that would need to touch money movement must
call `forbid_money_movement()`, which always raises.

Phase 7 (shock simulator) and Phase 8 (policy engine) both import this.
"""


class MoneyMovementNotSupportedError(RuntimeError):
    """Raised if any code path attempts an action AstraFlow is not allowed
    to perform. This should never be caught and worked around — if you hit
    this, the feature you're building is out of scope for AstraFlow v1."""


FORBIDDEN_ACTIONS = frozenset(
    {
        "transfer_funds",
        "pay_bill",
        "place_trade",
        "buy_investment",
        "sell_investment",
        "cancel_sip",          # AstraFlow can *recommend* pausing a SIP; it cannot execute it
        "close_account",
        "modify_bank_record",
    }
)


def forbid_money_movement(action: str) -> None:
    """Call this at the top of any function that might be tempted to
    actually execute a financial action. Always raises.

    Example:
        def apply_policy_action(action_type, target):
            if action_type == "pause" and target == "optional_investments":
                forbid_money_movement("cancel_sip")  # -> raises, by design
    """
    raise MoneyMovementNotSupportedError(
        f"AstraFlow is recommendation-only. '{action}' would move money or "
        "execute a financial action, which is out of scope for this system. "
        "The correct behavior is to produce an action card the user must "
        "accept, modify, ignore, or ask about — never to execute it."
    )


def is_forbidden(action: str) -> bool:
    """Non-raising check, for validation code (e.g. rejecting a policy
    action type that isn't one of the four allowed verbs in 4.5)."""
    return action in FORBIDDEN_ACTIONS
