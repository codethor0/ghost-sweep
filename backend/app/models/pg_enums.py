"""PostgreSQL enum columns aligned with Alembic-created types."""

from enum import Enum
from typing import TypeVar

from sqlalchemy import Enum as SAEnum

from app.models.enums import (
    ClaimStatus,
    PostingSource,
    PostingStatus,
    ReportStatus,
    ReportType,
    SnapshotEntityType,
    VerifiedStatus,
    VoteValue,
)

EnumT = TypeVar("EnumT", bound=Enum)


def pg_enum(enum_class: type[EnumT], name: str) -> SAEnum:
    """Build a SQLAlchemy enum bound to an existing PostgreSQL type."""
    return SAEnum(
        enum_class,
        name=name,
        create_type=False,
        values_callable=lambda members: [member.value for member in members],
    )


verified_status_enum = pg_enum(VerifiedStatus, "verified_status_enum")
posting_source_enum = pg_enum(PostingSource, "posting_source_enum")
posting_status_enum = pg_enum(PostingStatus, "posting_status_enum")
report_type_enum = pg_enum(ReportType, "report_type_enum")
report_status_enum = pg_enum(ReportStatus, "report_status_enum")
claim_status_enum = pg_enum(ClaimStatus, "claim_status_enum")
vote_value_enum = pg_enum(VoteValue, "vote_value_enum")
snapshot_entity_type_enum = pg_enum(SnapshotEntityType, "snapshot_entity_type_enum")
