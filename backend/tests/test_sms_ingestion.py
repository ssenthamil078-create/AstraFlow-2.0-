from decimal import Decimal

from app.core.vocabulary import Currency, EventStatus
from app.services.sms_ingestion import import_sms_batch, parse_sms_message


def test_parse_clean_debit_message():
    text = "Rs.450.00 debited from A/c XX1234 at SWIGGY on 05-01-2024. Ref No 12345678"
    fields = parse_sms_message(text, received_at=None)
    assert fields is not None
    assert fields["amount"] == Decimal("450.00")
    assert fields["direction"].value == "debit"
    assert fields["merchant"] is not None
    assert fields["date_was_guessed"] is False


def test_parse_credit_message():
    text = "INR 50,000.00 credited to your account on 2024-01-05. Ref TXN9988"
    fields = parse_sms_message(text, received_at=None)
    assert fields is not None
    assert fields["amount"] == Decimal("50000.00")
    assert fields["direction"].value == "credit"


def test_parse_returns_none_for_non_transaction_text():
    fields = parse_sms_message("Your OTP is 445566. Do not share it with anyone.", received_at=None)
    assert fields is None


def test_import_sms_batch_creates_events(db_session):
    messages = [
        "Rs.450.00 debited from A/c XX1234 at SWIGGY on 05-01-2024. Ref No 12345678",
        "INR 50,000.00 credited to your account on 2024-01-05. Ref TXN9988",
    ]
    result = import_sms_batch(db_session, user_id="s1", currency=Currency.INR, messages=messages)
    db_session.commit()

    assert result.total_messages == 2
    assert result.created_count == 2
    assert result.rejected_count == 0


def test_import_sms_batch_rejects_unparseable_message(db_session):
    messages = ["Hey, are we still meeting for lunch today?"]
    result = import_sms_batch(db_session, user_id="s2", currency=Currency.INR, messages=messages)
    db_session.commit()

    assert result.created_count == 0
    assert result.rejected_count == 1
    assert "amount" in result.rows[0].error.lower()


def test_import_sms_batch_low_signal_message_marked_uncertain(db_session):
    # No date, no "at MERCHANT" — should parse but land as UNCERTAIN, not LIKELY.
    messages = ["Rs.99.00 debited from your account."]
    result = import_sms_batch(db_session, user_id="s3", currency=Currency.INR, messages=messages)
    db_session.commit()

    assert result.created_count == 1
    assert result.rows[0].event_status == EventStatus.UNCERTAIN.value


def test_import_sms_batch_flags_duplicate(db_session):
    messages = [
        "Rs.300.00 debited from A/c at CAFE on 01-02-2024. Ref REF001",
        "Rs.300.00 debited from A/c at CAFE on 01-02-2024. Ref REF002",
    ]
    result = import_sms_batch(db_session, user_id="s4", currency=Currency.INR, messages=messages)
    db_session.commit()

    statuses = [r.event_status for r in result.rows]
    assert statuses.count(EventStatus.UNCERTAIN.value) >= 1
