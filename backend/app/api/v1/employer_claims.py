"""Employer claim API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db, require_admin
from app.models.enums import ClaimStatus
from app.models.user import User
from app.schemas import (
    CreateEmployerClaimRequest,
    EmployerClaimListResponse,
    EmployerClaimResponse,
    RejectEmployerClaimRequest,
)
from app.services import employer_claims as employer_claims_service

router = APIRouter(prefix="/employer-claims", tags=["employer-claims"])


@router.post("", response_model=EmployerClaimResponse, status_code=201)
async def submit_employer_claim(
    payload: CreateEmployerClaimRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EmployerClaimResponse:
    """Submit an employer claim for admin review."""
    claim = await employer_claims_service.create_claim(
        session,
        user=current_user,
        payload=payload,
    )
    return EmployerClaimResponse.model_validate(claim)


@router.get("/me", response_model=EmployerClaimListResponse)
async def list_my_employer_claims(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EmployerClaimListResponse:
    """Return claims submitted by the authenticated user."""
    return await employer_claims_service.list_my_claims(
        session,
        user=current_user,
        page=page,
        page_size=page_size,
    )


@router.get("", response_model=EmployerClaimListResponse)
async def list_employer_claims_for_admin(
    status: ClaimStatus = Query(default=ClaimStatus.PENDING),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> EmployerClaimListResponse:
    """Return paginated employer claims for admin review."""
    return await employer_claims_service.list_claims_for_admin(
        session,
        status=status,
        page=page,
        page_size=page_size,
    )


@router.get("/{claim_id}", response_model=EmployerClaimResponse)
async def get_employer_claim(
    claim_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EmployerClaimResponse:
    """Return an employer claim owned by the caller or visible to admins."""
    claim = await employer_claims_service.get_claim(session, claim_id=claim_id, user=current_user)
    return EmployerClaimResponse.model_validate(claim)


@router.post("/{claim_id}/approve", response_model=EmployerClaimResponse)
async def approve_employer_claim(
    claim_id: UUID,
    session: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> EmployerClaimResponse:
    """Approve a pending employer claim."""
    claim = await employer_claims_service.approve_claim(session, claim_id=claim_id, admin=admin)
    return EmployerClaimResponse.model_validate(claim)


@router.post("/{claim_id}/reject", response_model=EmployerClaimResponse)
async def reject_employer_claim(
    claim_id: UUID,
    payload: RejectEmployerClaimRequest = RejectEmployerClaimRequest(),
    session: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
) -> EmployerClaimResponse:
    """Reject a pending employer claim."""
    claim = await employer_claims_service.reject_claim(
        session,
        claim_id=claim_id,
        admin=admin,
        reason=payload.reason,
    )
    return EmployerClaimResponse.model_validate(claim)
