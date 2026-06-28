"""User report and evidence models."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin


class Report(Base, TimestampMixin):
    """Evidence-based job integrity report."""

    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_posting_id: Mapped[int] = mapped_column(
        ForeignKey("job_postings.id"),
        index=True,
        nullable=False,
    )
    submitter_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    timeline_description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="submitted", index=True, nullable=False)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    job_posting: Mapped["JobPosting"] = relationship(back_populates="reports")
    submitter: Mapped["User"] = relationship(back_populates="reports")
    evidence_items: Mapped[list["ReportEvidence"]] = relationship(back_populates="report")


class ReportEvidence(Base, TimestampMixin):
    """Supporting evidence attached to a report."""

    __tablename__ = "report_evidence"

    id: Mapped[int] = mapped_column(primary_key=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("reports.id"), index=True, nullable=False)
    evidence_type: Mapped[str] = mapped_column(String(64), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    report: Mapped["Report"] = relationship(back_populates="evidence_items")


from app.models.job_posting import JobPosting  # noqa: E402
from app.models.user import User  # noqa: E402
