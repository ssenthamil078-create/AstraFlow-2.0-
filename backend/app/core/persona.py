"""
Phase 1 — Primary persona.

AstraFlow is built for one primary persona first. Every later phase's default
assumptions (cold-start categories in vocabulary.py, demo dataset shape,
default policy trigger) should trace back to this, not be invented ad hoc.
"""

from dataclasses import dataclass, field

from app.core.vocabulary import Currency, IncomeSourceCategory


@dataclass(frozen=True)
class Persona:
    name: str
    description: str
    primary_currency: Currency
    typical_income_sources: list[IncomeSourceCategory]
    pain_points: list[str]
    non_goals: list[str]


PRIMARY_PERSONA = Persona(
    name="Riya — the variable-income freelancer",
    description=(
        "A freelance/gig-economy or small-business earner whose income arrives "
        "irregularly in timing and sometimes in amount, but who still has fixed "
        "obligations (rent, EMI, utilities) due on fixed dates. She does not need "
        "a budgeting app that assumes a steady monthly salary; she needs to know, "
        "right now, how many days she can safely spend against, given what's "
        "actually confirmed versus merely expected."
    ),
    primary_currency=Currency.INR,
    typical_income_sources=[
        IncomeSourceCategory.FREELANCE_CLIENT,
        IncomeSourceCategory.PLATFORM_GIG,
    ],
    pain_points=[
        "Can't tell confirmed money apart from merely-expected money at a glance.",
        "Fixed obligations don't wait for late client payments.",
        "No visibility into which clients are historically reliable vs. risky.",
        "Existing budgeting apps assume predictable monthly income.",
        "Wants to know what to cut BEFORE a shortfall happens, not after.",
    ],
    non_goals=[
        "AstraFlow does not move money, place trades, or pay bills on the user's behalf.",
        "AstraFlow does not predict market returns or give investment advice.",
        "AstraFlow does not require live bank credentials in v1 (CSV/manual/SMS-paste only).",
    ],
)


# Secondary persona, explicitly out of scope for the hackathon build — listed
# so later phases don't accidentally over-generalize the UI/data model for it.
SECONDARY_PERSONA_NOTE = (
    "A salaried employee with predictable income is a secondary, lower-priority "
    "persona: the same engine works for them (their income sources just carry a "
    "higher cold-start default reliability), but no UI/UX work is spent tailoring "
    "the product to steady-income assumptions in v1."
)
