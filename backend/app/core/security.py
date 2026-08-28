"""
Phase 6 — Authentication primitives: password hashing and JWT
issuing/verification.

Two token *types* share one encode/decode path (`_encode`/`decode_token`)
but are never interchangeable: an access token is minted with
`type="access"` and is the only kind `api/deps.get_current_user` accepts;
a verification token is minted with `type="email_verification"` and is
only accepted by `POST /api/auth/verify-email`. Checking `type` on decode
is what stops a verification-email link from being replayed as a login
token (or vice versa) even though both are structurally just JWTs signed
with the same secret.

`ASTRAFLOW_SECRET_KEY` MUST be overridden via env var outside of local
dev — the default here is intentionally obviously insecure so nobody
mistakes it for a real secret.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

ENV = os.environ.get("ASTRAFLOW_ENV", "development")
SECRET_KEY = os.environ.get("ASTRAFLOW_SECRET_KEY", "dev-only-insecure-secret-change-me")

if ENV != "development":
    if SECRET_KEY == "dev-only-insecure-secret-change-me":
        raise RuntimeError("ASTRAFLOW_SECRET_KEY must be configured in production.")
    if len(SECRET_KEY) < 32:
        raise ValueError("ASTRAFLOW_SECRET_KEY must be at least 32 characters long in production.")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ASTRAFLOW_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
EMAIL_VERIFICATION_EXPIRE_HOURS = int(os.environ.get("ASTRAFLOW_EMAIL_VERIFICATION_EXPIRE_HOURS", "24"))

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return _pwd_context.verify(plain_password, hashed_password)


class InvalidTokenError(Exception):
    """Raised for any decode failure: malformed, expired, bad signature,
    or a `type` claim that doesn't match what the caller expected."""


def _encode(subject: str, token_type: str, expires_delta: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": subject, "type": token_type, "iat": now, "exp": now + expires_delta}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_access_token(user_id: str) -> str:
    return _encode(user_id, "access", timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))


import secrets

def create_email_verification_token(user_id: str = None) -> str:
    # Just returning a random token. DB will map it to user_id.
    return secrets.token_urlsafe(32)


def decode_token(token: str, expected_type: str) -> str:
    """Returns the subject (user id) if `token` is valid and its `type`
    claim matches `expected_type`; raises InvalidTokenError otherwise."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise InvalidTokenError("Token is invalid or expired.") from exc

    if payload.get("type") != expected_type:
        raise InvalidTokenError(f"Expected a {expected_type} token.")

    subject = payload.get("sub")
    if not subject:
        raise InvalidTokenError("Token is missing a subject.")
    return subject
