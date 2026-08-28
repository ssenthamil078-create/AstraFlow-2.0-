"""
Phase 3 — FastAPI request-scoped dependencies.

Wraps Phase 2's SessionLocal (app/core/database.py) in a generator
dependency. Routers are responsible for calling session.commit() on the
success path; if a route raises before that, the session is closed without
committing (SQLAlchemy rolls back on close by default), so a failed
request never leaves a half-written row behind.

Phase 6 — adds `get_current_user`, the Bearer-token dependency every
other router now uses instead of a plain `user_id` query parameter.
`get_current_verified_user` is kept as a separate, stricter dependency
even though login already refuses to issue a token to an unverified
account (see services/auth_service.authenticate_user) — it's a second
line of defense against that policy ever loosening later without every
protected route noticing.
"""

from __future__ import annotations

from typing import Iterator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core import security
from app.core.database import SessionLocal
from app.models.user import UserORM
from app.services.auth_service import get_user_by_id


def get_db() -> Iterator[Session]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


# tokenUrl points at the OAuth2-form login endpoint so Swagger's built-in
# "Authorize" button works out of the box (see api/routers/auth.py).
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_db)) -> UserORM:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        user_id = security.decode_token(token, expected_type="access")
    except security.InvalidTokenError as exc:
        raise credentials_error from exc

    user = get_user_by_id(session, user_id)
    if user is None:
        raise credentials_error
    return user


def get_current_verified_user(current_user: UserORM = Depends(get_current_user)) -> UserORM:
    if not current_user.is_verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email not verified yet.")
    return current_user
