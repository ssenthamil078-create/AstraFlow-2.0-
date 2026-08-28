"""
Phase 2 — Canonical financial event (SQLAlchemy ORM model).

This is the single table every input type (transaction, SMS, bill, receipt,
invoice, goal, investment — see EventType in core/vocabulary.py) normalizes
into. The table is append-only at the database level: there is no UPDATE
path exposed anywhere in the service layer (see services/event_ledger.py)
for a CONFIRMED event. Corrections create a new row that references the
row it supersedes.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from app.core.types import UTCDateTime
from sqlalchemy import (
    JSON,
    CheckConstraint,
    ForeignKey,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class FinancialEventORM(Base):
    """One row = one canonical financial event.

    Columns map directly to the fields named in the spec's build order
    (6.1, API #1): amount, currency, date, category, source, confidence,
    status, provenance, recurrence, user ID.
    """

    __tablename__ = "financial_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)

    # --- what happened ---
    event_type: Mapped[str] = mapped_column(String(20), nullable=False)          # vocabulary.EventType
    direction: Mapped[str] = mapped_column(String(10), nullable=False)           # vocabulary.EventDirection
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)      # always positive magnitude
    currency: Mapped[str] = mapped_column(String(3), nullable=False)             # vocabulary.Currency
    event_date: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)      # populated from Phase 4 onward

    # --- how sure are we ---
    status: Mapped[str] = mapped_column(String(20), nullable=False)              # vocabulary.EventStatus
    confidence: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False)   # 0.000–1.000

    # --- where it came from (provenance) ---
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)         # vocabulary.EventSourceType
    source_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    raw_payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)        # original text/OCR output/etc.

    # --- recurrence (detection logic itself is Phase 4; this just stores the tag) ---
    recurrence_group_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)

    # --- append-only correction chain ---
    supersedes_event_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("financial_events.id"), nullable=True
    )
    correction_reason: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)  # vocabulary.CorrectionReason
    superseded_by: Mapped["FinancialEventORM"] = relationship(
        "FinancialEventORM", remote_side=[id], backref="corrections"
    )

    # --- audit timestamps ---
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=_utcnow, nullable=False)
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime, nullable=True)

    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_amount_positive"),
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="ck_confidence_range"),
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid only
        return (
            f"<FinancialEvent id={self.id[:8]} type={self.event_type} "
            f"{self.direction} {self.amount} {self.currency} status={self.status}>"
        )
