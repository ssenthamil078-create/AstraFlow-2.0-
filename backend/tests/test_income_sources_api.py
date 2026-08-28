import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.core.database import Base
from app.main import app
from app.models import (  # noqa: F401
    document,
    financial_event,
    financial_state_snapshot,
    goal,
    income_payment_observation,
    income_source,
    user,
)
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


def _create_source(client, headers, **overrides):
    payload = dict(
        name="Client A",
        category="freelance_client",
        currency="INR",
        typical_amount="20000",
    )
    payload.update(overrides)
    response = client.post("/api/income-sources", json=payload, headers=headers)
    assert response.status_code == 200
    return response.json()


def test_create_and_list_income_sources(client, auth_headers):
    _create_source(client, auth_headers)
    response = client.get("/api/income-sources", headers=auth_headers)
    assert response.status_code == 200
    sources = response.json()
    assert len(sources) == 1
    assert sources[0]["name"] == "Client A"
    assert sources[0]["cached_reliability_score"] is None


def test_reliability_with_no_observations_returns_category_default(client, auth_headers):
    source = _create_source(client, auth_headers)
    response = client.get(f"/api/income-sources/{source['id']}/reliability", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["observation_count"] == 0
    assert body["is_provisional"] is True
    assert float(body["reliability_score"]) == pytest.approx(0.55)


def test_record_observation_and_recalculate(client, auth_headers):
    source = _create_source(client, auth_headers)
    for _ in range(10):
        obs_response = client.post(
            f"/api/income-sources/{source['id']}/observations",
            json={
                "was_received": True,
                "expected_date": "2026-01-01T00:00:00Z",
                "actual_date": "2026-01-01T00:00:00Z",
                "expected_amount": "20000",
                "actual_amount": "20000",
                "source_type": "bank_feed",
            },
            headers=auth_headers,
        )
        assert obs_response.status_code == 200

    reliability = client.get(f"/api/income-sources/{source['id']}/reliability", headers=auth_headers).json()
    assert reliability["observation_count"] == 10
    assert reliability["is_provisional"] is False
    assert float(reliability["reliability_score"]) == pytest.approx(1.0)

    recalculated = client.post(f"/api/income-sources/{source['id']}/recalculate", headers=auth_headers)
    assert recalculated.status_code == 200

    refreshed = client.get("/api/income-sources", headers=auth_headers).json()
    assert float(refreshed[0]["cached_reliability_score"]) == pytest.approx(1.0)
    assert refreshed[0]["cached_observation_count"] == 10


def test_missed_observation_requires_no_actuals(client, auth_headers):
    source = _create_source(client, auth_headers)
    response = client.post(
        f"/api/income-sources/{source['id']}/observations",
        json={
            "was_received": False,
            "expected_date": "2026-01-01T00:00:00Z",
            "expected_amount": "20000",
            "source_type": "sms_text",
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["actual_amount"] is None


def test_reliability_for_unknown_source_is_404(client, auth_headers):
    response = client.get("/api/income-sources/does-not-exist/reliability", headers=auth_headers)
    assert response.status_code == 404


def test_income_source_404_for_another_users_source(client):
    headers_a = register_and_login(client, email="owner@example.com")
    headers_b = register_and_login(client, email="intruder@example.com")

    source = _create_source(client, headers_a)
    response = client.get(f"/api/income-sources/{source['id']}/reliability", headers=headers_b)
    assert response.status_code == 404


def test_income_sources_require_auth(client):
    response = client.get("/api/income-sources")
    assert response.status_code == 401


def test_health_reports_phase_6(client):
    response = client.get("/health")
    assert response.json() == {"status": "ok", "phase": 6}
