"""Audit logging for sensitive write actions."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


async def log_report_created(
    session: AsyncSession,
    *,
    actor_user_id: UUID,
    report_id: UUID,
    job_posting_id: UUID,
    report_type: str,
) -> None:
    """Record an audit entry for report creation.

    Args:
        session: Active database session.
        actor_user_id: User who submitted the report.
        report_id: Created report UUID.
        job_posting_id: Related job posting UUID.
        report_type: Report category value.
    """
    session.add(
        AuditLog(
            actor_user_id=actor_user_id,
            action="report.created",
            entity_type="report",
            entity_id=report_id,
            metadata_json={
                "job_posting_id": str(job_posting_id),
                "report_type": report_type,
            },
        )
    )


async def log_vote_created(
    session: AsyncSession,
    *,
    actor_user_id: UUID,
    vote_id: UUID,
    report_id: UUID,
    vote_value: str,
) -> None:
    """Record an audit entry for vote creation.

    Args:
        session: Active database session.
        actor_user_id: User who cast the vote.
        vote_id: Created vote UUID.
        report_id: Related report UUID.
        vote_value: Vote direction value.
    """
    session.add(
        AuditLog(
            actor_user_id=actor_user_id,
            action="vote.created",
            entity_type="vote",
            entity_id=vote_id,
            metadata_json={
                "report_id": str(report_id),
                "vote": vote_value,
            },
        )
    )
