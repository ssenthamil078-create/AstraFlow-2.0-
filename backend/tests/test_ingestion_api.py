import io

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.core.database import Base
from app.main import app
from app.models import document, financial_event, user  # noqa: F401 — register tables
from tests.conftest import register_and_login


@pytest.fixture()
def client():
    # StaticPool is required here (not just check_same_thread=False):
    # FastAPI's TestClient dispatches each request on its own worker
    # thread, and a plain sqlite:///:memory: engine hands each thread a
    # *distinct* empty in-memory database unless every thread shares the
    # same underlying connection.
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def _override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    engine.dispose()


@pytest.fixture()
def auth_headers(client):
    return register_and_login(client)


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_csv_import_endpoint(client, auth_headers):
    csv_content = "date,description,amount,type\n2024-01-05,Salary,50000.00,credit\n2024-01-06,Groceries,1200.00,debit\n"
    response = client.post(
        "/api/import/csv",
        data={"currency": "INR"},
        files={"file": ("statement.csv", io.BytesIO(csv_content.encode()), "text/csv")},
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["created_count"] == 2
    assert body["rejected_count"] == 0


def test_csv_import_requires_auth(client):
    csv_content = "date,description,amount,type\n2024-01-05,Salary,50000.00,credit\n"
    response = client.post(
        "/api/import/csv",
        data={"currency": "INR"},
        files={"file": ("statement.csv", io.BytesIO(csv_content.encode()), "text/csv")},
    )
    assert response.status_code == 401


def test_csv_import_rejects_empty_file(client, auth_headers):
    response = client.post(
        "/api/import/csv",
        data={"currency": "INR"},
        files={"file": ("empty.csv", io.BytesIO(b""), "text/csv")},
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_sms_import_endpoint(client, auth_headers):
    response = client.post(
        "/api/inputs/sms",
        json={
            "currency": "INR",
            "messages": ["Rs.450.00 debited from A/c at SWIGGY on 05-01-2024. Ref No 1234"],
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["created_count"] == 1


def test_full_review_and_confirm_flow(client, auth_headers):
    # 1. Import a CSV row -> lands as Likely.
    csv_content = "date,description,amount,type\n2024-01-05,Salary,50000.00,credit\n"
    import_response = client.post(
        "/api/import/csv",
        data={"currency": "INR"},
        files={"file": ("statement.csv", io.BytesIO(csv_content.encode()), "text/csv")},
        headers=auth_headers,
    )
    event_id = import_response.json()["rows"][0]["event_id"]

    # 2. It shows up in the Likely bucket of the review queue.
    review = client.get("/api/events/review", headers=auth_headers)
    assert review.status_code == 200
    likely_ids = [e["id"] for e in review.json()["likely"]]
    assert event_id in likely_ids

    # 3. Confirm it.
    confirm = client.post(f"/api/events/{event_id}/confirm", headers=auth_headers)
    assert confirm.status_code == 200
    assert confirm.json()["status"] == "confirmed"
    assert float(confirm.json()["confidence"]) == 1.0

    # 4. Confirming again is rejected (one-way transition).
    confirm_again = client.post(f"/api/events/{event_id}/confirm", headers=auth_headers)
    assert confirm_again.status_code == 409

    # 5. It now shows up in the Confirmed bucket.
    review2 = client.get("/api/events/review", headers=auth_headers)
    confirmed_ids = [e["id"] for e in review2.json()["confirmed"]]
    assert event_id in confirmed_ids


def test_confirm_event_404_for_another_users_event(client):
    headers_a = register_and_login(client, email="owner@example.com")
    headers_b = register_and_login(client, email="intruder@example.com")

    csv_content = "date,description,amount,type\n2024-01-05,Salary,50000.00,credit\n"
    import_response = client.post(
        "/api/import/csv",
        data={"currency": "INR"},
        files={"file": ("statement.csv", io.BytesIO(csv_content.encode()), "text/csv")},
        headers=headers_a,
    )
    event_id = import_response.json()["rows"][0]["event_id"]

    confirm = client.post(f"/api/events/{event_id}/confirm", headers=headers_b)
    assert confirm.status_code == 404


def test_merge_duplicate_flow(client, auth_headers):
    csv_content = (
        "date,description,amount,type\n"
        "2024-03-01,Rent,15000.00,debit\n"
        "2024-03-01,Rent,15000.00,debit\n"
    )
    import_response = client.post(
        "/api/import/csv",
        data={"currency": "INR"},
        files={"file": ("statement.csv", io.BytesIO(csv_content.encode()), "text/csv")},
        headers=auth_headers,
    )
    rows = import_response.json()["rows"]
    surviving_id = rows[0]["event_id"]
    duplicate_id = rows[1]["event_id"]
    assert rows[1]["duplicate_reasons"]  # second row was flagged against the first

    merge_response = client.post(
        f"/api/events/{duplicate_id}/merge",
        json={"surviving_event_id": surviving_id, "note": "same rent payment, imported twice"},
        headers=auth_headers,
    )
    assert merge_response.status_code == 200
    assert merge_response.json()["status"] == "rejected"

    events = client.get("/api/events", headers=auth_headers).json()
    active_ids = {e["id"] for e in events}
    # The original duplicate row is superseded and no longer active; the
    # surviving event, and the new REJECTED row, are what remain active.
    assert duplicate_id not in active_ids
    assert surviving_id in active_ids


from tests.test_ocr_ingestion import requires_tesseract
@requires_tesseract
def test_document_upload_and_extracted_data_endpoint(client, auth_headers):
    from PIL import Image, ImageDraw
    from tests.test_ocr_ingestion import _get_test_font

    font = _get_test_font(32)
    image = Image.new("RGB", (700, 260), color="white")
    draw = ImageDraw.Draw(image)
    for i, line in enumerate(["CORNER STORE", "Date: 15-03-2024", "Total: Rs.845.00"]):
        draw.text((20, 20 + i * 60), line, fill="black", font=font)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")

    upload_response = client.post(
        "/api/documents/upload",
        data={"currency": "INR"},
        files={"file": ("receipt.png", buffer.getvalue(), "image/png")},
        headers=auth_headers,
    )
    assert upload_response.status_code == 200
    body = upload_response.json()
    assert body["status"] == "linked"
    assert body["extracted"]["amount"] is not None
    document_id = body["document_id"]
    linked_event_id = body["linked_event_id"]

    fetched = client.get(f"/api/documents/{document_id}/extracted-data", headers=auth_headers)
    assert fetched.status_code == 200
    assert fetched.json()["document_id"] == document_id

    # The linked event must be Uncertain, never auto-confirmed.
    events = client.get("/api/events", headers=auth_headers).json()
    linked_event = next(e for e in events if e["id"] == linked_event_id)
    assert linked_event["status"] == "uncertain"


def test_get_extracted_data_404_for_unknown_document(client, auth_headers):
    response = client.get("/api/documents/does-not-exist/extracted-data", headers=auth_headers)
    assert response.status_code == 404
