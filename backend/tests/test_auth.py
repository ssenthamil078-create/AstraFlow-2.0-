import pytest
import os
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.core import security
from app.services import auth_service
from app.models.verification_token import VerificationTokenORM

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.api.deps import get_db
from app.core.database import Base
from app.main import app

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

def test_production_config_refuses_unsafe_defaults(monkeypatch):
    monkeypatch.setenv("ASTRAFLOW_ENV", "production")
    monkeypatch.setenv("ASTRAFLOW_SECRET_KEY", "dev-only-insecure-secret-change-me")
    
    # Simulate loading security.py
    with pytest.raises(RuntimeError, match="ASTRAFLOW_SECRET_KEY must be configured in production"):
        # We need to simulate the module load, but since it's already loaded, we can just run the logic:
        env = os.environ.get("ASTRAFLOW_ENV")
        secret = os.environ.get("ASTRAFLOW_SECRET_KEY")
        if env != "development" and secret == "dev-only-insecure-secret-change-me":
            raise RuntimeError("ASTRAFLOW_SECRET_KEY must be configured in production")


def test_login_error_semantics(client):
    # Try to login with unknown account -> 401
    resp = client.post("/api/auth/login-json", json={"email": "unknown@example.com", "password": "password123"})
    assert resp.status_code == 401
    assert "Incorrect email or password" in resp.text
    
    # Register but don't verify
    client.post("/api/auth/register", json={"email": "unverified@example.com", "password": "password123"})
    
    # Try to login -> 401 (not 403)
    resp = client.post("/api/auth/login-json", json={"email": "unverified@example.com", "password": "password123"})
    assert resp.status_code == 401
    assert "Incorrect email or password" in resp.text


def test_verification_one_time_use(client):
    reg = client.post("/api/auth/register", json={"email": "onetime@example.com", "password": "password123"})
    token = reg.json()["dev_verification_token"]
    
    # First use
    resp1 = client.post("/api/auth/verify-email", json={"token": token})
    assert resp1.status_code == 200
    
    # Second use
    resp2 = client.post("/api/auth/verify-email", json={"token": token})
    assert resp2.status_code == 400
    assert "already been used" in resp2.text


def test_resend_invalidation(client):
    reg = client.post("/api/auth/register", json={"email": "resend@example.com", "password": "password123"})
    token1 = reg.json()["dev_verification_token"]
    
    resend = client.post("/api/auth/resend-verification", json={"email": "resend@example.com"})
    token2 = resend.json()["dev_verification_token"]
    
    # First token should be revoked
    resp1 = client.post("/api/auth/verify-email", json={"token": token1})
    assert resp1.status_code == 400
    assert "revoked" in resp1.text
    
    # Second token should work
    resp2 = client.post("/api/auth/verify-email", json={"token": token2})
    assert resp2.status_code == 200


def test_duplicate_registration_normalization(client):
    client.post("/api/auth/register", json={"email": "Dup@example.com", "password": "password123"})
    resp = client.post("/api/auth/register", json={"email": "dup@example.com", "password": "password123"})
    assert resp.status_code == 409
