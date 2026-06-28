"""Report create and read service."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import NotFoundError
from app.models.company import Company
from app.models.enums import ReportStatus
from app.models.job_posting import JobPosting
from app.models.report import Report
from app.models.user import User
from app.schemas import CreateReportRequest, ReportListResponse, ReportResponse
from app.services.audit import log_report_created
from app.services.scoring_pipeline import recalculate_for_job_posting_and_company


async def create_report(
    session: AsyncSession,
    *,
    payload: CreateReportRequest,
    reporter: User,
) -> Report:
    """Create a report and recalculate related scores.

    Args:
        session: Active database session.
        payload: Report submission payload.
        reporter: Authenticated reporter.

    Returns:
        Report: Persisted report record.

    Raises:
        NotFoundError: When the job posting does not exist.
    """
    posting_result = await session.execute(
        select(JobPosting).where(JobPosting.id == payload.job_posting_id)
    )
    posting = posting_result.scalar_one_or_none()
    if posting is None:
        raise NotFoundError("Job posting not found")

    report = Report(
        job_posting_id=payload.job_posting_id,
        reporter_id=reporter.id,
        report_type=payload.report_type,
        description=payload.description,
        status=ReportStatus.PENDING,
    )
    session.add(report)
    await session.flush()

    company_result = await session.execute(select(Company).where(Company.id == posting.company_id))
    company = company_result.scalar_one()
    company.report_count += 1

    await log_report_created(
        session,
        actor_user_id=reporter.id,
        report_id=report.id,
        job_posting_id=report.job_posting_id,
        report_type=payload.report_type.value,
    )
    await recalculate_for_job_posting_and_company(session, posting.id, posting.company_id)
    await session.commit()
    await session.refresh(report)
    return report


async def get_report(session: AsyncSession, report_id: UUID) -> Report:
    """Load a report by primary key.

    Args:
        session: Active database session.
        report_id: Report UUID.

    Returns:
        Report: Matching report record.

    Raises:
        NotFoundError: When the report does not exist.
    """
    result = await session.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if report is None:
        raise NotFoundError("Report not found")
    return report


async def list_reports_for_job_posting(
    session: AsyncSession,
    job_posting_id: UUID,
    *,
    page: int,
    page_size: int,
) -> ReportListResponse:
    """List reports linked to a job posting.

    Args:
        session: Active database session.
        job_posting_id: Job posting UUID.
        page: One-based page number.
        page_size: Page size capped by the API layer.

    Returns:
        ReportListResponse: Paginated reports for the posting.

    Raises:
        NotFoundError: When the job posting does not exist.
    """
    posting_result = await session.execute(
        select(JobPosting.id).where(JobPosting.id == job_posting_id)
    )
    if posting_result.scalar_one_or_none() is None:
        raise NotFoundError("Job posting not found")

    safe_page = max(page, 1)
    safe_page_size = max(page_size, 1)
    offset = (safe_page - 1) * safe_page_size

    total_result = await session.execute(
        select(func.count()).select_from(Report).where(Report.job_posting_id == job_posting_id)
    )
    total = int(total_result.scalar_one())

    result = await session.execute(
        select(Report)
        .where(Report.job_posting_id == job_posting_id)
        .order_by(Report.created_at.desc())
        .offset(offset)
        .limit(safe_page_size)
    )
    items = [ReportResponse.model_validate(report) for report in result.scalars().all()]
    return ReportListResponse(
        items=items,
        total=total,
        page=safe_page,
        page_size=safe_page_size,
    )
