"""Company ORM model."""

from decimal import Decimal

from sqlalchemy import Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import VerifiedStatus
from app.models.pg_enums import verified_status_enum


class Company(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Employer organization tracked by the integrity database."""

    __tablename__ = "companies"

    name: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    domain: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    industry: Mapped[str | None] = mapped_column(String(128), nullable=True)
    size: Mapped[str | None] = mapped_column(String(64), nullable=True)
    locations: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    integrity_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("50.0"))
    verified_status: Mapped[VerifiedStatus] = mapped_column(
        verified_status_enum,
        default=VerifiedStatus.UNVERIFIED,
        index=True,
    )
    total_postings: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_hires: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    report_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    job_postings: Mapped[list["JobPosting"]] = relationship(back_populates="company")
    employer_claims: Mapped[list["EmployerClaim"]] = relationship(back_populates="company")
    employer_responses: Mapped[list["EmployerResponse"]] = relationship(back_populates="company")


from app.models.employer_claim import EmployerClaim  # noqa: E402
from app.models.employer_response import EmployerResponse  # noqa: E402
from app.models.job_posting import JobPosting  # noqa: E402
