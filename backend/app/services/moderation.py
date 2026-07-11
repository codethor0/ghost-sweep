"""Report moderation state transitions for admin review."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.exceptions import NotFoundError, ValidationError
from app.models.enums import ReportStatus
from app.models.report import Report
from app.models.user import User
from app.schemas import ReportListResponse, ReportResponse
from app.services.audit import log_report_dismissed, log_report_verified
from app.services.reports import recalculate_scores_if_needed, sync_company_report_count

_ADMIN_VERIFY_FROM = frozenset({ReportStatus.PENDING, ReportStatus.DISPUTED})
_ADMIN_DISMISS_FROM = frozenset({ReportStatus.PENDING, ReportStatus.DISPUTED})


async def _get_report_with_posting(session: AsyncSession, report_id: UUID) -> Report:
    """Load a report with its job posting relationship."""
    result = await session.execute(
        select(Report).options(selectinload(Report.job_posting)).where(Report.id == report_id)
    )
    report = result.scalar_one_or_none()
    if report is None:
        raise NotFoundError("Report not found")
    return report


async def list_reports_by_status(
    session: AsyncSession,
    *,
    status: ReportStatus,
    page: int,
    page_size: int,
) -> ReportListResponse:
    """Return paginated reports filtered by moderation status."""
    safe_page = max(page, 1)
    safe_page_size = max(page_size, 1)
    offset = (safe_page - 1) * safe_page_size

    total_result = await session.execute(
        select(func.count()).select_from(Report).where(Report.status == status)
    )
    total = int(total_result.scalar_one())

    result = await session.execute(
        select(Report)
        .where(Report.status == status)
        .order_by(Report.created_at.asc())
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


async def verify_report(
    session: AsyncSession,
    *,
    report_id: UUID,
    admin: User,
) -> Report:
    """Mark a report as verified after admin review."""
    report = await _get_report_with_posting(session, report_id)
    if report.status not in _ADMIN_VERIFY_FROM:
        raise ValidationError("Report cannot be verified from its current status")

    previous_status = report.status
    report.status = ReportStatus.VERIFIED

    await log_report_verified(
        session,
        actor_user_id=admin.id,
        report_id=report.id,
        job_posting_id=report.job_posting_id,
        previous_status=previous_status.value,
    )
    await recalculate_scores_if_needed(
        session,
        job_posting_id=report.job_posting_id,
        company_id=report.job_posting.company_id,
    )
    await sync_company_report_count(session, report.job_posting.company_id)
    await session.commit()
    await session.refresh(report)
    return report


async def dismiss_report(
    session: AsyncSession,
    *,
    report_id: UUID,
    admin: User,
    reason: str | None,
) -> Report:
    """Dismiss a report after admin review."""
    report = await _get_report_with_posting(session, report_id)
    if report.status not in _ADMIN_DISMISS_FROM:
        raise ValidationError("Report cannot be dismissed from its current status")

    previous_status = report.status
    report.status = ReportStatus.DISMISSED

    await log_report_dismissed(
        session,
        actor_user_id=admin.id,
        report_id=report.id,
        job_posting_id=report.job_posting_id,
        previous_status=previous_status.value,
        reason=reason,
    )
    await recalculate_scores_if_needed(
        session,
        job_posting_id=report.job_posting_id,
        company_id=report.job_posting.company_id,
    )
    await sync_company_report_count(session, report.job_posting.company_id)
    await session.commit()
    await session.refresh(report)
    return report
