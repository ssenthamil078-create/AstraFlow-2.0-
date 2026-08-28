"""
Phase 3 — Ingestion API contracts not already covered by schemas/event.py.

CSV and document upload go through multipart form fields (see
api/routers/ingestion.py), so they don't need a request body schema here —
only SMS input (JSON body of raw message strings) and the merge action do.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from app.core.vocabulary import Currency


class SmsImportRequest(BaseModel):
    """Body for POST /api/inputs/sms. `messages` is a list so a whole
    pasted SMS export (or a batch forwarded from an Android SMS-reader
    shortcut) can be ingested in one call.

    Phase 6: no `user_id` field — the ingesting user is always the
    authenticated caller (see api/routers/ingestion.py)."""

    currency: Currency
    messages: list[str] = Field(..., min_length=1, description="One raw SMS text per entry.")


class MergeEventsRequest(BaseModel):
    """Body for POST /api/events/{event_id}/merge. `{event_id}` in the
    path is the duplicate being resolved; `surviving_event_id` is the one
    that stays active. The path event is superseded with
    CorrectionReason.DUPLICATE_RESOLVED and status REJECTED — the
    surviving event is never modified."""

    surviving_event_id: str = Field(..., min_length=1)
    note: Optional[str] = Field(default=None, max_length=500)
