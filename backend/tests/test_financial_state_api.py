import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.core.database import Base
from app.main import app
from app.models import document, financial_event, financial_state_snapshot, goal, user  # noqa: F401
from tests.conftest import register_and_login


@pytest.fixture()
def client():
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


def _import_csv(client, headers):
    from datetime import datetime, timedelta
    now = datetime.now()
    d1 = (now - timedelta(days=9)).strftime("%Y-%m-%d")
    d2 = (now - timedelta(days=5)).strftime("%Y-%m-%d")
    d3 = (now - timedelta(days=4)).strftime("%Y-%m-%d")
    d4 = (now - timedelta(days=3)).strftime("%Y-%m-%d")
    csv_content = (
        f"date,description,amount,type\n"
        f"{d1},Salary,50000.00,credit\n"
        f"{d2},Monthly rent payment to landlord,20000.00,debit\n"
        f"{d3},Netflix subscription renewal,500.00,debit\n"
        f"{d4},Amazon purchase,1200.00,debit\n"
    )
    response = client.post(
        "/api/import/csv",
        data={"currency": "INR"},
        files={"file": ("statement.csv", csv_content.encode(), "text/csv")},
        headers=headers,
    )
    assert response.status_code == 200
    return response.json()


def _confirm_all(client, headers):
    events = client.get("/api/events", headers=headers).json()
    for e in events:
        client.post(f"/api/events/{e['id']}/confirm", headers=headers)


def test_health_reports_current_phase(client):
    # Bumped to 6 when the auth router was added — see app/main.py. Each
    # phase updates this same assertion rather than leaving a stale
    # phase number behind.
    response = client.get("/health")
    assert response.json() == {"status": "ok", "phase": 6}


def test_endpoints_require_auth(client):
    assert client.get("/api/financial-state", params={"currency": "INR"}).status_code == 401
    assert client.get("/api/events").status_code == 401


def test_get_financial_state_before_rebuild_has_no_obligations_yet(client, auth_headers):
    _import_csv(client, auth_headers)
    response = client.get("/api/financial-state", params={"currency": "INR"}, headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    # GET never classifies — rent/subscription events are still uncategorized.
    assert body["obligations"] == []


def test_rebuild_classifies_and_persists_snapshot(client, auth_headers):
    _import_csv(client, auth_headers)
    _confirm_all(client, auth_headers)

    response = client.post("/api/financial-state/rebuild", params={"currency": "INR"}, headers=auth_headers)
    assert response.status_code == 200
    body = response.json()

    assert body["confirmed_balance"] == "28300.00" or float(body["confirmed_balance"]) == 28300.00
    categories = {o["category"] for o in body["obligations"]}
    assert "rent" in categories
    assert "utilities" in categories  # Netflix subscription
    assert body["discretionary_spending"]["event_count"] == 1  # Amazon purchase


def test_rebuild_is_idempotent_across_two_calls(client, auth_headers):
    _import_csv(client, auth_headers)
    _confirm_all(client, auth_headers)

    first = client.post(
        "/api/financial-state/rebuild", params={"currency": "INR"}, headers=auth_headers
    ).json()
    second = client.post(
        "/api/financial-state/rebuild", params={"currency": "INR"}, headers=auth_headers
    ).json()

    assert len(first["obligations"]) == len(second["obligations"])
    assert first["discretionary_spending"]["total"] == second["discretionary_spending"]["total"]


def test_timeline_records_each_rebuild(client, auth_headers):
    _import_csv(client, auth_headers)
    _confirm_all(client, auth_headers)

    client.post("/api/financial-state/rebuild", params={"currency": "INR"}, headers=auth_headers)
    client.post("/api/financial-state/rebuild", params={"currency": "INR"}, headers=auth_headers)

    response = client.get("/api/financial-state/timeline", params={"currency": "INR"}, headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_provenance_links_confirmed_balance_to_events(client, auth_headers):
    _import_csv(client, auth_headers)
    _confirm_all(client, auth_headers)
    client.post("/api/financial-state/rebuild", params={"currency": "INR"}, headers=auth_headers)

    response = client.get("/api/financial-state/provenance", params={"currency": "INR"}, headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert len(body["confirmed_balance_events"]) == 4  # all 4 rows were confirmed
    assert any("rent" in key for key in body["obligations"])


def test_goal_crud_and_progress_via_financial_state(client, auth_headers):
    _import_csv(client, auth_headers)
    _confirm_all(client, auth_headers)

    create_response = client.post(
        "/api/goals",
        json={
            "name": "Emergency fund",
            "goal_type": "savings_target",
            "currency": "INR",
            "linked_category": "emergency_savings",
            "target_amount": "10000",
        },
        headers=auth_headers,
    )
    assert create_response.status_code == 200
    goal_id = create_response.json()["id"]

    list_response = client.get("/api/goals", headers=auth_headers)
    assert len(list_response.json()) == 1

    update_response = client.patch(
        f"/api/goals/{goal_id}", json={"target_amount": "20000"}, headers=auth_headers
    )
    assert update_response.status_code == 200
    assert update_response.json()["target_amount"] == "20000.00" or float(
        update_response.json()["target_amount"]
    ) == 20000.0

    state_response = client.get("/api/financial-state", params={"currency": "INR"}, headers=auth_headers)
    goal_entries = state_response.json()["goals"]
    assert len(goal_entries) == 1
    assert goal_entries[0]["goal_id"] == goal_id


def test_data_is_isolated_between_users(client):
    headers_a = register_and_login(client, email="user-a@example.com")
    headers_b = register_and_login(client, email="user-b@example.com")

    _import_csv(client, headers_a)

    assert len(client.get("/api/events", headers=headers_a).json()) == 4
    assert len(client.get("/api/events", headers=headers_b).json()) == 0
