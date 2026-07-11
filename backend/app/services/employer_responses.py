"""Employer response submission for integrity reports."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db_errors import raise_conflict_from_integrity_error
from app.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.employer_response import EmployerResponse
from app.models.enums import ReportStatus
from app.models.report import Report
from app.models.user import User
from app.schemas import (
    CreateEmployerResponseRequest,
    PublicEmployerResponseListResponse,
    PublicEmployerResponseResponse,
)
from app.services.audit import log_employer_response_created
from app.services.report_eligibility import is_publicly_visible
from app.services.reports import sync_company_report_count
from app.services.scoring_pipeline import recalculate_for_job_posting_and_company

_DISPUTE_FROM = frozenset({ReportStatus.PENDING, ReportStatus.VERIFIED})
_DUPLICATE_RESPONSE_DETAIL = "An employer response from this account already exists for this report"


async def _get_report_with_posting(session: AsyncSession, report_id: UUID) -> Report:
    """Load a report with its job posting relationship."""
    result = await session.execute(
        select(Report).options(selectinload(Report.job_posting)).where(Report.id == report_id)
    )
    report = result.scalar_one_or_none()
    if report is None:
        raise NotFoundError("Report not found")
    return report


def _ensure_verified_employer_for_company(user: User, company_id: UUID) -> None:
    """Ensure the user is a verified employer for the target company."""
    if not user.is_employer or user.employer_company_id != company_id:
        raise ForbiddenError("Employer access required for this company")


async def create_employer_response(
    session: AsyncSession,
    *,
    report_id: UUID,
    payload: CreateEmployerResponseRequest,
    employer: User,
) -> EmployerResponse:
    """Create an employer response and dispute the report when applicable."""
    report = await _get_report_with_posting(session, report_id)
    company_id = report.job_posting.company_id
    _ensure_verified_employer_for_company(employer, company_id)

    existing = await session.execute(
        select(EmployerResponse.id).where(
            EmployerResponse.report_id == report_id,
            EmployerResponse.user_id == employer.id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise ConflictError(_DUPLICATE_RESPONSE_DETAIL)

    previous_status = report.status
    if report.status in _DISPUTE_FROM:
        report.status = ReportStatus.DISPUTED

    response = EmployerResponse(
        report_id=report_id,
        company_id=company_id,
        user_id=employer.id,
        response_text=payload.response_text,
        evidence_urls=payload.evidence_urls,
    )
    session.add(response)
    try:
        await session.flush()
    except IntegrityError as exc:
        await session.rollback()
        raise_conflict_from_integrity_error(exc)

    await log_employer_response_created(
        session,
        actor_user_id=employer.id,
        response_id=response.id,
        report_id=report_id,
        company_id=company_id,
        previous_status=previous_status.value,
        new_status=report.status.value,
    )
    await recalculate_for_job_posting_and_company(session, report.job_posting_id, company_id)
    await sync_company_report_count(session, company_id)
    await session.commit()
    await session.refresh(response)
    return response


async def list_public_employer_responses(
    session: AsyncSession,
    *,
    report_id: UUID,
) -> PublicEmployerResponseListResponse:
    """Return employer responses only when the parent report is publicly visible."""
    report = await _get_report_with_posting(session, report_id)
    if not is_publicly_visible(report.status):
        raise NotFoundError("Report not found")

    total_result = await session.execute(
        select(func.count())
        .select_from(EmployerResponse)
        .where(EmployerResponse.report_id == report_id)
    )
    total = int(total_result.scalar_one())

    result = await session.execute(
        select(EmployerResponse)
        .where(EmployerResponse.report_id == report_id)
        .order_by(EmployerResponse.created_at.asc())
    )
    items = [
        PublicEmployerResponseResponse.model_validate(response)
        for response in result.scalars().all()
    ]
    return PublicEmployerResponseListResponse(items=items, total=total)
