"""Job posting model."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin


class JobPosting(Base, TimestampMixin):
    """Tracked job posting linked to a company."""

    __tablename__ = "job_postings"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    posting_url: Mapped[str] = mapped_column(String(1024), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="reported", index=True, nullable=False)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    description_excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)

    company: Mapped["Company"] = relationship(back_populates="job_postings")
    reports: Mapped[list["Report"]] = relationship(back_populates="job_posting")


from app.models.company import Company  # noqa: E402
from app.models.report import Report  # noqa: E402
