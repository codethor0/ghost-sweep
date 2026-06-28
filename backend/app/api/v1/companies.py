"""Company read API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.schemas import CompanyIntegrityScoreResponse, CompanyListResponse, CompanyResponse
from app.services import companies as companies_service

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("", response_model=CompanyListResponse)
async def list_companies(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
) -> CompanyListResponse:
    """Return a paginated list of companies."""
    return await companies_service.list_companies(session, page=page, page_size=page_size)


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> CompanyResponse:
    """Return a company profile."""
    company = await companies_service.get_company(session, company_id)
    return CompanyResponse.model_validate(company)


@router.get("/{company_id}/integrity-score", response_model=CompanyIntegrityScoreResponse)
async def get_company_integrity_score(
    company_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> CompanyIntegrityScoreResponse:
    """Return the current integrity score breakdown for a company."""
    result = await companies_service.get_company_integrity_score(session, company_id)
    return CompanyIntegrityScoreResponse(score=result.score, breakdown=result.breakdown)
