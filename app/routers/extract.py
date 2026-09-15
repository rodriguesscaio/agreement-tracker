from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Agreement
from app.schemas import ExtractResponse
from app.services.extraction import extract_agreements_from_text

router = APIRouter(tags=["extract"])


@router.post("/extract", response_model=ExtractResponse, status_code=201)
async def extract_agreements(
    request: Request,
    text: str | None = Form(None),
    file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
) -> ExtractResponse | RedirectResponse:
    """Accepts pasted text or an uploaded .txt file, extracts agreements via
    Claude, and persists them. Browser form submissions (Accept: text/html)
    are redirected back to the dashboard; API clients get the created
    agreements as JSON.
    """
    if file is not None and file.filename:
        raw_bytes = await file.read()
        raw_text = raw_bytes.decode("utf-8", errors="replace")
    elif text:
        raw_text = text
    else:
        raise HTTPException(status_code=400, detail="Provide 'text' or upload a 'file'")

    if not raw_text.strip():
        raise HTTPException(status_code=400, detail="Input text is empty")

    extracted = extract_agreements_from_text(raw_text)

    saved: list[Agreement] = []
    for item in extracted:
        agreement = Agreement(
            source_text_excerpt=item.source_text_excerpt,
            owner=item.owner,
            commitment=item.commitment,
            deadline=item.deadline,
            confidence=item.confidence,
        )
        db.add(agreement)
        saved.append(agreement)
    db.commit()
    for agreement in saved:
        db.refresh(agreement)

    if "text/html" in request.headers.get("accept", ""):
        return RedirectResponse(url="/dashboard", status_code=303)

    return ExtractResponse(agreements=saved)
