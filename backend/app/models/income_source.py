"""
Phase 5 — Income source (SQLAlchemy ORM model).

An income source is configuration a user declares once ("Client A",
"Platform B salary"), the same way a Goal (Phase 4) is configuration
rather than history. What accumulates *history* against a source is a
stream of `IncomePaymentObservationORM` rows (see
models/income_payment_observation.py) — this table only stores the
source's identity, its category (which drives the cold-start default —
see core/vocabulary.INCOME_SOURCE_CATEGORY_DEFAULT_RELIABILITY), and a
small *cache* of the last computed reliability score.

The cache exists so `GET /api/income-sources` (a list view) doesn't need
to recompute every source's full observation history on every call —
`services/income_reliability.py` always recomputes fresh for
`GET /api/income-sources/{id}/reliability`, and only
`POST /api/income-sources/{id}/recalculate` writes the cache. This
mirrors the Phase 4 twin's "GET is a pure read, POST rebuild is the only
side effect" split.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from app.core.types import UTCDateTime
from sqlalchemy import CheckConstraint, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class IncomeSourceORM(Base):
    """One row = one income source a user is tracking."""

    __tablename__ = "income_sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str] = mapped_column(String(30), nullable=False)  # vocabulary.IncomeSourceCategory
    currency: Mapped[str] = mapped_column(String(3), nullable=False)   # vocabulary.Currency

    # Typical amount this source pays — used as the comparison baseline
    # for an observation's amount-consistency score when the observation
    # itself doesn't carry its own per-payment expected_amount. Optional:
    # a brand-new source may not have a typical amount declared yet.
    typical_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)

    # --- cached reliability (written only by recalculate_and_persist) ---
    cached_reliability_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 3), nullable=True)
    cached_observation_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cached_is_provisional: Mapped[Optional[bool]] = mapped_column(nullable=True)
    cached_calculated_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
     default=_utcnow, onupdate=_utcnow, nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "cached_reliability_score IS NULL OR "
            "(cached_reliability_score >= 0 AND cached_reliability_score <= 1)",
            name="ck_income_source_cached_score_range",
        ),
        CheckConstraint("typical_amount IS NULL OR typical_amount > 0", name="ck_income_source_typical_amount"),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<IncomeSource id={self.id[:8]} name={self.name!r} category={self.category}>"
