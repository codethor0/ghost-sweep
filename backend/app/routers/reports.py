"""Report routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.report import ReportCreateRequest, ReportResponse
from app.services import reports as report_service

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("", response_model=ReportResponse)
async def submit_report(
    payload: ReportCreateRequest,
    session: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_current_user),
) -> ReportResponse:
    """Submit an evidence-based integrity report."""
    return await report_service.create_report(session, user, payload)
