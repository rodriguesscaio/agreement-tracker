from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Agreement, AgreementStatus

router = APIRouter(tags=["dashboard"])

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    agreements = list(
        db.execute(select(Agreement).order_by(Agreement.created_at.desc())).scalars().all()
    )
    open_agreements = [a for a in agreements if a.status == AgreementStatus.open]
    resolved_agreements = [a for a in agreements if a.status == AgreementStatus.resolved]

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "open_agreements": open_agreements,
            "resolved_agreements": resolved_agreements,
        },
    )
