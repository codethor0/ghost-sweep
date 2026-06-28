"""Orchestrate score recalculation and persistence from database state."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.company import Company
from app.models.enums import ReportType, SnapshotEntityType
from app.models.job_posting import JobPosting
from app.models.report import Report
from app.models.score_snapshot import ScoreSnapshot
from app.services.scoring import (
    CompanyIntegrityInputs,
    JobGhostRiskInputs,
    ScoreResult,
    calculate_company_integrity_score,
    calculate_job_ghost_risk_score,
    count_verified_reports,
)


def _posting_age_days(detected_at: datetime) -> int:
    """Return whole days since a posting was first detected.

    Args:
        detected_at: Posting detection timestamp.

    Returns:
        int: Non-negative day count.
    """
    now = datetime.now(tz=UTC)
    if detected_at.tzinfo is None:
        detected_at = detected_at.replace(tzinfo=UTC)
    return max(0, (now - detected_at).days)


async def _reports_for_posting(session: AsyncSession, job_posting_id: UUID) -> list[Report]:
    """Load reports linked to a job posting.

    Args:
        session: Active database session.
        job_posting_id: Job posting UUID.

    Returns:
        list[Report]: Reports for the posting.
    """
    result = await session.execute(select(Report).where(Report.job_posting_id == job_posting_id))
    return list(result.scalars().all())


async def _reports_for_company(session: AsyncSession, company_id: UUID) -> list[Report]:
    """Load reports linked to postings owned by a company.

    Args:
        session: Active database session.
        company_id: Company UUID.

    Returns:
        list[Report]: Reports across the company's postings.
    """
    result = await session.execute(
        select(Report)
        .join(JobPosting, Report.job_posting_id == JobPosting.id)
        .where(JobPosting.company_id == company_id)
    )
    return list(result.scalars().all())


def _build_job_inputs(
    posting: JobPosting,
    company: Company,
    reports: list[Report],
) -> JobGhostRiskInputs:
    """Build job ghost risk inputs from ORM entities.

    Args:
        posting: Job posting entity.
        company: Parent company entity.
        reports: Reports linked to the posting.

    Returns:
        JobGhostRiskInputs: Normalized scoring inputs.
    """
    report_statuses = [report.status for report in reports]
    return JobGhostRiskInputs(
        posting_age_days=_posting_age_days(posting.detected_at),
        repost_count=posting.repost_count,
        company_integrity_score=float(company.integrity_score),
        verified_report_count=count_verified_reports(report_statuses),
        language_risk_signal=0.0,
        no_response_report_count=sum(
            1 for report in reports if report.report_type == ReportType.NO_RESPONSE
        ),
        fake_interview_report_count=sum(
            1 for report in reports if report.report_type == ReportType.FAKE_INTERVIEW
        ),
        posting_status=posting.status,
    )


def _build_company_inputs(company: Company, reports: list[Report]) -> CompanyIntegrityInputs:
    """Build company integrity inputs from ORM entities.

    Args:
        company: Company entity.
        reports: Reports linked to company postings.

    Returns:
        CompanyIntegrityInputs: Normalized scoring inputs.
    """
    report_statuses = [report.status for report in reports]
    return CompanyIntegrityInputs(
        total_postings=company.total_postings,
        total_hires=company.total_hires,
        verified_report_count=count_verified_reports(report_statuses),
        total_reports=company.report_count,
        employer_response_count=len(company.employer_responses),
        verified_status=company.verified_status,
        average_days_to_fill=None,
        recruiter_follow_through_rate=0.0,
        correction_count=0,
    )


async def calculate_job_posting_risk_score(
    session: AsyncSession,
    job_posting_id: UUID,
) -> ScoreResult:
    """Calculate a job posting risk score without persisting changes.

    Args:
        session: Active database session.
        job_posting_id: Job posting UUID.

    Returns:
        ScoreResult: Calculated score and breakdown.
    """
    posting = await _load_job_posting(session, job_posting_id)
    reports = await _reports_for_posting(session, job_posting_id)
    inputs = _build_job_inputs(posting, posting.company, reports)
    return calculate_job_ghost_risk_score(inputs)


async def calculate_company_integrity_score_result(
    session: AsyncSession,
    company_id: UUID,
) -> ScoreResult:
    """Calculate a company integrity score without persisting changes.

    Args:
        session: Active database session.
        company_id: Company UUID.

    Returns:
        ScoreResult: Calculated score and breakdown.
    """
    company = await _load_company(session, company_id)
    reports = await _reports_for_company(session, company_id)
    inputs = _build_company_inputs(company, reports)
    return calculate_company_integrity_score(inputs)


async def recalculate_job_posting_score(
    session: AsyncSession,
    job_posting_id: UUID,
) -> ScoreResult:
    """Recalculate, persist, and snapshot a job posting risk score.

    Args:
        session: Active database session.
        job_posting_id: Job posting UUID.

    Returns:
        ScoreResult: Updated score and breakdown.
    """
    result = await calculate_job_posting_risk_score(session, job_posting_id)
    posting = await _load_job_posting(session, job_posting_id)
    posting.ghost_risk_score = Decimal(str(result.score))
    session.add(
        ScoreSnapshot(
            entity_type=SnapshotEntityType.JOB_POSTING,
            entity_id=posting.id,
            score=Decimal(str(result.score)),
            breakdown=result.breakdown,
        )
    )
    return result


async def recalculate_company_score(
    session: AsyncSession,
    company_id: UUID,
) -> ScoreResult:
    """Recalculate, persist, and snapshot a company integrity score.

    Args:
        session: Active database session.
        company_id: Company UUID.

    Returns:
        ScoreResult: Updated score and breakdown.
    """
    result = await calculate_company_integrity_score_result(session, company_id)
    company = await _load_company(session, company_id)
    company.integrity_score = Decimal(str(result.score))
    session.add(
        ScoreSnapshot(
            entity_type=SnapshotEntityType.COMPANY,
            entity_id=company.id,
            score=Decimal(str(result.score)),
            breakdown=result.breakdown,
        )
    )
    return result


async def recalculate_for_job_posting_and_company(
    session: AsyncSession,
    job_posting_id: UUID,
    company_id: UUID,
) -> None:
    """Recalculate scores for a posting and its parent company.

    Args:
        session: Active database session.
        job_posting_id: Job posting UUID.
        company_id: Company UUID.
    """
    await recalculate_job_posting_score(session, job_posting_id)
    await recalculate_company_score(session, company_id)


async def _load_job_posting(session: AsyncSession, job_posting_id: UUID) -> JobPosting:
    """Load a job posting with its company relationship.

    Args:
        session: Active database session.
        job_posting_id: Job posting UUID.

    Returns:
        JobPosting: Loaded posting with company attached.
    """
    result = await session.execute(
        select(JobPosting)
        .options(selectinload(JobPosting.company))
        .where(JobPosting.id == job_posting_id)
    )
    return result.scalar_one()


async def _load_company(session: AsyncSession, company_id: UUID) -> Company:
    """Load a company with employer responses for scoring inputs.

    Args:
        session: Active database session.
        company_id: Company UUID.

    Returns:
        Company: Loaded company with responses attached.
    """
    result = await session.execute(
        select(Company)
        .options(selectinload(Company.employer_responses))
        .where(Company.id == company_id)
    )
    return result.scalar_one()
