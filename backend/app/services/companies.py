"""Company read service."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import NotFoundError
from app.models.company import Company
from app.schemas import CompanyListResponse, CompanyResponse
from app.services.scoring import ScoreResult
from app.services.scoring_pipeline import calculate_company_integrity_score_result


async def list_companies(
    session: AsyncSession,
    *,
    page: int,
    page_size: int,
) -> CompanyListResponse:
    """Return a paginated list of companies.

    Args:
        session: Active database session.
        page: One-based page number.
        page_size: Page size capped by the API layer.

    Returns:
        CompanyListResponse: Paginated company records.
    """
    safe_page = max(page, 1)
    safe_page_size = max(page_size, 1)
    offset = (safe_page - 1) * safe_page_size

    total_result = await session.execute(select(func.count()).select_from(Company))
    total = int(total_result.scalar_one())

    result = await session.execute(
        select(Company).order_by(Company.name.asc()).offset(offset).limit(safe_page_size)
    )
    items = [CompanyResponse.model_validate(company) for company in result.scalars().all()]
    return CompanyListResponse(items=items, total=total, page=safe_page, page_size=safe_page_size)


async def get_company(session: AsyncSession, company_id: UUID) -> Company:
    """Load a company by primary key.

    Args:
        session: Active database session.
        company_id: Company UUID.

    Returns:
        Company: Matching company record.

    Raises:
        NotFoundError: When the company does not exist.
    """
    result = await session.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()
    if company is None:
        raise NotFoundError("Company not found")
    return company


async def get_company_integrity_score(session: AsyncSession, company_id: UUID) -> ScoreResult:
    """Calculate the current integrity score breakdown for a company.

    Args:
        session: Active database session.
        company_id: Company UUID.

    Returns:
        ScoreResult: Calculated score and breakdown.

    Raises:
        NotFoundError: When the company does not exist.
    """
    await get_company(session, company_id)
    return await calculate_company_integrity_score_result(session, company_id)
