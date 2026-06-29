"""Admin moderation API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, require_admin
from app.models.enums import ReportStatus
from app.models.user import User
from app.schemas import DismissReportRequest, ReportListResponse, ReportResponse
from app.services import moderation as moderation_service

router = APIRouter(prefix="/moderation", tags=["moderation"])


@router.get("/reports", response_model=ReportListResponse)
async def list_reports_for_moderation(
    status: ReportStatus = Query(default=ReportStatus.PENDING),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> ReportListResponse:
    """Return paginated reports filtered by moderation status."""
    return await moderation_service.list_reports_by_status(
        session,
        status=status,
        page=page,
        page_size=page_size,
    )


@router.post("/reports/{report_id}/verify", response_model=ReportResponse)
async def verify_report(
    report_id: UUID,
    session: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> ReportResponse:
    """Mark a report as verified after admin review."""
    report = await moderation_service.verify_report(session, report_id=report_id, admin=admin)
    return ReportResponse.model_validate(report)


@router.post("/reports/{report_id}/dismiss", response_model=ReportResponse)
async def dismiss_report(
    report_id: UUID,
    payload: DismissReportRequest = DismissReportRequest(),
    session: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> ReportResponse:
    """Dismiss a report after admin review."""
    report = await moderation_service.dismiss_report(
        session,
        report_id=report_id,
        admin=admin,
        reason=payload.reason,
    )
    return ReportResponse.model_validate(report)
