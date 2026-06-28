"""Score snapshot ORM model."""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Numeric, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import UUIDPrimaryKeyMixin
from app.models.enums import SnapshotEntityType
from app.models.pg_enums import snapshot_entity_type_enum


class ScoreSnapshot(Base, UUIDPrimaryKeyMixin):
    """Historical score record for auditability."""

    __tablename__ = "score_snapshots"

    entity_type: Mapped[SnapshotEntityType] = mapped_column(
        snapshot_entity_type_enum, index=True, nullable=False
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), index=True, nullable=False)
    score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    breakdown: Mapped[dict[str, float]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
