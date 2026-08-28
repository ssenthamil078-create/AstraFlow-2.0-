"""
Phase 4 — Goal / reserve target (SQLAlchemy ORM model).

Unlike a FinancialEvent, a goal is not a record of something that
happened — it's a user-declared target the digital twin measures itself
against. That's why it lives in its own small, directly-editable table
instead of the append-only event ledger: a user changing a savings
target from ₹50,000 to ₹60,000 isn't a correction to history, it's a
new configuration choice.

Progress toward a goal, however, IS derived from the immutable ledger
(see services/goal_tracking.py) — only the *target* is stored here, so
"how much have I actually saved" can never drift from what the ledger
says actually happened.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from app.core.types import UTCDateTime
from sqlalchemy import CheckConstraint, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class GoalORM(Base):
    """One row = one savings target or reserve target for a user."""

    __tablename__ = "goals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    goal_type: Mapped[str] = mapped_column(String(20), nullable=False)   # vocabulary.GoalType
    currency: Mapped[str] = mapped_column(String(3), nullable=False)    # vocabulary.Currency

    # The category of ledger event counted toward this goal's progress.
    # For a SAVINGS_TARGET this is typically "emergency_savings"; for a
    # RESERVE_TARGET it's conventionally "min_cash_reserve", but progress
    # for reserve goals is actually read off the account balance (see
    # goal_tracking.compute_goal_progress) — this field still records the
    # intent for display/grouping purposes.
    linked_category: Mapped[str] = mapped_column(String(40), nullable=False)  # vocabulary.ObligationCategory

    target_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    target_date: Mapped[Optional[datetime]] = mapped_column(UTCDateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
     default=_utcnow, onupdate=_utcnow, nullable=False
    )

    __table_args__ = (
        CheckConstraint("target_amount > 0", name="ck_goal_target_amount_positive"),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Goal id={self.id[:8]} name={self.name!r} type={self.goal_type} target={self.target_amount}>"
