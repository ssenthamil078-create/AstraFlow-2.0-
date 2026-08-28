"""
Phase 6 — Registration, login, and email-verification service logic.

Scope note: `users.id` is deliberately NOT added as a foreign key on
financial_events.user_id / income_sources.user_id / goals.user_id /
documents.user_id. Those columns predate this table (Phases 2-5) and stay
plain strings for now — wiring a real FK plus a backfill migration for
existing rows is deferred to when the project adopts Alembic (roadmap
Phase 11, same deferral noted in core/database.py's init_db()). Until
then, `api/deps.get_current_user` is the one place that guarantees a
`user_id` used in a request actually corresponds to a real, authenticated
account going forward.
"""

from __future__ import annotations

import os
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from app.core import security
from app.models.user import UserORM
from app.models.verification_token import VerificationTokenORM
from app.services import email_service
from datetime import timedelta, datetime, timezone

# Hackathon/local-dev convenience: since no real SMTP is wired up (see
# email_service.py), the register/resend-verification endpoints can echo
# the verification token back in the JSON response so the flow is
# testable end to end without an inbox. Set this to "false" the moment
# real email delivery exists — leaking the token defeats the point of
# verification.
ENV = os.environ.get("ASTRAFLOW_ENV", "development")
EXPOSE_VERIFICATION_TOKEN = os.environ.get("ASTRAFLOW_EXPOSE_VERIFICATION_TOKEN", "false").lower() == "true"

if ENV != "development" and EXPOSE_VERIFICATION_TOKEN:
    raise RuntimeError("ASTRAFLOW_EXPOSE_VERIFICATION_TOKEN cannot be true in non-development environments.")


class EmailAlreadyRegisteredError(Exception):
    """Raised on registration when the email is already taken."""


class InvalidCredentialsError(Exception):
    """Raised on login when the email/password pair doesn't match."""


class EmailNotVerifiedError(Exception):
    """Raised on login when the account exists but hasn't verified its email yet."""


def get_user_by_email(session: Session, email: str) -> Optional[UserORM]:
    return session.query(UserORM).filter(UserORM.email == email.strip().casefold()).one_or_none()


def get_user_by_id(session: Session, user_id: str) -> Optional[UserORM]:
    return session.get(UserORM, user_id)


def register_user(session: Session, email: str, password: str) -> Tuple[UserORM, Optional[str]]:
    """Creates the account (unverified) and sends the verification email.
    Returns (user, dev_verification_token) — the second element is only
    non-None when EXPOSE_VERIFICATION_TOKEN is on."""
    from sqlalchemy.exc import IntegrityError
    
    normalized_email = email.strip().casefold()
    if get_user_by_email(session, normalized_email) is not None:
        raise EmailAlreadyRegisteredError(f"{email} is already registered.")

    user = UserORM(
        email=normalized_email,
        hashed_password=security.hash_password(password),
        is_verified=False,
    )
    session.add(user)
    
    try:
        session.flush()  # populate user.id before it's needed for the token
    except IntegrityError:
        session.rollback()
        raise EmailAlreadyRegisteredError(f"{email} is already registered.")

    token = security.create_email_verification_token()
    vt = VerificationTokenORM(
        token=token,
        user_id=user.id,
        purpose="email_verification",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=security.EMAIL_VERIFICATION_EXPIRE_HOURS)
    )
    session.add(vt)
    
    email_service.send_verification_email(user.email, token)

    return user, (token if EXPOSE_VERIFICATION_TOKEN else None)


def authenticate_user(session: Session, email: str, password: str) -> UserORM:
    user = get_user_by_email(session, email)
    if user is None or not security.verify_password(password, user.hashed_password):
        raise InvalidCredentialsError("Incorrect email or password.")
    if not user.is_verified:
        raise EmailNotVerifiedError("Email not verified yet. Check your inbox for the verification link.")
    return user


def verify_email(session: Session, token: str) -> UserORM:
    vt = session.query(VerificationTokenORM).filter_by(token=token, purpose="email_verification").with_for_update().first()
    if not vt:
        raise LookupError("Invalid verification token.")
    if vt.used_at:
        raise LookupError("Verification token has already been used.")
    if vt.revoked_at:
        raise LookupError("Verification token has been revoked.")
    if vt.expires_at < datetime.now(timezone.utc):
        raise LookupError("Verification token has expired.")
    
    user = get_user_by_id(session, vt.user_id)
    if user is None:
        raise LookupError("No account matches this verification token.")
    
    vt.used_at = datetime.now(timezone.utc)
    user.is_verified = True
    session.add(vt)
    session.add(user)
    return user


def resend_verification(session: Session, email: str) -> Optional[str]:
    """Silently no-ops if there's no matching unverified account, so this
    endpoint can't be used to probe which emails are registered. Returns
    the dev token under the same EXPOSE_VERIFICATION_TOKEN gate as
    register_user."""
    user = get_user_by_email(session, email)
    if user is None or user.is_verified:
        return None
        
    # Revoke previous tokens
    session.query(VerificationTokenORM).filter_by(user_id=user.id, purpose="email_verification", revoked_at=None, used_at=None).update({"revoked_at": datetime.now(timezone.utc)})
    
    token = security.create_email_verification_token()
    vt = VerificationTokenORM(
        token=token,
        user_id=user.id,
        purpose="email_verification",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=security.EMAIL_VERIFICATION_EXPIRE_HOURS)
    )
    session.add(vt)
    email_service.send_verification_email(user.email, token)
    return token if EXPOSE_VERIFICATION_TOKEN else None
