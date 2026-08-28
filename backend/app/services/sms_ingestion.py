"""
Phase 3 — SMS input.

Bank SMS text (pasted or uploaded as plain text — one message per list
entry) is parsed with regex heuristics for the common "Rs.X debited/
credited ... at MERCHANT ... on DATE" alert patterns, then normalized into
the same FinancialEventCreate shape every other source uses.

SMS parsing is inherently lower-confidence than a structured CSV row —
free text, dozens of bank-specific templates, easy to misparse a merchant
name — so its base confidence sits below CSV's even before duplicate
detection runs, and any message missing a clean date or merchant is
downgraded to Uncertain rather than guessed into Likely.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.core.vocabulary import Currency, EventDirection, EventSourceType, EventStatus, EventType
from app.schemas.event import FinancialEventCreate
from app.schemas.provenance import SourceProvenance
from app.services import duplicate_detection
from app.services.event_ledger import create_event, list_ledger

SMS_BASE_CONFIDENCE = Decimal("0.65")       # clean parse: amount + direction + date + merchant all found
SMS_LOW_SIGNAL_CONFIDENCE = Decimal("0.35")  # parsed, but date and/or merchant had to be guessed
SMS_DUPLICATE_CONFIDENCE = Decimal("0.30")

_AMOUNT_RE = re.compile(r"(?:Rs\.?|INR|USD|\$|₹)\s*([\d,]+(?:\.\d{1,2})?)", re.IGNORECASE)
_DEBIT_RE = re.compile(r"\b(debited|spent|paid|purchase|withdrawn|sent)\b", re.IGNORECASE)
_CREDIT_RE = re.compile(r"\b(credited|received|deposited|refunded?)\b", re.IGNORECASE)
_DATE_RE = re.compile(r"\b(\d{1,2}[-/][A-Za-z]{3,9}[-/]\d{2,4})\b|\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b|\b(\d{4}-\d{2}-\d{2})\b")
_MERCHANT_RE = re.compile(r"\bat\s+([A-Za-z0-9 &._-]{2,40}?)(?:\s+on\b|\s+ref\b|[.,]|$)", re.IGNORECASE)
_REFERENCE_RE = re.compile(r"\b(?:ref(?:erence)?|txn)\.?\s*(?:no\.?|id)?\s*[:#]?\s*([A-Za-z0-9]{4,20})", re.IGNORECASE)

_DATE_FORMATS = (
    "%d-%m-%y", "%d-%m-%Y", "%d/%m/%y", "%d/%m/%Y", "%Y-%m-%d",
    "%d-%b-%y", "%d-%b-%Y", "%d-%B-%y", "%d-%B-%Y",
)


@dataclass
class SmsParseResult:
    message_number: int
    status: str  # "created" | "rejected"
    event_id: Optional[str] = None
    event_status: Optional[str] = None
    parsed_fields: dict = field(default_factory=dict)
    duplicate_reasons: list[str] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class SmsImportResult:
    total_messages: int
    created_count: int
    rejected_count: int
    rows: list[SmsParseResult]


def _try_parse_date(text: str) -> tuple[Optional[datetime], bool]:
    """Returns (parsed_date, was_guessed). was_guessed=True means no date
    could be parsed at all and the caller should supply a fallback."""
    match = _DATE_RE.search(text)
    if not match:
        return None, True
    raw = next(g for g in match.groups() if g is not None)
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(raw, fmt).replace(tzinfo=timezone.utc), False
        except ValueError:
            continue
    return None, True


def parse_sms_message(text: str, received_at: datetime) -> Optional[dict]:
    """Best-effort extraction. Returns None if the message doesn't look
    like a transaction alert at all (no amount, or no debit/credit
    keyword) — such messages are rejected outright rather than guessed
    into a low-confidence event."""
    amount_match = _AMOUNT_RE.search(text)
    if not amount_match:
        return None

    if _DEBIT_RE.search(text):
        direction = EventDirection.DEBIT
    elif _CREDIT_RE.search(text):
        direction = EventDirection.CREDIT
    else:
        return None

    amount = Decimal(amount_match.group(1).replace(",", ""))
    parsed_date, date_guessed = _try_parse_date(text)
    event_date = parsed_date or received_at

    merchant_match = _MERCHANT_RE.search(text)
    ref_match = _REFERENCE_RE.search(text)

    return {
        "amount": amount,
        "direction": direction,
        "event_date": event_date,
        "merchant": merchant_match.group(1).strip() if merchant_match else None,
        "reference": ref_match.group(1) if ref_match else None,
        "date_was_guessed": date_guessed,
    }


def import_sms_batch(
    session: Session,
    user_id: str,
    currency: Currency,
    messages: list[str],
) -> SmsImportResult:
    existing_events = list_ledger(session, user_id)
    now = datetime.now(timezone.utc)
    rows: list[SmsParseResult] = []

    for idx, raw_text in enumerate(messages, start=1):
        text = raw_text.strip()
        if not text:
            rows.append(SmsParseResult(message_number=idx, status="rejected", error="Empty message."))
            continue

        fields = parse_sms_message(text, received_at=now)
        if fields is None:
            rows.append(
                SmsParseResult(
                    message_number=idx,
                    status="rejected",
                    error="Could not find an amount and a debit/credit keyword in this message.",
                )
            )
            continue

        matches = duplicate_detection.find_potential_duplicates(
            candidate_amount=fields["amount"],
            candidate_direction=fields["direction"].value,
            candidate_event_date=fields["event_date"],
            existing_events=existing_events,
        )
        flagged = duplicate_detection.has_any_match(matches)
        low_signal = fields["date_was_guessed"] or fields["merchant"] is None

        if flagged:
            status, confidence = EventStatus.UNCERTAIN, SMS_DUPLICATE_CONFIDENCE
        elif low_signal:
            status, confidence = EventStatus.UNCERTAIN, SMS_LOW_SIGNAL_CONFIDENCE
        else:
            status, confidence = EventStatus.LIKELY, SMS_BASE_CONFIDENCE

        payload = FinancialEventCreate(
            user_id=user_id,
            event_type=EventType.SMS,
            direction=fields["direction"],
            amount=fields["amount"],
            currency=currency,
            event_date=fields["event_date"],
            category=None,
            status=status,
            confidence=confidence,
            provenance=SourceProvenance(
                source_type=EventSourceType.SMS_TEXT,
                source_reference=fields["reference"] or f"sms-{idx}-{int(now.timestamp())}",
                ingested_at=now,
                extraction_method="regex-sms-parser",
                raw_excerpt=text[:500],
            ),
        )
        orm_event = create_event(session, payload)
        existing_events.append(orm_event)

        rows.append(
            SmsParseResult(
                message_number=idx,
                status="created",
                event_id=orm_event.id,
                event_status=orm_event.status,
                parsed_fields={
                    "amount": str(fields["amount"]),
                    "direction": fields["direction"].value,
                    "event_date": fields["event_date"].isoformat(),
                    "merchant": fields["merchant"],
                    "date_was_guessed": fields["date_was_guessed"],
                },
                duplicate_reasons=[m.reason for m in matches],
            )
        )

    created = [r for r in rows if r.status == "created"]
    return SmsImportResult(
        total_messages=len(rows),
        created_count=len(created),
        rejected_count=len(rows) - len(created),
        rows=rows,
    )
