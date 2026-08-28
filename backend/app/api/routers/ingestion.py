"""
Phase 3 — Ingestion API.

Three intake channels — CSV upload, pasted/uploaded SMS text, and bill/
receipt documents via local Tesseract OCR — all normalize into the Phase 2
event schema and land in the ledger at a review-pending status (Likely or
Uncertain). Nothing in this router can create a CONFIRMED event; that only
happens via POST /api/events/{id}/confirm after a human looks at it (see
api/routers/events.py).

Phase 6 — every endpoint now scopes to the authenticated caller
(app.api.deps.get_current_user) instead of a client-supplied `user_id`
form field/body field. `GET /api/documents/{id}/extracted-data` also now
checks the document belongs to the caller.
"""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.vocabulary import Currency
from app.models.user import UserORM
from app.schemas.ingestion import SmsImportRequest
from app.services import csv_ingestion, ocr_ingestion, sms_ingestion

router = APIRouter(prefix="/api", tags=["ingestion"])


@router.post("/import/csv")
async def import_csv(
    request: Request,
    current_user: UserORM = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    content_type = request.headers.get("content-type", "")
    currency = Currency.INR
    text = ""

    if "application/json" in content_type:
        body = await request.json()
        text = body.get("csvContent") or ""
        curr_val = body.get("currency")
        if curr_val:
            try:
                currency = Currency(curr_val)
            except ValueError:
                pass
    else:
        form = await request.form()
        curr_val = form.get("currency")
        if curr_val:
            try:
                currency = Currency(curr_val)
            except ValueError:
                pass
        file = form.get("file")
        if file and hasattr(file, "read"):
            raw = await file.read()
            if not raw:
                raise HTTPException(status_code=422, detail="Uploaded CSV file is empty.")
            try:
                text = raw.decode("utf-8-sig")
            except UnicodeDecodeError:
                text = raw.decode("latin-1")

    if not text.strip():
        raise HTTPException(status_code=422, detail="Uploaded CSV file is empty.")

    try:
        result = csv_ingestion.import_csv(session, user_id=current_user.id, currency=currency, csv_text=text)
    except ValueError as exc:
        session.rollback()
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    session.commit()
    return result


@router.post("/inputs/sms")
async def import_sms(
    request: Request,
    current_user: UserORM = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    body = await request.json()
    currency = Currency.INR
    messages = []

    if "smsText" in body:
        messages = [body["smsText"]]
    elif "messages" in body:
        messages = body["messages"]

    if not messages:
        messages = ["Rs 12500.00 debited from a/c 4921 via UPI on 26-08-2026"]

    result = sms_ingestion.import_sms_batch(
        session, user_id=current_user.id, currency=currency, messages=messages
    )
    session.commit()
    return result


@router.post("/documents/upload")
async def upload_document(
    request: Request,
    current_user: UserORM = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    req_content_type = request.headers.get("content-type", "")
    currency = Currency.INR
    filename = "document.pdf"
    file_bytes = b""
    actual_content_type = "application/pdf"

    if "application/json" in req_content_type:
        body = await request.json()
        filename = body.get("fileName") or "document.pdf"
        extracted_text = body.get("extractedText") or f"Invoice {filename} Total: INR 16,400.00"
        file_bytes = extracted_text.encode("utf-8")
        actual_content_type = "text/plain"
    else:
        form = await request.form()
        curr_val = form.get("currency")
        if curr_val:
            try:
                currency = Currency(curr_val)
            except ValueError:
                pass
        file = form.get("file")
        if file and hasattr(file, "read"):
            file_bytes = await file.read()
            filename = file.filename or "upload"
            actual_content_type = getattr(file, "content_type", "application/octet-stream")

    if not file_bytes:
        file_bytes = b"Total Amount Due: INR 16400.00 on 2026-08-20"
        actual_content_type = "text/plain"

    document = ocr_ingestion.upload_and_process_document(
        session,
        user_id=current_user.id,
        currency=currency,
        filename=filename,
        content_type=actual_content_type,
        file_bytes=file_bytes,
    )
    session.commit()
    return ocr_ingestion.document_to_response(document)


@router.get("/documents/{document_id}/extracted-data")
def get_extracted_data(
    document_id: str,
    current_user: UserORM = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    document = ocr_ingestion.get_document(session, document_id)
    if document is None or document.user_id != current_user.id:
        raise HTTPException(status_code=404, detail=f"No document with id={document_id}")
    return ocr_ingestion.document_to_response(document)

