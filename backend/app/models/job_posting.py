"""Job posting ORM model."""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import UUIDPrimaryKeyMixin
from app.models.enums import PostingSource, PostingStatus
from app.models.pg_enums import posting_source_enum, posting_status_enum


class JobPosting(Base, UUIDPrimaryKeyMixin):
    """Tracked job posting linked to a company."""

    __tablename__ = "job_postings"

    company_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("companies.id"),
        index=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str] = mapped_column(String(1024), unique=True, nullable=False)
    source: Mapped[PostingSource] = mapped_column(
        posting_source_enum, default=PostingSource.OTHER, index=True
    )
    posted_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[PostingStatus] = mapped_column(
        posting_status_enum, default=PostingStatus.ACTIVE, index=True
    )
    ghost_risk_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("50.0"))
    repost_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    original_posting_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("job_postings.id"),
        nullable=True,
    )
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    company: Mapped["Company"] = relationship(back_populates="job_postings")
    reports: Mapped[list["Report"]] = relationship(back_populates="job_posting")
    original_posting: Mapped["JobPosting | None"] = relationship(
        remote_side="JobPosting.id",
        foreign_keys=[original_posting_id],
    )


from app.models.company import Company  # noqa: E402
from app.models.report import Report  # noqa: E402
