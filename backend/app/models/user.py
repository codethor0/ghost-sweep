"""User ORM model."""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import UUIDPrimaryKeyMixin


class User(Base, UUIDPrimaryKeyMixin):
    """Registered platform user."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    reputation_score: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=Decimal("0.0"))
    report_weight: Mapped[Decimal] = mapped_column(Numeric(4, 2), default=Decimal("1.0"))
    is_employer: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    employer_company_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("companies.id"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    reports: Mapped[list["Report"]] = relationship(back_populates="reporter")
    votes: Mapped[list["Vote"]] = relationship(back_populates="user")
    employer_claims: Mapped[list["EmployerClaim"]] = relationship(back_populates="user")
    employer_responses: Mapped[list["EmployerResponse"]] = relationship(back_populates="user")
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="actor")


from app.models.audit_log import AuditLog  # noqa: E402
from app.models.employer_claim import EmployerClaim  # noqa: E402
from app.models.employer_response import EmployerResponse  # noqa: E402
from app.models.report import Report  # noqa: E402
from app.models.vote import Vote  # noqa: E402
