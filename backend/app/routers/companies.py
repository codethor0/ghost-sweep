"""Company routes."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.company import CompanyCreateRequest, CompanyListResponse, CompanyResponse
from app.services import companies as company_service

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("", response_model=CompanyListResponse)
async def list_companies(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
) -> CompanyListResponse:
    """List companies with pagination."""
    return await company_service.list_companies(session, page, page_size)


@router.post("", response_model=CompanyResponse)
async def create_company(
    payload: CompanyCreateRequest,
    session: AsyncSession = Depends(get_db_session),
    _: User = Depends(get_current_user),
) -> CompanyResponse:
    """Create a company profile."""
    return await company_service.create_company(session, payload)
