"""Company query service."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.schemas.company import CompanyCreateRequest, CompanyListResponse, CompanyResponse


async def list_companies(
    session: AsyncSession,
    page: int,
    page_size: int,
) -> CompanyListResponse:
    """Return a paginated list of companies.

    Args:
        session: Database session.
        page: One-based page number.
        page_size: Number of records per page.

    Returns:
        CompanyListResponse: Paginated company results.
    """
    total_result = await session.execute(select(func.count()).select_from(Company))
    total = int(total_result.scalar_one())

    offset = (page - 1) * page_size
    result = await session.execute(
        select(Company).order_by(Company.name.asc()).offset(offset).limit(page_size)
    )
    items = [CompanyResponse.model_validate(company) for company in result.scalars().all()]
    return CompanyListResponse(items=items, total=total, page=page, page_size=page_size)


async def create_company(session: AsyncSession, payload: CompanyCreateRequest) -> CompanyResponse:
    """Create a company profile.

    Args:
        session: Database session.
        payload: Company creation payload.

    Returns:
        CompanyResponse: Created company record.
    """
    company = Company(name=payload.name.strip(), website=payload.website)
    session.add(company)
    await session.commit()
    await session.refresh(company)
    return CompanyResponse.model_validate(company)
