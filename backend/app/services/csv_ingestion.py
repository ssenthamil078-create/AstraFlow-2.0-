"""
Phase 3 — CSV import.

Normalizes bank-statement-style CSV rows into FinancialEventCreate payloads,
runs duplicate detection, and writes each row through the Phase 2 event
ledger service.

Column detection is flexible — accepts any common bank export format.
Each logical field maps from a priority list of known column name aliases.
A malformed row never aborts the whole file.
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Optional

from sqlalchemy.orm import Session

from app.core.vocabulary import Currency, EventDirection, EventSourceType, EventStatus, EventType
from app.schemas.event import FinancialEventCreate
from app.schemas.provenance import SourceProvenance
from app.services import duplicate_detection
from app.services.event_ledger import create_event, list_ledger

# ---------------------------------------------------------------------------
# Flexible column alias maps — checked in priority order (first match wins)
# ---------------------------------------------------------------------------

AMOUNT_ALIASES = [
    "amount", "debit amount", "credit amount", "transaction amount",
    "withdrawal amt (inr)", "deposit amt (inr)", "withdrawal", "deposit",
    "dr", "cr", "txn amount", "value", "amt",
]

DESCRIPTION_ALIASES = [
    "description", "narration", "remarks", "particulars", "details",
    "transaction details", "transaction description", "memo", "note",
    "payee", "merchant", "beneficiary", "transaction remarks", "txn remarks",
    "transaction narration", "accounts", "activity", "source/destination",
]

DATE_ALIASES = [
    "date", "transaction date", "txn date", "value date", "posting date",
    "book date", "trans date", "trade date", "transaction dt", "tran date",
]

TYPE_ALIASES = [
    "type", "txn type", "transaction type", "cr/dr", "dr/cr",
    "debit/credit", "credit/debit", "mode",
]

REFERENCE_ALIASES = [
    "reference", "ref no", "chq/ref no.", "chq no", "cheque no",
    "transaction id", "txn id", "utr no", "utr", "reference number",
    "ref number", "ref", "transaction ref", "wallet txn id",
]

CATEGORY_ALIASES = ["category", "sub-category", "transaction category", "tag"]

BALANCE_ALIASES = [
    "balance", "closing balance", "available balance", "running balance",
    "balance (inr)", "bal",
]

DEBIT_ALIASES = ["debit amount", "withdrawal amt (inr)", "withdrawal", "debit", "dr", "money paid (amount in rs.)", "money paid"]
CREDIT_ALIASES = ["credit amount", "deposit amt (inr)", "deposit", "credit", "cr", "money received (amount in rs.)", "money received"]

CSV_BASE_CONFIDENCE = Decimal("0.90")
CSV_DUPLICATE_CONFIDENCE = Decimal("0.40")

_DATE_FORMATS = (
    "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d",
    "%d %b %Y", "%d %B %Y", "%d-%b-%Y", "%d-%b-%y", "%d/%b/%Y",
    "%d %b %y", "%b %d, %Y", "%B %d, %Y", "%d.%m.%Y", "%d.%m.%y",
)


@dataclass
class CsvRowResult:
    row_number: int
    status: str  # "created" | "rejected"
    event_id: Optional[str] = None
    event_status: Optional[str] = None
    parsed_fields: dict = field(default_factory=dict)
    duplicate_reasons: list[str] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class CsvImportResult:
    total_rows: int
    created_count: int
    rejected_count: int
    flagged_duplicate_count: int
    rows: list[CsvRowResult]


def _find_col(row: dict, aliases: list[str]) -> Optional[str]:
    """Return the first alias key found in `row` (case-insensitive), or None."""
    for alias in aliases:
        if alias in row:
            return row[alias]
    return None


def _parse_amount(raw: str) -> Decimal:
    """Parse amount string — strips currency symbols, commas, parentheses."""
    cleaned = (
        raw.strip()
        .replace(",", "")
        .replace("₹", "")
        .replace("$", "")
        .replace("€", "")
        .replace("£", "")
        .replace("Rs.", "")
        .replace("Rs", "")
        .replace("INR", "")
        .replace(" ", "")
    )
    negative = cleaned.startswith("(") and cleaned.endswith(")")
    if negative:
        cleaned = cleaned[1:-1]
    if not cleaned or cleaned == "-":
        raise InvalidOperation("empty amount")
    value = Decimal(cleaned)
    return -value if negative else value


def _parse_direction(row: dict, signed_amount: Decimal) -> tuple[EventDirection, Decimal]:
    """
    Determine CREDIT/DEBIT from the type column, or debit/credit split columns,
    or fall back to the sign of the amount.
    """
    # 1. Explicit type column
    type_val = (_find_col(row, TYPE_ALIASES) or "").strip().lower()
    if type_val in {"credit", "cr", "income", "deposit", "c"}:
        return EventDirection.CREDIT, abs(signed_amount)
    if type_val in {"debit", "dr", "expense", "withdrawal", "d"}:
        return EventDirection.DEBIT, abs(signed_amount)

    # 2. Separate debit/credit columns (common in HDFC/SBI exports)
    debit_raw = _find_col(row, DEBIT_ALIASES)
    credit_raw = _find_col(row, CREDIT_ALIASES)
    if debit_raw and debit_raw.strip().replace(",", "").replace("₹", "").strip():
        try:
            val = _parse_amount(debit_raw)
            if val != 0:
                return EventDirection.DEBIT, abs(val)
        except InvalidOperation:
            pass
    if credit_raw and credit_raw.strip().replace(",", "").replace("₹", "").strip():
        try:
            val = _parse_amount(credit_raw)
            if val != 0:
                return EventDirection.CREDIT, abs(val)
        except InvalidOperation:
            pass

    # 3. Fall back to sign of amount
    if signed_amount < 0:
        return EventDirection.DEBIT, abs(signed_amount)
    return EventDirection.CREDIT, abs(signed_amount)


def _parse_date(raw: str) -> datetime:
    raw = raw.strip()
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(raw, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    raise ValueError(f"Unrecognized date format: {raw!r}")


def import_csv(
    session: Session,
    user_id: str,
    currency: Currency,
    csv_text: str,
) -> CsvImportResult:
    lines = csv_text.strip().splitlines()
    if not lines:
        raise ValueError("CSV file is empty.")

    # 1. Scan for the header row by looking for known column aliases
    header_row_index = -1
    raw_headers = []
    
    # We'll look for a row that has an amount column
    amount_alias_set = set(AMOUNT_ALIASES + DEBIT_ALIASES + CREDIT_ALIASES)
    
    csv_reader = csv.reader(lines)
    all_rows = list(csv_reader)
    
    for idx, row in enumerate(all_rows):
        normalized_row = [(col or "").strip().lower() for col in row]
        if any(h in normalized_row for h in amount_alias_set):
            header_row_index = idx
            raw_headers = normalized_row
            break

    if header_row_index == -1:
        # Fallback for error reporting: show the first non-empty row they sent
        first_row = [c for c in all_rows[0]] if all_rows else []
        raise ValueError(
            f"CSV is missing required column(s): no amount column found in any row. "
            f"Accepted amount column names: {AMOUNT_ALIASES[:6]}... "
            f"Found first row columns: {first_row}"
        )

    # Now we have the headers, process the remaining rows
    existing_events = list_ledger(session, user_id)
    rows: list[CsvRowResult] = []
    now = datetime.now(timezone.utc)

    # Process rows after the header
    for row_offset, raw_values in enumerate(all_rows[header_row_index + 1:], start=1):
        row_number = header_row_index + 1 + row_offset
        # Map values to the discovered headers
        row: dict[str, str] = {}
        for i, h in enumerate(raw_headers):
            if h:  # skip empty headers
                row[h] = raw_values[i].strip() if i < len(raw_values) else ""

        try:
            # --- Date ---
            date_raw = _find_col(row, DATE_ALIASES)
            if date_raw:
                event_date = _parse_date(date_raw)
            else:
                event_date = now

            # --- Amount ---
            # Try unified amount column first, then split debit/credit columns
            amount_raw = _find_col(row, AMOUNT_ALIASES)
            if amount_raw:
                signed_amount = _parse_amount(amount_raw)
            else:
                # Try to build from split columns
                debit_raw = _find_col(row, DEBIT_ALIASES)
                credit_raw = _find_col(row, CREDIT_ALIASES)
                if debit_raw and debit_raw.strip().replace(",", "").replace("₹", "").strip():
                    signed_amount = -abs(_parse_amount(debit_raw))
                elif credit_raw and credit_raw.strip().replace(",", "").replace("₹", "").strip():
                    signed_amount = abs(_parse_amount(credit_raw))
                else:
                    raise ValueError("No amount value found in this row")

            if signed_amount == 0:
                raise ValueError("Amount is zero — skipped")

            direction, amount = _parse_direction(row, signed_amount)

        except (InvalidOperation, ValueError) as exc:
            rows.append(CsvRowResult(row_number=row_number, status="rejected", error=str(exc)))
            continue

        # Description — optional but used in provenance / event title
        description = (
            _find_col(row, DESCRIPTION_ALIASES)
            or _find_col(row, REFERENCE_ALIASES)
            or f"Row {row_number}"
        )

        matches = duplicate_detection.find_potential_duplicates(
            candidate_amount=amount,
            candidate_direction=direction.value,
            candidate_event_date=event_date,
            existing_events=existing_events,
        )
        flagged = duplicate_detection.has_any_match(matches)
        status = EventStatus.UNCERTAIN if flagged else EventStatus.LIKELY
        confidence = CSV_DUPLICATE_CONFIDENCE if flagged else CSV_BASE_CONFIDENCE

        payload = FinancialEventCreate(
            user_id=user_id,
            event_type=EventType.TRANSACTION,
            direction=direction,
            amount=amount,
            currency=currency,
            event_date=event_date,
            category=_find_col(row, CATEGORY_ALIASES) or None,
            status=status,
            confidence=confidence,
            provenance=SourceProvenance(
                source_type=EventSourceType.CSV_UPLOAD,
                source_reference=_find_col(row, REFERENCE_ALIASES) or f"csv-row-{row_number}",
                ingested_at=now,
                extraction_method="csv-parser",
                raw_excerpt=description[:200],
            ),
        )
        orm_event = create_event(session, payload)
        existing_events.append(orm_event)

        rows.append(
            CsvRowResult(
                row_number=row_number,
                status="created",
                event_id=orm_event.id,
                event_status=orm_event.status,
                parsed_fields={
                    "amount": str(amount),
                    "direction": direction.value,
                    "event_date": event_date.isoformat(),
                    "merchant": description,
                    "category": payload.category,
                },
                duplicate_reasons=[m.reason for m in matches],
            )
        )

    created = [r for r in rows if r.status == "created"]
    return CsvImportResult(
        total_rows=len(rows),
        created_count=len(created),
        rejected_count=len(rows) - len(created),
        flagged_duplicate_count=sum(1 for r in created if r.duplicate_reasons),
        rows=rows,
    )

