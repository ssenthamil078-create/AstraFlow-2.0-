"""
Phase 3 — Uploaded document record (bills/receipts, OCR'd via Tesseract).

A document is *not* a financial event. It's the audit trail for an upload:
the raw OCR text, a quality score, and whatever fields could be parsed out
of it. If parsing found enough to act on, this row links to the
FinancialEvent it produced (always created at UNCERTAIN — see
services/ocr_ingestion.py) via `linked_event_id`. If not, the document sits
with status EXTRACTION_FAILED so the review UI can offer manual entry
instead of silently dropping the upload.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from app.core.types import UTCDateTime
from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class DocumentORM(Base):
    """One row per uploaded bill/receipt file."""

    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)

    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)

    # "uploaded" -> "extracted" -> "linked"  |  or -> "extraction_failed"
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="uploaded")

    ocr_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ocr_mean_confidence: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 3), nullable=True)  # 0.000-1.000

    extracted_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    extracted_direction: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # vocabulary.EventDirection
    extracted_date: Mapped[Optional[datetime]] = mapped_column(UTCDateTime, nullable=True)
    extracted_merchant: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)

    extraction_error: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    linked_event_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("financial_events.id"), nullable=True
    )

    uploaded_at: Mapped[datetime] = mapped_column(UTCDateTime, default=_utcnow, nullable=False)
    processed_at: Mapped[Optional[datetime]] = mapped_column(UTCDateTime, nullable=True)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid only
        return f"<Document id={self.id[:8]} filename={self.filename} status={self.status}>"
