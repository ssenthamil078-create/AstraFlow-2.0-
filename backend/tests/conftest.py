import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import os
os.environ["ASTRAFLOW_EXPOSE_VERIFICATION_TOKEN"] = "true"
os.environ["ASTRAFLOW_ENV"] = "development"

from app.core.database import Base
from app.models import (  # noqa: F401 — ensures the tables are registered on Base.metadata
    document,
    financial_event,
    financial_state_snapshot,
    goal,
    income_payment_observation,
    income_source,
    user,
    verification_token,
)


@pytest.fixture()
def db_session():
    """Fresh in-memory SQLite database per test — no shared state, no
    cleanup needed, and no dependency on the dev sqlite file on disk."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def register_and_login(client, email: str = "test@example.com", password: str = "testpassword123") -> dict:
    """Phase 6 test helper shared by every API-level test file: registers
    a new account against `client`, verifies it using the
    `dev_verification_token` the register response echoes back (see
    services/auth_service.EXPOSE_VERIFICATION_TOKEN — on by default since
    no real SMTP backend exists), logs in, and returns the
    `{"Authorization": "Bearer ..."}` header dict every protected
    endpoint now requires."""
    register_response = client.post("/api/auth/register", json={"email": email, "password": password})
    assert register_response.status_code == 201, register_response.text
    token = register_response.json()["dev_verification_token"]
    assert token, "ASTRAFLOW_EXPOSE_VERIFICATION_TOKEN must be enabled for this test helper to work"

    verify_response = client.post("/api/auth/verify-email", json={"token": token})
    assert verify_response.status_code == 200, verify_response.text

    login_response = client.post("/api/auth/login-json", json={"email": email, "password": password})
    assert login_response.status_code == 200, login_response.text

    access_token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {access_token}"}
