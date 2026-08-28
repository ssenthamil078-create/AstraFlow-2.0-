"""
Phase 5 — Income payment observation (SQLAlchemy ORM model).

A `FinancialEventORM` (Phase 2) only records what actually happened — it
has no notion of "when was this supposed to arrive" or "how much was this
supposed to be". Reliability scoring needs exactly that comparison
(expected vs. actual), so an observation is its own small append-only
table rather than extra columns bolted onto the immutable event ledger.

An observation optionally references the ledger event it corresponds to
(`source_event_id`) purely for provenance/traceability — recalculating
reliability never reads the ledger directly, only this table, so Phase 5
stays decoupled from however Phase 3/4 chose to classify or store events.

Like the event ledger, observations are append-only: a wrong observation
is not edited, it is superseded the same way a financial event is (see
`FinancialEventORM.supersedes_event_id` / `CorrectionReason`), keeping a
consistent "history is corrected by appending, never by mutating" rule
across the whole system.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from app.core.types import UTCDateTime
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class IncomePaymentObservationORM(Base):
    """One row = one expected-vs-actual payment outcome for an income
    source, feeding the reliability formula in
    services/income_reliability.py (spec 4.3)."""

    __tablename__ = "income_payment_observations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    income_source_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("income_sources.id"), index=True, nullable=False
    )
    user_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)

    # --- was the payment received at all ---
    was_received: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # --- timing ---
    expected_date: Mapped[Optional[datetime]] = mapped_column(UTCDateTime, nullable=True)
    actual_date: Mapped[Optional[datetime]] = mapped_column(UTCDateTime, nullable=True)

    # --- amount ---
    expected_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    actual_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)

    # --- data confidence (spec 4.3: 20% weight) ---
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)  # vocabulary.EventSourceType

    # --- optional traceability back to the ledger (Phase 2) ---
    source_event_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("financial_events.id"), nullable=True
    )

    # --- append-only correction chain, mirroring FinancialEventORM ---
    supersedes_observation_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("income_payment_observations.id"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=_utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "(NOT was_received) OR (actual_date IS NOT NULL AND actual_amount IS NOT NULL)",
            name="ck_observation_received_has_actuals",
        ),
        CheckConstraint(
            "expected_amount IS NULL OR expected_amount > 0", name="ck_observation_expected_amount_positive"
        ),
        CheckConstraint(
            "actual_amount IS NULL OR actual_amount > 0", name="ck_observation_actual_amount_positive"
        ),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<IncomePaymentObservation id={self.id[:8]} source={self.income_source_id[:8]} "
            f"received={self.was_received}>"
        )
