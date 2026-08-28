"""
Phase 6 — Auth request/response contracts (Pydantic).
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class UserRead(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    email: EmailStr
    is_verified: bool
    created_at: datetime


class RegisterResponse(BaseModel):
    user: UserRead
    message: str = "Registration successful. Check your email to verify your account."
    access_token: Optional[str] = None
    token: Optional[str] = None
    dev_verification_token: Optional[str] = Field(
        default=None,
        description=(
            "Only populated when ASTRAFLOW_EXPOSE_VERIFICATION_TOKEN=true "
            "(the default, since no SMTP backend is wired up yet). Set "
            "that env var to false once real email delivery is added."
        ),
    )


class VerifyEmailRequest(BaseModel):
    token: str = Field(..., min_length=1)


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
