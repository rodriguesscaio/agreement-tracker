import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Agreement, AgreementStatus
from app.schemas import AgreementRead

router = APIRouter(tags=["agreements"])


@router.get("/agreements", response_model=list[AgreementRead])
def list_agreements(
    status: AgreementStatus | None = Query(None, description="Filter by open/resolved"),
    db: Session = Depends(get_db),
) -> list[Agreement]:
    stmt = select(Agreement).order_by(Agreement.created_at.desc())
    if status is not None:
        stmt = stmt.where(Agreement.status == status)
    return db.execute(stmt).scalars().all()


@router.post("/agreements/{agreement_id}/resolve", response_model=AgreementRead)
def resolve_agreement(
    agreement_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
) -> Agreement | RedirectResponse:
    """Marks an agreement as resolved. Browser form submissions (Accept:
    text/html) are redirected back to the dashboard; API clients get the
    updated agreement as JSON.
    """
    agreement = db.get(Agreement, agreement_id)
    if agreement is None:
        raise HTTPException(status_code=404, detail="Agreement not found")

    agreement.status = AgreementStatus.resolved
    db.commit()
    db.refresh(agreement)

    if "text/html" in request.headers.get("accept", ""):
        return RedirectResponse(url="/dashboard", status_code=303)

    return agreement


@router.post("/agreements/{agreement_id}/remind", response_model=AgreementRead)
def remind_agreement(
    agreement_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
) -> Agreement | RedirectResponse:
    """Marks an open agreement as reminded, recording when the reminder was
    sent. This is a visual flag on the dashboard only — no email, push, or
    other external notification is sent (see README Future Work).
    """
    agreement = db.get(Agreement, agreement_id)
    if agreement is None:
        raise HTTPException(status_code=404, detail="Agreement not found")

    agreement.reminder_sent_at = datetime.now(UTC)
    db.commit()
    db.refresh(agreement)

    if "text/html" in request.headers.get("accept", ""):
        return RedirectResponse(url="/dashboard", status_code=303)

    return agreement
