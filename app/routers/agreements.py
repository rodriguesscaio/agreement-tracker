from fastapi import APIRouter, Depends, Query
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
    return list(db.execute(stmt).scalars().all())
