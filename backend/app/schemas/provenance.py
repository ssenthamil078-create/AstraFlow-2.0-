"""
Phase 2 — Source provenance.

Every event must be able to answer "where did this number come from, and
how sure are we it was read correctly" independent of whether the *payer*
is reliable (that's Phase 5's job). This schema captures the former.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from app.core.vocabulary import EventSourceType


class SourceProvenance(BaseModel):
    """Where a financial event's data came from, and how it was read.

    `source_reference` is intentionally generic: a bank feed transaction ID,
    a CSV row number, an SMS message ID, or an uploaded document's file ID,
    depending on `source_type`.
    """

    source_type: EventSourceType
    source_reference: Optional[str] = Field(
        default=None,
        description="Bank txn ID / CSV row ref / SMS message ID / document ID, depending on source_type.",
    )
    ingested_at: datetime
    extraction_method: Optional[str] = Field(
        default=None,
        description="e.g. 'tesseract-ocr', 'ollama-extraction', 'manual'. Populated from Phase 3 onward.",
    )
    raw_excerpt: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Original text/snippet the event was extracted from, kept for audit — never edited.",
    )

    @model_validator(mode="after")
    def _manual_entry_needs_no_reference(self) -> "SourceProvenance":
        # Every non-manual source should carry a reference back to the
        # original record, or the event can never be traced or re-verified.
        if self.source_type != EventSourceType.MANUAL_ENTRY and self.source_reference is None:
            raise ValueError(
                f"source_reference is required when source_type is '{self.source_type.value}' "
                "(only manual_entry may omit it)."
            )
        return self
