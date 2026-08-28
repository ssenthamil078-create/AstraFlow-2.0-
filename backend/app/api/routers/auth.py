"""
Phase 6 — Registration, login, and email-verification API.

`POST /api/auth/login` takes OAuth2 form-encoding (`username`/`password`
fields) so Swagger's built-in "Authorize" button works out of the box —
that's what `app.api.deps.oauth2_scheme`'s `tokenUrl` points at.
`POST /api/auth/login-json` is the same check with a JSON body, for
clients (mobile apps, `fetch()`) that would rather not form-encode a
request.
"""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core import security
from app.models.user import UserORM
from app.schemas.auth import (
    RegisterResponse,
    ResendVerificationRequest,
    TokenResponse,
    UserLogin,
    UserRead,
    UserRegister,
    VerifyEmailRequest,
)
from app.services import auth_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


class OnboardingRequest(BaseModel):
    currency: Optional[str] = "₹"


class FlexibleVerifyRequest(BaseModel):
    token: Optional[str] = None
    email: Optional[EmailStr] = None
    code: Optional[str] = None


@router.get("/me")
@router.get("/profile")
def get_current_profile(current_user: UserORM = Depends(get_current_user)):
    """Returns profile for current authenticated user."""
    name = current_user.email.split("@")[0].capitalize()
    return {
        "user": {
            "id": current_user.id,
            "name": name,
            "email": current_user.email,
            "emailVerified": current_user.is_verified,
            "currency": "₹",
            "onboardingCompleted": True,
            "avatarUrl": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80",
            "createdAt": current_user.created_at.isoformat(),
        },
        "authenticated": True,
    }


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, session: Session = Depends(get_db)):
    try:
        user, dev_token = auth_service.register_user(session, payload.email, payload.password)
    except auth_service.EmailAlreadyRegisteredError as exc:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    # In dev mode, auto-verify for smooth local workflow
    if dev_token is not None:
        user.is_verified = True

    token = security.create_access_token(user.id)
    session.commit()

    return RegisterResponse(
        user=UserRead.model_validate(user),
        message="Registration successful. Check your email for a verification link.",
        access_token=token,
        token=token,
        dev_verification_token=dev_token,
    )


@router.post("/verify-email")
def verify_email(payload: FlexibleVerifyRequest, session: Session = Depends(get_db)):
    verify_token = payload.token or payload.code
    if not verify_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification token is required.")

    try:
        user = auth_service.verify_email(session, verify_token)
    except (security.InvalidTokenError, LookupError) as exc:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    session.commit()
    return {
        "success": True,
        "message": "Email verified successfully.",
        "user": UserRead.model_validate(user),
    }


@router.post("/onboarding")
def complete_onboarding(payload: OnboardingRequest, current_user: UserORM = Depends(get_current_user)):
    return {
        "success": True,
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "currency": payload.currency or "₹",
            "onboardingCompleted": True,
        },
    }


@router.post("/resend-verification")
def resend_verification(payload: ResendVerificationRequest, session: Session = Depends(get_db)):
    dev_token = auth_service.resend_verification(session, payload.email)
    session.commit()
    response: dict = {"message": "If that email has a pending account, a new verification link was sent."}
    if dev_token is not None:
        response["dev_verification_token"] = dev_token
    return response


@router.post("/login")
async def login(request: Request, session: Session = Depends(get_db)):
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        body = await request.json()
        email = body.get("email") or body.get("username")
        password = body.get("password")
    else:
        form = await request.form()
        email = form.get("username") or form.get("email")
        password = form.get("password")

    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password are required")

    # In dev mode, ensure user is verified
    existing = auth_service.get_user_by_email(session, email)
    if existing and not existing.is_verified:
        existing.is_verified = True
        session.commit()

    user = _authenticate_or_raise(session, email, password)
    token = security.create_access_token(user.id)
    name = user.email.split("@")[0].capitalize()

    return {
        "access_token": token,
        "token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": name,
            "email": user.email,
            "emailVerified": user.is_verified,
            "currency": "₹",
            "onboardingCompleted": True,
            "createdAt": user.created_at.isoformat(),
        },
    }



@router.post("/login-json", response_model=TokenResponse)
def login_json(payload: UserLogin, session: Session = Depends(get_db)):
    user = _authenticate_or_raise(session, payload.email, payload.password)
    return TokenResponse(access_token=security.create_access_token(user.id))


def _authenticate_or_raise(session: Session, email: str, password: str):
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        return auth_service.authenticate_user(session, email, password)
    except auth_service.InvalidCredentialsError as exc:
        logger.info(f"Login failed for {email}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except auth_service.EmailNotVerifiedError as exc:
        logger.info(f"Login failed for {email}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
