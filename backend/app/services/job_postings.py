"""Job posting read service."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.exceptions import NotFoundError
from app.models.job_posting import JobPosting
from app.services.scoring import ScoreResult
from app.services.scoring_pipeline import calculate_job_posting_risk_score


async def get_job_posting(session: AsyncSession, job_posting_id: UUID) -> JobPosting:
    """Load a job posting by primary key.

    Args:
        session: Active database session.
        job_posting_id: Job posting UUID.

    Returns:
        JobPosting: Matching job posting record.

    Raises:
        NotFoundError: When the job posting does not exist.
    """
    result = await session.execute(
        select(JobPosting)
        .options(selectinload(JobPosting.company))
        .where(JobPosting.id == job_posting_id)
    )
    posting = result.scalar_one_or_none()
    if posting is None:
        raise NotFoundError("Job posting not found")
    return posting


async def get_job_posting_risk_score(session: AsyncSession, job_posting_id: UUID) -> ScoreResult:
    """Calculate the current risk score breakdown for a job posting.

    Args:
        session: Active database session.
        job_posting_id: Job posting UUID.

    Returns:
        ScoreResult: Calculated score and breakdown.

    Raises:
        NotFoundError: When the job posting does not exist.
    """
    await get_job_posting(session, job_posting_id)
    return await calculate_job_posting_risk_score(session, job_posting_id)
