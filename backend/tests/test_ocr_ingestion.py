import io

import pytest

from app.core.vocabulary import Currency, EventSourceType, EventStatus
from app.services import ocr_ingestion
from app.services.event_ledger import list_ledger


def _get_test_font(size: int):
    """A TrueType font at a receipt-sized point size, resolved
    cross-platform. Tries common system font locations first (nicer
    anti-aliasing); falls back to Pillow's built-in scalable default font
    (`load_default(size=...)`, available from Pillow 9.2+) so the test
    doesn't depend on any particular OS having a specific font installed."""
    from PIL import ImageFont

    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # common on Linux
        "C:\\Windows\\Fonts\\arial.ttf",                          # Windows
        "C:\\Windows\\Fonts\\calibrib.ttf",                       # Windows fallback
        "/Library/Fonts/Arial.ttf",                               # macOS
        "/System/Library/Fonts/Supplemental/Arial.ttf",           # macOS
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default(size=size)


def _make_receipt_image_bytes() -> bytes:
    """Renders a simple synthetic receipt as a PNG so the test doesn't
    depend on a fixture file, and runs against the real local Tesseract
    binary (no mocking) to exercise the actual OCR pipeline."""
    from PIL import Image, ImageDraw

    font = _get_test_font(32)

    image = Image.new("RGB", (700, 320), color="white")
    draw = ImageDraw.Draw(image)
    lines = [
        "CORNER STORE",
        "Date: 15-03-2024",
        "Item: Groceries",
        "Total: Rs.845.00",
    ]
    y = 20
    for line in lines:
        draw.text((20, y), line, fill="black", font=font)
        y += 60

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


import shutil

def has_tesseract():
    return shutil.which("tesseract") is not None

requires_tesseract = pytest.mark.skipif(not has_tesseract(), reason="Tesseract is not installed")

@requires_tesseract
def test_extract_fields_finds_amount_and_date_from_receipt():
    image_bytes = _make_receipt_image_bytes()
    extraction = ocr_ingestion.extract_fields(image_bytes, content_type="image/png")


    assert extraction.error is None
    assert extraction.amount == pytest.approx(845.00)
    assert extraction.event_date is not None
    assert extraction.event_date.year == 2024
    assert extraction.event_date.month == 3
    assert extraction.event_date.day == 15


@requires_tesseract
def test_extract_fields_reports_error_on_blank_image():
    from PIL import Image

    blank = Image.new("RGB", (200, 100), color="white")
    buffer = io.BytesIO()
    blank.save(buffer, format="PNG")

    extraction = ocr_ingestion.extract_fields(buffer.getvalue(), content_type="image/png")
    assert extraction.amount is None
    assert extraction.error is not None


@requires_tesseract
def test_upload_and_process_document_creates_uncertain_event_never_confirmed(db_session):
    image_bytes = _make_receipt_image_bytes()
    document = ocr_ingestion.upload_and_process_document(
        db_session,
        user_id="ocr-user-1",
        currency=Currency.INR,
        filename="receipt.png",
        content_type="image/png",
        file_bytes=image_bytes,
    )
    db_session.commit()

    assert document.status == "linked"
    assert document.linked_event_id is not None

    ledger = list_ledger(db_session, "ocr-user-1")
    assert len(ledger) == 1
    event = ledger[0]

    # Definition-of-done check: OCR output is NEVER auto-confirmed, no
    # matter how clean the extraction looked.
    assert event.status == EventStatus.UNCERTAIN.value
    assert event.confidence < 1
    assert event.source_type == EventSourceType.OCR_DOCUMENT.value


@requires_tesseract
def test_upload_and_process_document_extraction_failure_creates_no_event(db_session):
    from PIL import Image

    blank = Image.new("RGB", (200, 100), color="white")
    buffer = io.BytesIO()
    blank.save(buffer, format="PNG")

    document = ocr_ingestion.upload_and_process_document(
        db_session,
        user_id="ocr-user-2",
        currency=Currency.INR,
        filename="blank.png",
        content_type="image/png",
        file_bytes=buffer.getvalue(),
    )
    db_session.commit()

    assert document.status == "extraction_failed"
    assert document.linked_event_id is None
    assert list_ledger(db_session, "ocr-user-2") == []


@requires_tesseract
def test_document_to_response_shape():
    image_bytes = _make_receipt_image_bytes()
    extraction = ocr_ingestion.extract_fields(image_bytes, content_type="image/png")
    assert extraction.amount is not None  # sanity check for the fixture image itself
