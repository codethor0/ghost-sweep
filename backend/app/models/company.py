"""Company and employer claim models."""

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin


class Company(Base, TimestampMixin):
    """Employer organization tracked by the integrity database."""

    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    website: Mapped[str | None] = mapped_column(String(512), nullable=True)
    profile_status: Mapped[str] = mapped_column(
        String(32),
        default="unclaimed",
        index=True,
        nullable=False,
    )

    job_postings: Mapped[list["JobPosting"]] = relationship(back_populates="company")
    claims: Mapped[list["CompanyClaim"]] = relationship(back_populates="company")


class CompanyClaim(Base, TimestampMixin):
    """Employer claim request for a company profile."""

    __tablename__ = "company_claims"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True, nullable=False)
    claimant_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), index=True, nullable=False
    )
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True, nullable=False)
    verification_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    company: Mapped["Company"] = relationship(back_populates="claims")


from app.models.job_posting import JobPosting  # noqa: E402
