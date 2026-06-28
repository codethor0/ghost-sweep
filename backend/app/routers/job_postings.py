"""Job posting routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.schemas.job_posting import GhostRiskScoreResponse, JobPostingResponse
from app.services import job_postings as job_posting_service

router = APIRouter(prefix="/job-postings", tags=["job-postings"])


@router.get("/{job_posting_id}", response_model=JobPostingResponse)
async def get_job_posting(
    job_posting_id: int,
    session: AsyncSession = Depends(get_db_session),
) -> JobPostingResponse:
    """Fetch a tracked job posting."""
    return await job_posting_service.get_job_posting(session, job_posting_id)


@router.get("/{job_posting_id}/risk-score", response_model=GhostRiskScoreResponse)
async def get_job_posting_risk_score(
    job_posting_id: int,
    session: AsyncSession = Depends(get_db_session),
) -> GhostRiskScoreResponse:
    """Return a transparent ghost job risk signal for a posting."""
    return await job_posting_service.get_job_posting_risk_score(session, job_posting_id)
