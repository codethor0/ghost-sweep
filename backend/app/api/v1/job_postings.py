"""Job posting read API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.schemas import JobGhostRiskScoreResponse, JobPostingResponse
from app.services import job_postings as job_postings_service

router = APIRouter(prefix="/job-postings", tags=["job-postings"])


@router.get("/{job_posting_id}", response_model=JobPostingResponse)
async def get_job_posting(
    job_posting_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> JobPostingResponse:
    """Return a job posting profile."""
    posting = await job_postings_service.get_job_posting(session, job_posting_id)
    return JobPostingResponse.model_validate(posting)


@router.get("/{job_posting_id}/risk-score", response_model=JobGhostRiskScoreResponse)
async def get_job_posting_risk_score(
    job_posting_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> JobGhostRiskScoreResponse:
    """Return the current ghost job risk score breakdown for a posting."""
    result = await job_postings_service.get_job_posting_risk_score(session, job_posting_id)
    return JobGhostRiskScoreResponse(score=result.score, breakdown=result.breakdown)
