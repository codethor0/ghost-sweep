"""Report create and read service."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_errors import raise_conflict_from_integrity_error
from app.exceptions import ConflictError, NotFoundError
from app.models.company import Company
from app.models.enums import ReportStatus, ReportType
from app.models.job_posting import JobPosting
from app.models.report import Report
from app.models.user import User
from app.schemas import (
    CreateReportRequest,
    PublicReportListResponse,
    PublicReportResponse,
    ReportResponse,
)
from app.services.audit import log_report_created
from app.services.report_eligibility import (
    active_duplicate_filter,
    is_publicly_visible,
    public_visibility_filter,
    score_eligibility_filter,
)
from app.services.scoring_pipeline import recalculate_for_job_posting_and_company

DUPLICATE_REPORT_DETAIL = "A similar report from this account is already active for this posting"


async def _find_active_duplicate_report(
    session: AsyncSession,
    *,
    reporter_id: UUID,
    job_posting_id: UUID,
    report_type: ReportType,
) -> Report | None:
    """Return an active duplicate report when one already exists."""
    result = await session.execute(
        select(Report).where(
            Report.reporter_id == reporter_id,
            Report.job_posting_id == job_posting_id,
            Report.report_type == report_type,
            active_duplicate_filter(),
        )
    )
    return result.scalar_one_or_none()


async def create_report(
    session: AsyncSession,
    *,
    payload: CreateReportRequest,
    reporter: User,
) -> Report:
    """Create a pending report without affecting public scores.

    Args:
        session: Active database session.
        payload: Report submission payload.
        reporter: Authenticated reporter.

    Returns:
        Report: Persisted report record.

    Raises:
        NotFoundError: When the job posting does not exist.
        ConflictError: When a materially duplicate active report exists.
    """
    posting_result = await session.execute(
        select(JobPosting).where(JobPosting.id == payload.job_posting_id)
    )
    posting = posting_result.scalar_one_or_none()
    if posting is None:
        raise NotFoundError("Job posting not found")

    duplicate = await _find_active_duplicate_report(
        session,
        reporter_id=reporter.id,
        job_posting_id=payload.job_posting_id,
        report_type=payload.report_type,
    )
    if duplicate is not None:
        raise ConflictError(DUPLICATE_REPORT_DETAIL)

    report = Report(
        job_posting_id=payload.job_posting_id,
        reporter_id=reporter.id,
        report_type=payload.report_type,
        description=payload.description,
        status=ReportStatus.PENDING,
    )
    session.add(report)
    try:
        await session.flush()
    except IntegrityError as exc:
        await session.rollback()
        raise_conflict_from_integrity_error(exc)

    await log_report_created(
        session,
        actor_user_id=reporter.id,
        report_id=report.id,
        job_posting_id=report.job_posting_id,
        report_type=payload.report_type.value,
    )
    await session.commit()
    await session.refresh(report)
    return report


async def _load_report(session: AsyncSession, report_id: UUID) -> Report | None:
    """Load a report by primary key."""
    result = await session.execute(select(Report).where(Report.id == report_id))
    return result.scalar_one_or_none()


def _user_may_view_internal_report(report: Report, viewer: User | None) -> bool:
    """Return whether an authenticated viewer may access internal report fields."""
    if viewer is None:
        return False
    if viewer.is_admin:
        return True
    return report.reporter_id == viewer.id


async def get_report(
    session: AsyncSession,
    report_id: UUID,
    *,
    viewer: User | None = None,
) -> Report:
    """Load a report respecting public visibility rules.

    Args:
        session: Active database session.
        report_id: Report UUID.
        viewer: Optional authenticated viewer.

    Returns:
        Report: Matching report record.

    Raises:
        NotFoundError: When the report is not visible to the caller.
    """
    report = await _load_report(session, report_id)
    if report is None:
        raise NotFoundError("Report not found")

    if _user_may_view_internal_report(report, viewer):
        return report

    if is_publicly_visible(report.status):
        return report

    raise NotFoundError("Report not found")


def _to_public_response(report: Report) -> PublicReportResponse:
    """Convert a report entity to a public response schema."""
    return PublicReportResponse.model_validate(report)


def _to_internal_response(report: Report) -> ReportResponse:
    """Convert a report entity to an internal response schema."""
    return ReportResponse.model_validate(report)


async def get_report_response(
    session: AsyncSession,
    report_id: UUID,
    *,
    viewer: User | None = None,
) -> PublicReportResponse | ReportResponse:
    """Return the appropriate report schema for the caller."""
    report = await get_report(session, report_id, viewer=viewer)
    if _user_may_view_internal_report(report, viewer):
        return _to_internal_response(report)
    return _to_public_response(report)


async def list_public_reports_for_job_posting(
    session: AsyncSession,
    job_posting_id: UUID,
    *,
    page: int,
    page_size: int,
) -> PublicReportListResponse:
    """List publicly visible reports linked to a job posting.

    Args:
        session: Active database session.
        job_posting_id: Job posting UUID.
        page: One-based page number.
        page_size: Page size capped by the API layer.

    Returns:
        PublicReportListResponse: Paginated public reports for the posting.

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
    visibility = public_visibility_filter()

    total_result = await session.execute(
        select(func.count())
        .select_from(Report)
        .where(Report.job_posting_id == job_posting_id, visibility)
    )
    total = int(total_result.scalar_one())

    result = await session.execute(
        select(Report)
        .where(Report.job_posting_id == job_posting_id, visibility)
        .order_by(Report.created_at.desc())
        .offset(offset)
        .limit(safe_page_size)
    )
    items = [_to_public_response(report) for report in result.scalars().all()]
    return PublicReportListResponse(
        items=items,
        total=total,
        page=safe_page,
        page_size=safe_page_size,
    )


async def adjust_company_report_count(
    session: AsyncSession,
    company_id: UUID,
    *,
    delta: int,
) -> None:
    """Adjust a company's public report count by a signed delta."""
    company_result = await session.execute(select(Company).where(Company.id == company_id))
    company = company_result.scalar_one()
    company.report_count = max(0, company.report_count + delta)


async def sync_company_report_count(session: AsyncSession, company_id: UUID) -> None:
    """Recompute a company's public report count from score-eligible reports."""
    count_result = await session.execute(
        select(func.count())
        .select_from(Report)
        .join(JobPosting, Report.job_posting_id == JobPosting.id)
        .where(JobPosting.company_id == company_id, score_eligibility_filter())
    )
    eligible_count = int(count_result.scalar_one())
    company_result = await session.execute(select(Company).where(Company.id == company_id))
    company = company_result.scalar_one()
    company.report_count = eligible_count


async def recalculate_scores_if_needed(
    session: AsyncSession,
    *,
    job_posting_id: UUID,
    company_id: UUID,
) -> None:
    """Recalculate scores from eligible records only."""
    await recalculate_for_job_posting_and_company(session, job_posting_id, company_id)
