"""Report ORM model."""

import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, Numeric, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import ReportStatus, ReportType
from app.models.pg_enums import report_status_enum, report_type_enum


class Report(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Evidence-based job integrity report."""

    __tablename__ = "reports"

    job_posting_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("job_postings.id"),
        index=True,
        nullable=False,
    )
    reporter_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        index=True,
        nullable=True,
    )
    report_type: Mapped[ReportType] = mapped_column(report_type_enum, index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ReportStatus] = mapped_column(
        report_status_enum, default=ReportStatus.PENDING, index=True
    )
    confidence_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0.0"))
    verification_votes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    job_posting: Mapped["JobPosting"] = relationship(back_populates="reports")
    reporter: Mapped["User | None"] = relationship(back_populates="reports")
    evidence_files: Mapped[list["EvidenceFile"]] = relationship(back_populates="report")
    votes: Mapped[list["Vote"]] = relationship(back_populates="report")
    employer_responses: Mapped[list["EmployerResponse"]] = relationship(back_populates="report")


from app.models.employer_response import EmployerResponse  # noqa: E402
from app.models.evidence_file import EvidenceFile  # noqa: E402
from app.models.job_posting import JobPosting  # noqa: E402
from app.models.user import User  # noqa: E402
from app.models.vote import Vote  # noqa: E402
