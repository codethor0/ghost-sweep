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


async def log_employer_claim_created(
    session: AsyncSession,
    *,
    actor_user_id: UUID,
    claim_id: UUID,
    company_id: UUID,
) -> None:
    """Record an audit entry for employer claim submission."""
    session.add(
        AuditLog(
            actor_user_id=actor_user_id,
            action="employer_claim.created",
            entity_type="employer_claim",
            entity_id=claim_id,
            metadata_json={"company_id": str(company_id)},
        )
    )


async def log_employer_claim_approved(
    session: AsyncSession,
    *,
    actor_user_id: UUID,
    claim_id: UUID,
    company_id: UUID,
    claimant_user_id: UUID,
) -> None:
    """Record an audit entry for employer claim approval."""
    session.add(
        AuditLog(
            actor_user_id=actor_user_id,
            action="employer_claim.approved",
            entity_type="employer_claim",
            entity_id=claim_id,
            metadata_json={
                "company_id": str(company_id),
                "claimant_user_id": str(claimant_user_id),
            },
        )
    )


async def log_employer_claim_rejected(
    session: AsyncSession,
    *,
    actor_user_id: UUID,
    claim_id: UUID,
    company_id: UUID,
    claimant_user_id: UUID,
    reason: str | None,
) -> None:
    """Record an audit entry for employer claim rejection."""
    metadata: dict[str, object] = {
        "company_id": str(company_id),
        "claimant_user_id": str(claimant_user_id),
    }
    if reason is not None:
        metadata["reason"] = reason
    session.add(
        AuditLog(
            actor_user_id=actor_user_id,
            action="employer_claim.rejected",
            entity_type="employer_claim",
            entity_id=claim_id,
            metadata_json=metadata,
        )
    )


async def log_report_verified(
    session: AsyncSession,
    *,
    actor_user_id: UUID,
    report_id: UUID,
    job_posting_id: UUID,
    previous_status: str,
) -> None:
    """Record an audit entry for report verification."""
    session.add(
        AuditLog(
            actor_user_id=actor_user_id,
            action="report.verified",
            entity_type="report",
            entity_id=report_id,
            metadata_json={
                "job_posting_id": str(job_posting_id),
                "previous_status": previous_status,
                "new_status": "verified",
            },
        )
    )


async def log_report_dismissed(
    session: AsyncSession,
    *,
    actor_user_id: UUID,
    report_id: UUID,
    job_posting_id: UUID,
    previous_status: str,
    reason: str | None,
) -> None:
    """Record an audit entry for report dismissal."""
    metadata: dict[str, object] = {
        "job_posting_id": str(job_posting_id),
        "previous_status": previous_status,
        "new_status": "dismissed",
    }
    if reason is not None:
        metadata["reason"] = reason
    session.add(
        AuditLog(
            actor_user_id=actor_user_id,
            action="report.dismissed",
            entity_type="report",
            entity_id=report_id,
            metadata_json=metadata,
        )
    )


async def log_employer_response_created(
    session: AsyncSession,
    *,
    actor_user_id: UUID,
    response_id: UUID,
    report_id: UUID,
    company_id: UUID,
    previous_status: str,
    new_status: str,
) -> None:
    """Record an audit entry for employer response creation."""
    session.add(
        AuditLog(
            actor_user_id=actor_user_id,
            action="employer_response.created",
            entity_type="employer_response",
            entity_id=response_id,
            metadata_json={
                "report_id": str(report_id),
                "company_id": str(company_id),
                "previous_status": previous_status,
                "new_status": new_status,
            },
        )
    )
