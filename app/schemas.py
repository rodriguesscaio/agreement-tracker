import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models import AgreementStatus, Confidence


class ExtractedAgreement(BaseModel):
    """One agreement as returned by Claude, before it is persisted."""

    source_text_excerpt: str
    owner: str
    commitment: str
    deadline: date | None = None
    confidence: Confidence


class AgreementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_text_excerpt: str
    owner: str
    commitment: str
    deadline: date | None
    confidence: Confidence
    status: AgreementStatus
    created_at: datetime
    updated_at: datetime


class ExtractResponse(BaseModel):
    agreements: list[AgreementRead]
