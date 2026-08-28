"""
AstraFlow Chat & Copilot API Router.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.vocabulary import Currency
from app.models.user import UserORM
from app.services import ai_copilot

router = APIRouter(prefix="/api", tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    currency: Currency = Currency.INR


class ChatResponse(BaseModel):
    reply: str
    timestamp: str


@router.post("/chat", response_model=ChatResponse)
def copilot_chat(
    payload: ChatRequest,
    current_user: UserORM = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    """
    Direct endpoint for Astra Copilot chat. Uses Gemini AI grounded on user's real DB records.
    """
    result = ai_copilot.generate_copilot_response(
        session=session,
        user=current_user,
        user_query=payload.message,
        currency=payload.currency,
    )
    return ChatResponse(reply=result["reply"], timestamp=result["timestamp"])
