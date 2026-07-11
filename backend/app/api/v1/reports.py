"""Report and vote API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.dependencies import (
    get_current_user,
    get_db,
    get_optional_current_user,
    get_redis,
    get_settings_dependency,
)
from app.models.user import User
from app.redis_client import RedisClient
from app.schemas import (
    CreateEmployerResponseRequest,
    CreateReportRequest,
    CreateVoteRequest,
    EmployerResponseResponse,
    PublicEmployerResponseListResponse,
    PublicReportListResponse,
    PublicReportResponse,
    ReportResponse,
    VoteResponse,
)
from app.services import employer_responses as employer_responses_service
from app.services import reports as reports_service
from app.services import votes as votes_service
from app.services.rate_limit import check_report_submission_rate_limit

router = APIRouter(prefix="/reports", tags=["reports"])


def _client_ip(request: Request) -> str:
    """Return the client IP address for rate limiting."""
    if request.client is None:
        return "unknown"
    return request.client.host


@router.post("", response_model=ReportResponse, status_code=201)
async def create_report(
    payload: CreateReportRequest,
    request: Request,
    session: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
    settings: Settings = Depends(get_settings_dependency),
    current_user: User = Depends(get_current_user),
) -> ReportResponse:
    """Submit an integrity report for a job posting."""
    await check_report_submission_rate_limit(
        redis,
        str(current_user.id),
        _client_ip(request),
        settings,
    )
    report = await reports_service.create_report(
        session,
        payload=payload,
        reporter=current_user,
    )
    return ReportResponse.model_validate(report)


@router.get("/{report_id}", response_model=PublicReportResponse | ReportResponse)
async def get_report(
    report_id: UUID,
    session: AsyncSession = Depends(get_db),
    viewer: User | None = Depends(get_optional_current_user),
) -> PublicReportResponse | ReportResponse:
    """Return a report when visible to the caller."""
    return await reports_service.get_report_response(session, report_id, viewer=viewer)


@router.get("/{report_id}/responses", response_model=PublicEmployerResponseListResponse)
async def list_employer_responses(
    report_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> PublicEmployerResponseListResponse:
    """Return public employer responses linked to a visible report."""
    return await employer_responses_service.list_public_employer_responses(
        session,
        report_id=report_id,
    )


@router.post("/{report_id}/responses", response_model=EmployerResponseResponse, status_code=201)
async def create_employer_response(
    report_id: UUID,
    payload: CreateEmployerResponseRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EmployerResponseResponse:
    """Submit an employer response for a report."""
    response = await employer_responses_service.create_employer_response(
        session,
        report_id=report_id,
        payload=payload,
        employer=current_user,
    )
    return EmployerResponseResponse.model_validate(response)


@router.get("", response_model=PublicReportListResponse)
async def list_reports(
    job_posting_id: UUID = Query(...),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
) -> PublicReportListResponse:
    """List publicly visible reports linked to a job posting."""
    return await reports_service.list_public_reports_for_job_posting(
        session,
        job_posting_id,
        page=page,
        page_size=page_size,
    )


@router.post("/{report_id}/votes", response_model=VoteResponse, status_code=201)
async def create_vote(
    report_id: UUID,
    payload: CreateVoteRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> VoteResponse:
    """Cast a community vote on a report."""
    vote = await votes_service.create_vote(
        session,
        report_id=report_id,
        payload=payload,
        voter=current_user,
    )
    return VoteResponse.model_validate(vote)
