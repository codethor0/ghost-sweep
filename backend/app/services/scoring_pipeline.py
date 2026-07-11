"""Orchestrate score recalculation and persistence from database state."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.company import Company
from app.models.employer_response import EmployerResponse
from app.models.enums import ReportType, SnapshotEntityType
from app.models.job_posting import JobPosting
from app.models.report import Report
from app.models.score_snapshot import ScoreSnapshot
from app.services.report_eligibility import is_score_eligible, score_eligibility_filter
from app.services.scoring import (
    CompanyIntegrityInputs,
    JobGhostRiskInputs,
    ScoreResult,
    calculate_company_integrity_score,
    calculate_job_ghost_risk_score,
    count_verified_reports,
)


def _posting_age_days(detected_at: datetime) -> int:
    """Return whole days since a posting was first detected."""
    now = datetime.now(tz=UTC)
    if detected_at.tzinfo is None:
        detected_at = detected_at.replace(tzinfo=UTC)
    return max(0, (now - detected_at).days)


def _eligible_reports(reports: list[Report]) -> list[Report]:
    """Filter reports to score-eligible moderation states."""
    return [report for report in reports if is_score_eligible(report.status)]


async def _reports_for_posting(session: AsyncSession, job_posting_id: UUID) -> list[Report]:
    """Load score-eligible reports linked to a job posting."""
    result = await session.execute(
        select(Report).where(
            Report.job_posting_id == job_posting_id,
            score_eligibility_filter(),
        )
    )
    return list(result.scalars().all())


async def _reports_for_company(session: AsyncSession, company_id: UUID) -> list[Report]:
    """Load score-eligible reports linked to postings owned by a company."""
    result = await session.execute(
        select(Report)
        .join(JobPosting, Report.job_posting_id == JobPosting.id)
        .where(JobPosting.company_id == company_id, score_eligibility_filter())
    )
    return list(result.scalars().all())


async def _eligible_responded_report_count(session: AsyncSession, company_id: UUID) -> int:
    """Count distinct eligible reports that received an employer response."""
    result = await session.execute(
        select(func.count(func.distinct(EmployerResponse.report_id)))
        .select_from(EmployerResponse)
        .join(Report, EmployerResponse.report_id == Report.id)
        .join(JobPosting, Report.job_posting_id == JobPosting.id)
        .where(JobPosting.company_id == company_id, score_eligibility_filter())
    )
    return int(result.scalar_one())


def _build_job_inputs(
    posting: JobPosting,
    company: Company,
    reports: list[Report],
) -> JobGhostRiskInputs:
    """Build job ghost risk inputs from ORM entities."""
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


def _build_company_inputs(
    company: Company,
    reports: list[Report],
    responded_report_count: int,
) -> CompanyIntegrityInputs:
    """Build company integrity inputs from ORM entities."""
    report_statuses = [report.status for report in reports]
    eligible_total = len(reports)
    return CompanyIntegrityInputs(
        total_postings=company.total_postings,
        total_hires=company.total_hires,
        verified_report_count=count_verified_reports(report_statuses),
        total_reports=eligible_total,
        employer_response_count=responded_report_count,
        verified_status=company.verified_status,
        average_days_to_fill=None,
        recruiter_follow_through_rate=0.0,
        correction_count=0,
    )


async def calculate_job_posting_risk_score(
    session: AsyncSession,
    job_posting_id: UUID,
) -> ScoreResult:
    """Calculate a job posting risk score without persisting changes."""
    posting = await _load_job_posting(session, job_posting_id)
    reports = await _reports_for_posting(session, job_posting_id)
    inputs = _build_job_inputs(posting, posting.company, reports)
    return calculate_job_ghost_risk_score(inputs)


async def calculate_company_integrity_score_result(
    session: AsyncSession,
    company_id: UUID,
) -> ScoreResult:
    """Calculate a company integrity score without persisting changes."""
    company = await _load_company(session, company_id)
    reports = await _reports_for_company(session, company_id)
    responded_count = await _eligible_responded_report_count(session, company_id)
    inputs = _build_company_inputs(company, reports, responded_count)
    return calculate_company_integrity_score(inputs)


async def recalculate_job_posting_score(
    session: AsyncSession,
    job_posting_id: UUID,
) -> ScoreResult:
    """Recalculate, persist, and snapshot a job posting risk score."""
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
    """Recalculate, persist, and snapshot a company integrity score."""
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
    """Recalculate scores for a posting and its parent company."""
    await recalculate_job_posting_score(session, job_posting_id)
    await recalculate_company_score(session, company_id)


async def _load_job_posting(session: AsyncSession, job_posting_id: UUID) -> JobPosting:
    """Load a job posting with its company relationship."""
    result = await session.execute(
        select(JobPosting)
        .options(selectinload(JobPosting.company))
        .where(JobPosting.id == job_posting_id)
    )
    return result.scalar_one()


async def _load_company(session: AsyncSession, company_id: UUID) -> Company:
    """Load a company for scoring inputs."""
    result = await session.execute(select(Company).where(Company.id == company_id))
    return result.scalar_one()
