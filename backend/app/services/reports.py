"""Report submission service."""

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.exceptions import ValidationError
from app.models.company import Company
from app.models.job_posting import JobPosting
from app.models.report import Report, ReportEvidence
from app.models.user import User
from app.schemas.report import ReportCreateRequest, ReportResponse


async def create_report(
    session: AsyncSession,
    user: User,
    payload: ReportCreateRequest,
) -> ReportResponse:
    """Create an evidence-based integrity report.

    Args:
        session: Database session.
        user: Authenticated submitter.
        payload: Report submission payload.

    Returns:
        ReportResponse: Created report with evidence.

    Raises:
        ValidationError: When required evidence is missing or invalid.
    """
    if not payload.evidence:
        raise ValidationError("At least one evidence item is required")

    company_result = await session.execute(
        select(Company).where(Company.name == payload.company_name.strip())
    )
    company = company_result.scalar_one_or_none()
    if company is None:
        company = Company(name=payload.company_name.strip())
        session.add(company)
        await session.flush()

    posting_url = str(payload.posting_url)
    posting_result = await session.execute(
        select(JobPosting).where(JobPosting.posting_url == posting_url)
    )
    posting = posting_result.scalar_one_or_none()
    now = datetime.now(tz=UTC)
    if posting is None:
        posting = JobPosting(
            company_id=company.id,
            title=payload.job_title.strip(),
            posting_url=posting_url,
            first_seen_at=now,
            last_seen_at=now,
        )
        session.add(posting)
        await session.flush()
    else:
        posting.title = payload.job_title.strip()
        posting.last_seen_at = now

    duplicate_count_result = await session.execute(
        select(func.count())
        .select_from(Report)
        .where(
            Report.job_posting_id == posting.id,
            Report.submitter_id == user.id,
            Report.category == payload.category,
        )
    )
    duplicate_count = int(duplicate_count_result.scalar_one())
    if duplicate_count > 0:
        raise ValidationError("Duplicate report category already submitted for this posting")

    report = Report(
        job_posting_id=posting.id,
        submitter_id=user.id,
        category=payload.category,
        timeline_description=payload.timeline_description.strip(),
    )
    session.add(report)
    await session.flush()

    for evidence in payload.evidence:
        session.add(
            ReportEvidence(
                report_id=report.id,
                evidence_type=evidence.evidence_type,
                source_url=str(evidence.source_url) if evidence.source_url else None,
                description=evidence.description.strip(),
            )
        )

    await session.commit()

    loaded = await session.execute(
        select(Report).options(selectinload(Report.evidence_items)).where(Report.id == report.id)
    )
    saved_report = loaded.scalar_one()
    return ReportResponse.model_validate(saved_report)
