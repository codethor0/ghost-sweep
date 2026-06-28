"""Vote create service."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_errors import raise_conflict_from_integrity_error
from app.exceptions import ConflictError, NotFoundError
from app.models.job_posting import JobPosting
from app.models.report import Report
from app.models.user import User
from app.models.vote import Vote
from app.schemas import CreateVoteRequest
from app.services.audit import log_vote_created
from app.services.scoring_pipeline import recalculate_for_job_posting_and_company


async def create_vote(
    session: AsyncSession,
    *,
    report_id: UUID,
    payload: CreateVoteRequest,
    voter: User,
) -> Vote:
    """Create a vote and recalculate related scores.

    Args:
        session: Active database session.
        report_id: Target report UUID.
        payload: Vote submission payload.
        voter: Authenticated voter.

    Returns:
        Vote: Persisted vote record.

    Raises:
        NotFoundError: When the report does not exist.
        ConflictError: When the user already voted on the report.
    """
    report_result = await session.execute(select(Report).where(Report.id == report_id))
    report = report_result.scalar_one_or_none()
    if report is None:
        raise NotFoundError("Report not found")

    existing_vote = await session.execute(
        select(Vote.id).where(Vote.report_id == report_id, Vote.user_id == voter.id)
    )
    if existing_vote.scalar_one_or_none() is not None:
        raise ConflictError("Vote already recorded for this report")

    vote = Vote(report_id=report_id, user_id=voter.id, vote=payload.vote)
    session.add(vote)
    try:
        await session.flush()
    except IntegrityError as exc:
        await session.rollback()
        raise_conflict_from_integrity_error(exc)

    posting_result = await session.execute(
        select(JobPosting).where(JobPosting.id == report.job_posting_id)
    )
    posting = posting_result.scalar_one()

    await log_vote_created(
        session,
        actor_user_id=voter.id,
        vote_id=vote.id,
        report_id=report_id,
        vote_value=payload.vote.value,
    )
    await recalculate_for_job_posting_and_company(session, posting.id, posting.company_id)
    await session.commit()
    await session.refresh(vote)
    return vote
