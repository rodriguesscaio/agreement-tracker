import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, String, Text
from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Confidence(str, enum.Enum):
    high = "high"
    medium = "medium"
    low = "low"


class AgreementStatus(str, enum.Enum):
    open = "open"
    resolved = "resolved"


class Agreement(Base):
    __tablename__ = "agreements"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    source_text_excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    owner: Mapped[str] = mapped_column(String(255), nullable=False)
    commitment: Mapped[str] = mapped_column(Text, nullable=False)
    deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    confidence: Mapped[Confidence] = mapped_column(
        Enum(Confidence, name="confidence_level"), nullable=False
    )
    status: Mapped[AgreementStatus] = mapped_column(
        Enum(AgreementStatus, name="agreement_status"),
        nullable=False,
        default=AgreementStatus.open,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
