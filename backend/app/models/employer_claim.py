"""Employer claim ORM model."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import UUIDPrimaryKeyMixin
from app.models.enums import ClaimStatus
from app.models.pg_enums import claim_status_enum


class EmployerClaim(Base, UUIDPrimaryKeyMixin):
    """Employer request to claim a company profile."""

    __tablename__ = "employer_claims"

    company_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("companies.id"),
        index=True,
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        index=True,
        nullable=False,
    )
    status: Mapped[ClaimStatus] = mapped_column(
        claim_status_enum, default=ClaimStatus.PENDING, index=True
    )
    verification_documents: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    company: Mapped["Company"] = relationship(back_populates="employer_claims")
    user: Mapped["User"] = relationship(back_populates="employer_claims")


from app.models.company import Company  # noqa: E402
from app.models.user import User  # noqa: E402
