"""
Phase 4 — Financial-state snapshot (SQLAlchemy ORM model).

The digital twin itself is never stored as mutable state — it's always
rebuilt from the event ledger (see schemas/financial_state.py). This
table exists only so `GET /api/financial-state/timeline` has something to
read: each `POST /api/financial-state/rebuild` call persists a read-only
snapshot of what the pure rebuild function produced at that moment, the
same way a bank statement is a point-in-time snapshot of a ledger that
keeps moving. Nothing ever reads this table as the source of truth — a
snapshot can always be reproduced byte-for-byte by re-running the rebuild
against the ledger as it stood at that time.
"""

import uuid
from datetime import datetime, timezone

from app.core.types import UTCDateTime
from sqlalchemy import JSON, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class FinancialStateSnapshotORM(Base):
    __tablename__ = "financial_state_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    confirmed_balance: Mapped[str] = mapped_column(Numeric(14, 2), nullable=False)

    # Full FinancialState (Phase 2 shape + Phase 4 additions), serialized,
    # so the timeline can show exactly what the API returned at that
    # moment without re-deriving it from a ledger that has since moved on.
    state_json: Mapped[dict] = mapped_column(JSON, nullable=False)

    rebuilt_at: Mapped[datetime] = mapped_column(UTCDateTime, default=_utcnow, nullable=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<FinancialStateSnapshot id={self.id[:8]} user={self.user_id} at={self.rebuilt_at}>"
