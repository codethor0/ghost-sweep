"""Vote ORM model."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import UUIDPrimaryKeyMixin
from app.models.enums import VoteValue


class Vote(Base, UUIDPrimaryKeyMixin):
    """Community vote on a report."""

    __tablename__ = "votes"
    __table_args__ = (UniqueConstraint("report_id", "user_id", name="uq_votes_report_user"),)

    report_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("reports.id"),
        index=True,
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        index=True,
        nullable=False,
    )
    vote: Mapped[VoteValue] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    report: Mapped["Report"] = relationship(back_populates="votes")
    user: Mapped["User"] = relationship(back_populates="votes")


from app.models.report import Report  # noqa: E402
from app.models.user import User  # noqa: E402
