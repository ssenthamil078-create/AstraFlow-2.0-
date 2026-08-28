"""
Phase 6 — User account (SQLAlchemy ORM model).

This is the first table in the project that isn't scoped *by* a user_id —
it's the thing user_id refers to. Every other table's `user_id` column
(financial_events, income_sources, goals, documents) predates auth and is
a plain, unindexed-by-FK string (see auth_service.py module docstring for
why that's not changed here). Going forward, `api/deps.get_current_user`
is what guarantees a request's `user_id` corresponds to a real,
authenticated row in this table.
"""

import uuid
from datetime import datetime, timezone

from app.core.types import UTCDateTime
from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class UserORM(Base):
    """One row = one account."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
     default=_utcnow, onupdate=_utcnow, nullable=False
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid only
        return f"<User id={self.id[:8]} email={self.email!r} verified={self.is_verified}>"
