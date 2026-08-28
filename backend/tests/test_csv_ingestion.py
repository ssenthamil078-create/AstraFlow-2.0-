import pytest

from app.core.vocabulary import Currency, EventStatus
from app.services.csv_ingestion import import_csv
from app.services.event_ledger import list_ledger

VALID_CSV = """date,description,amount,type,reference
2024-01-05,Salary,50000.00,credit,SAL-JAN
2024-01-06,Groceries,1200.50,debit,POS-1
2024-01-10,Electricity Bill,850.00,debit,BILL-1
"""


def test_import_csv_creates_events_at_likely_status(db_session):
    result = import_csv(db_session, user_id="u1", currency=Currency.INR, csv_text=VALID_CSV)
    db_session.commit()

    assert result.total_rows == 3
    assert result.created_count == 3
    assert result.rejected_count == 0
    assert result.flagged_duplicate_count == 0
    assert all(r.event_status == EventStatus.LIKELY.value for r in result.rows)

    ledger = list_ledger(db_session, "u1")
    assert len(ledger) == 3


def test_import_csv_infers_direction_from_negative_amount(db_session):
    csv_text = "date,description,amount\n2024-02-01,ATM Withdrawal,-2000.00\n2024-02-02,Refund,500.00\n"
    result = import_csv(db_session, user_id="u2", currency=Currency.INR, csv_text=csv_text)
    db_session.commit()

    ledger = list_ledger(db_session, "u2")
    directions = {e.amount: e.direction for e in ledger}
    assert directions[2000] == "debit"
    assert directions[500] == "credit"


def test_import_csv_flags_duplicate_row(db_session):
    csv_text = (
        "date,description,amount,type\n"
        "2024-03-01,Rent,15000.00,debit\n"
        "2024-03-01,Rent,15000.00,debit\n"
    )
    result = import_csv(db_session, user_id="u3", currency=Currency.INR, csv_text=csv_text)
    db_session.commit()

    assert result.created_count == 2
    assert result.flagged_duplicate_count == 1
    statuses = [r.event_status for r in result.rows]
    assert statuses.count(EventStatus.LIKELY.value) == 1
    assert statuses.count(EventStatus.UNCERTAIN.value) == 1


def test_import_csv_rejects_bad_rows_without_aborting_file(db_session):
    csv_text = (
        "date,description,amount,type\n"
        "not-a-date,Bad Row,100.00,debit\n"
        "2024-04-01,Good Row,250.00,debit\n"
    )
    result = import_csv(db_session, user_id="u4", currency=Currency.INR, csv_text=csv_text)
    db_session.commit()

    assert result.total_rows == 2
    assert result.created_count == 1
    assert result.rejected_count == 1
    rejected = [r for r in result.rows if r.status == "rejected"][0]
    assert "date" in rejected.error.lower() or "unrecognized" in rejected.error.lower()


def test_import_csv_requires_required_columns(db_session):
    with pytest.raises(ValueError, match="missing required column"):
        import_csv(db_session, user_id="u5", currency=Currency.INR, csv_text="foo,bar\n1,2\n")


def test_import_csv_no_header_raises(db_session):
    with pytest.raises(ValueError):
        import_csv(db_session, user_id="u6", currency=Currency.INR, csv_text="")
