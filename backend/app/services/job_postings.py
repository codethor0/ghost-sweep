"""Job posting query and scoring service."""

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.exceptions import NotFoundError
from app.models.job_posting import JobPosting
from app.models.report import Report
from app.schemas.job_posting import (
    GhostRiskScoreResponse,
    JobPostingResponse,
    ScoreComponentResponse,
)
from app.services.scoring import ScoringInputs, VerificationStatus, calculate_ghost_risk_score


def _map_verification_status(posting_status: str, reviewed_report_count: int) -> VerificationStatus:
    """Map posting state to a verification enum.

    Args:
        posting_status: Stored posting status.
        reviewed_report_count: Number of reviewed reports.

    Returns:
        VerificationStatus: Verification state used by scoring.
    """
    if posting_status == "verified_active":
        return VerificationStatus.VERIFIED_ACTIVE
    if posting_status == "disputed":
        return VerificationStatus.DISPUTED
    if reviewed_report_count > 0:
        return VerificationStatus.EVIDENCE_REVIEWED
    return VerificationStatus.UNVERIFIED


async def get_job_posting(session: AsyncSession, job_posting_id: int) -> JobPostingResponse:
    """Fetch a job posting by id.

    Args:
        session: Database session.
        job_posting_id: Job posting primary key.

    Returns:
        JobPostingResponse: Job posting details.

    Raises:
        NotFoundError: When the posting does not exist.
    """
    result = await session.execute(select(JobPosting).where(JobPosting.id == job_posting_id))
    posting = result.scalar_one_or_none()
    if posting is None:
        raise NotFoundError("Job posting not found")
    return JobPostingResponse.model_validate(posting)


async def get_job_posting_risk_score(
    session: AsyncSession,
    job_posting_id: int,
) -> GhostRiskScoreResponse:
    """Calculate and return a transparent risk score for a posting.

    Args:
        session: Database session.
        job_posting_id: Job posting primary key.

    Returns:
        GhostRiskScoreResponse: Explained risk score.

    Raises:
        NotFoundError: When the posting does not exist.
    """
    result = await session.execute(
        select(JobPosting)
        .options(selectinload(JobPosting.reports))
        .where(JobPosting.id == job_posting_id)
    )
    posting = result.scalar_one_or_none()
    if posting is None:
        raise NotFoundError("Job posting not found")

    report_count = len(posting.reports)
    reviewed_report_count = len(
        [report for report in posting.reports if report.reviewed_at is not None]
    )

    duplicate_result = await session.execute(
        select(func.count())
        .select_from(Report)
        .where(Report.job_posting_id == posting.id)
        .group_by(Report.category)
        .having(func.count() > 1)
    )
    duplicate_report_count = len(duplicate_result.all())

    now = datetime.now(tz=UTC)
    days_since_first_seen = max((now - posting.first_seen_at).days, 0)
    days_since_last_repost = max((now - posting.last_seen_at).days, 0)

    score = calculate_ghost_risk_score(
        ScoringInputs(
            report_count=report_count,
            reviewed_report_count=reviewed_report_count,
            days_since_first_seen=days_since_first_seen,
            days_since_last_repost=days_since_last_repost,
            duplicate_report_count=duplicate_report_count,
            verification_status=_map_verification_status(posting.status, reviewed_report_count),
        )
    )

    return GhostRiskScoreResponse(
        job_posting_id=posting.id,
        score=score.score,
        confidence=score.confidence,
        explanation=score.explanation,
        components=[ScoreComponentResponse.from_component(item) for item in score.components],
        calculated_at=score.calculated_at,
    )
