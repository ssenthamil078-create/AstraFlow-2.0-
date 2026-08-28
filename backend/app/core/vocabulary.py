"""
Phase 1 — Canonical vocabulary.

Every later phase (event schema in Phase 2, truth layer in Phase 3, reliability
scoring in Phase 5, policy engine in Phase 8...) imports these enums instead of
redefining strings inline. This is what keeps "confirmed" from turning into
"CONFIRMED" / "Confirmed" / "verified" in three different modules.
"""

from enum import Enum


class Currency(str, Enum):
    """Currencies AstraFlow v1 supports. Amounts are always stored with an
    explicit currency — never assumed. Multi-currency conversion is out of
    scope for the hackathon build; every user operates in a single currency."""

    INR = "INR"
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"


class EventType(str, Enum):
    """What kind of real-world thing produced a financial event."""

    TRANSACTION = "transaction"       # a bank/card movement, confirmed or from CSV
    SMS = "sms"                       # parsed/pasted bank SMS
    BILL = "bill"                     # an upcoming or paid bill
    RECEIPT = "receipt"               # proof of a completed payment
    INVOICE = "invoice"               # money owed to or by the user
    GOAL = "goal"                     # a savings/spending target, not itself cash movement
    INVESTMENT = "investment"         # SIP, deposit, or similar recurring contribution


class EventStatus(str, Enum):
    """The truth-layer state of a financial event (Phase 3).

    This is the single vocabulary for "how sure are we this happened as
    recorded" — the UI's Confirmed / Likely / Uncertain review screen reads
    directly off this enum, nothing else.
    """

    CONFIRMED = "confirmed"           # verified against a reconciled source (e.g. bank feed, CSV)
    LIKELY = "likely"                 # extracted/parsed but not yet independently confirmed
    UNCERTAIN = "uncertain"           # duplicate/conflict flagged, or low-confidence extraction
    REJECTED = "rejected"             # user explicitly dismissed it


class EventSourceType(str, Enum):
    """Where the underlying data point came from — feeds the data-confidence
    component of the reliability score (see 4.3: 20% weight)."""

    BANK_FEED = "bank_feed"
    CSV_UPLOAD = "csv_upload"
    SMS_TEXT = "sms_text"
    OCR_DOCUMENT = "ocr_document"
    MANUAL_ENTRY = "manual_entry"


class IncomeSourceCategory(str, Enum):
    """Cold-start category defaults (4.3) key off this enum — every income
    source must be tagged with exactly one category so a new source has a
    sane starting reliability before it has payment history."""

    SALARIED_EMPLOYER = "salaried_employer"
    FREELANCE_CLIENT = "freelance_client"
    PLATFORM_GIG = "platform_gig"          # e.g. marketplace/gig-platform payouts
    RENTAL_INCOME = "rental_income"
    INVESTMENT_RETURN = "investment_return"
    OTHER = "other"


# Cold-start category default reliability scores, referenced by Phase 5.
# Kept here (not duplicated in the reliability module) because it's part of
# the shared vocabulary a new income source is classified against.
INCOME_SOURCE_CATEGORY_DEFAULT_RELIABILITY: dict[IncomeSourceCategory, float] = {
    IncomeSourceCategory.SALARIED_EMPLOYER: 0.90,
    IncomeSourceCategory.FREELANCE_CLIENT: 0.55,
    IncomeSourceCategory.PLATFORM_GIG: 0.60,
    IncomeSourceCategory.RENTAL_INCOME: 0.85,
    IncomeSourceCategory.INVESTMENT_RETURN: 0.75,
    IncomeSourceCategory.OTHER: 0.50,
}


class ObligationCategory(str, Enum):
    """Protected-obligation vocabulary — this is the closed set of values
    that can appear in a policy's `priority_order` (4.5). Keeping it a
    closed enum (not free text) is what makes the policy engine deterministic."""

    RENT = "rent"
    EMI = "emi"
    UTILITIES = "utilities"
    MIN_CASH_RESERVE = "min_cash_reserve"
    INSURANCE = "insurance"
    DEBT_PAYMENTS = "debt_payments"
    OPTIONAL_INVESTMENTS = "optional_investments"
    FLEXIBLE_SPENDING = "flexible_spending"
    EMERGENCY_SAVINGS = "emergency_savings"


class PolicyActionType(str, Enum):
    """Closed set of action verbs a policy rule can express (4.5)."""

    PAUSE = "pause"
    REDUCE = "reduce"
    PROTECT = "protect"
    REQUIRE_CONFIRMATION = "require_confirmation"


class RunwayMeasure(str, Enum):
    """The three distinct runway measures from 4.2 — never conflated."""

    CONFIRMED = "confirmed_runway"
    EXPECTED = "expected_runway"
    STRESS = "stress_runway"


class RecommendationUserResponse(str, Enum):
    """The four, and only four, ways a user can respond to an action card
    (Phase 9 / product workflow step 7). Nothing in the system may act on
    the user's money beyond recording one of these."""

    ACCEPT = "accept"
    MODIFY = "modify"
    IGNORE = "ignore"
    ASK_WHY = "ask_why"


class EventDirection(str, Enum):
    """Added in Phase 2. Every financial event stores a positive magnitude
    (`amount`) plus an explicit direction — never a signed float — so
    "is this money in or out" is never inferred from a sign convention
    that a later module could get backwards.
    """

    CREDIT = "credit"   # money coming in (income, refund, goal contribution reversal)
    DEBIT = "debit"     # money going out (expense, obligation payment, investment contribution)


class GoalType(str, Enum):
    """Added in Phase 4. The two kinds of target the digital twin tracks
    progress against (spec: "goals and reserve tracking").

    SAVINGS_TARGET — an amount the user is building up toward by a date
    (e.g. a house deposit). Progress is read off CREDIT events tagged
    with the goal's linked_category.
    RESERVE_TARGET — a standing cash-cushion level (e.g. "keep ₹50,000
    minimum in the account"). Progress is read off the account's current
    confirmed balance rather than a dedicated event stream, since a
    reserve is a level to maintain, not a total to accumulate.
    """

    SAVINGS_TARGET = "savings_target"
    RESERVE_TARGET = "reserve_target"


class CorrectionReason(str, Enum):
    """Added in Phase 2. The event ledger is append-only (see spec 4.1's
    'immutable financial event ledger' and Phase 2's data model). A wrong
    or outdated event is never edited in place — it is superseded by a new
    event carrying one of these reasons, so the audit trail always explains
    *why* a correction happened, not just that one did.
    """

    DUPLICATE_RESOLVED = "duplicate_resolved"
    AMOUNT_CORRECTED = "amount_corrected"
    DATE_CORRECTED = "date_corrected"
    CATEGORY_RECLASSIFIED = "category_reclassified"
    USER_DISMISSED = "user_dismissed"
    OCR_RE_EXTRACTION = "ocr_re_extraction"
