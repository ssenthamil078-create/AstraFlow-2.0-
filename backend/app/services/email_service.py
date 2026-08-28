"""
Phase 6 — Outbound email for auth flows.

The hackathon build has no SMTP/SES credentials wired up, so the only
backend implemented is "console": it logs the link instead of sending
it. Everything upstream (auth_service.py, api/routers/auth.py) only ever
calls `send_verification_email` — swapping in a real provider later is a
one-function change, nothing else needs to know which backend is active.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger("astraflow.email")

EMAIL_BACKEND = os.environ.get("ASTRAFLOW_EMAIL_BACKEND", "console")
FRONTEND_BASE_URL = os.environ.get("ASTRAFLOW_FRONTEND_BASE_URL", "http://localhost:3000")


def send_verification_email(to_email: str, token: str) -> None:
    verify_link = f"{FRONTEND_BASE_URL}/verify-email?token={token}"
    if EMAIL_BACKEND == "console":
        logger.info("Verification email for %s: %s", to_email, verify_link)
    else:  # pragma: no cover - no other backend wired up yet
        raise NotImplementedError(f"Unknown ASTRAFLOW_EMAIL_BACKEND={EMAIL_BACKEND!r}")
