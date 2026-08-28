"""
Phase 1 — Personal Financial Emergency Policy schema (spec section 4.5).

The policy is built through a structured UI (priority list + threshold
sliders) and produces this rule object directly. There is no natural-language
parsing step in the critical path — a free-text convenience layer may exist
later (Phase 8, explicitly optional) but it only ever produces a *draft* of
this same schema for human review; it never writes to the active policy.

This module owns validation, so an invalid policy (duplicate priorities, a
forbidden action type, a nonsensical threshold) is rejected at the schema
boundary, before it ever reaches the decision engine in later phases.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.vocabulary import ObligationCategory, PolicyActionType


class PolicyTrigger(BaseModel):
    """When the policy should activate. `safe_runway_days_below` is the
    user-configurable number referenced throughout the spec (e.g. "14 days").
    This is ONE of several conditions checked by the 4.6 threshold rule in
    Phase 9 — the policy only owns this one; the others (stress runway < 0,
    reliability swings, goal unreachability) are system-wide and not
    per-policy configurable.
    """

    safe_runway_days_below: int = Field(
        ...,
        gt=0,
        le=365,
        description="Policy activates when expected runway drops below this many days.",
    )


class PolicyAction(BaseModel):
    """A single ordered action the policy takes once triggered.

    type: one of the four closed verbs from 4.5 — pause, reduce, protect,
    require_confirmation. Anything else is rejected at validation time.
    target: an ObligationCategory the action applies to.
    by_percent: required (and only meaningful) for `reduce`.
    """

    type: PolicyActionType
    target: ObligationCategory
    by_percent: Optional[float] = Field(
        default=None,
        gt=0,
        le=100,
        description="Required for type='reduce'; the percentage to cut the target by.",
    )

    @model_validator(mode="after")
    def _by_percent_only_for_reduce(self) -> "PolicyAction":
        if self.type == PolicyActionType.REDUCE and self.by_percent is None:
            raise ValueError("by_percent is required when action type is 'reduce'.")
        if self.type != PolicyActionType.REDUCE and self.by_percent is not None:
            raise ValueError("by_percent is only meaningful when action type is 'reduce'.")
        return self


class EmergencyPolicy(BaseModel):
    """The full structured policy object (spec 4.5 example, formalized).

    Example (matches the spec's illustration):
        {
          "trigger": {"safe_runway_days_below": 14},
          "priority_order": ["rent", "emi", "utilities", "min_cash_reserve"],
          "actions": [
            {"type": "pause", "target": "optional_investments"},
            {"type": "reduce", "target": "flexible_spending", "by_percent": 30},
            {"type": "protect", "target": "emergency_savings"},
            {"type": "require_confirmation", "target": "debt_payments"}
          ]
        }
    """

    version: int = Field(default=1, ge=1)
    trigger: PolicyTrigger
    priority_order: list[ObligationCategory] = Field(..., min_length=1)
    actions: list[PolicyAction] = Field(..., min_length=1)

    @field_validator("priority_order")
    @classmethod
    def _priority_order_no_duplicates(
        cls, v: list[ObligationCategory]
    ) -> list[ObligationCategory]:
        if len(v) != len(set(v)):
            raise ValueError("priority_order cannot contain duplicate categories.")
        return v

    # NOTE: an earlier draft of this schema required every 'protect' action's
    # target to also appear in priority_order. That turned out to be an
    # invented constraint, not one from the spec: the spec's own canonical
    # example (4.5) protects "emergency_savings", which is a reserve rather
    # than a competing obligation, and is deliberately absent from
    # priority_order. Removed rather than "fixed" — priority_order ranks
    # competing obligations against each other; protect/pause/reduce/
    # require_confirmation can each target anything in ObligationCategory
    # independent of whether it's ranked.

    def action_for(self, target: ObligationCategory) -> Optional[PolicyAction]:
        """Convenience lookup used by later phases' policy evaluator."""
        for action in self.actions:
            if action.target == target:
                return action
        return None


class DraftPolicyProposal(BaseModel):
    """Output of the OPTIONAL free-text-to-draft LLM assist (spec 4.5,
    explicitly a stretch feature, not on the critical path). This is never
    the active policy — it is only ever a proposal awaiting explicit human
    confirmation before it can become an EmergencyPolicy.
    """

    source_text: str = Field(..., min_length=1)
    proposed_policy: EmergencyPolicy
    requires_user_confirmation: bool = Field(default=True, frozen=True)
