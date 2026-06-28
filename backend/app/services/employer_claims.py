"""Employer claim submission and review service."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_errors import raise_conflict_from_integrity_error
from app.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.models.company import Company
from app.models.employer_claim import EmployerClaim
from app.models.enums import ClaimStatus
from app.models.user import User
from app.schemas import CreateEmployerClaimRequest, EmployerClaimListResponse, EmployerClaimResponse
from app.services.audit import (
    log_employer_claim_approved,
    log_employer_claim_created,
    log_employer_claim_rejected,
)


async def _get_company_or_404(session: AsyncSession, company_id: UUID) -> Company:
    """Load a company or raise NotFoundError."""
    result = await session.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()
    if company is None:
        raise NotFoundError("Company not found")
    return company


async def _get_claim_or_404(session: AsyncSession, claim_id: UUID) -> EmployerClaim:
    """Load an employer claim or raise NotFoundError."""
    result = await session.execute(select(EmployerClaim).where(EmployerClaim.id == claim_id))
    claim = result.scalar_one_or_none()
    if claim is None:
        raise NotFoundError("Employer claim not found")
    return claim


def _ensure_user_can_view_claim(claim: EmployerClaim, user: User) -> None:
    """Allow claim owners and admins to read a claim."""
    if user.is_admin or claim.user_id == user.id:
        return
    raise ForbiddenError()


async def _ensure_user_can_submit_claim(
    session: AsyncSession,
    user: User,
    company_id: UUID,
) -> None:
    """Validate that a user may submit a new employer claim."""
    if user.is_employer and user.employer_company_id is not None:
        if user.employer_company_id == company_id:
            raise ConflictError("Already an employer for this company")
        raise ConflictError("User is already linked to another company")

    pending_result = await session.execute(
        select(EmployerClaim.id).where(
            EmployerClaim.user_id == user.id,
            EmployerClaim.company_id == company_id,
            EmployerClaim.status == ClaimStatus.PENDING,
        )
    )
    if pending_result.scalar_one_or_none() is not None:
        raise ConflictError("Pending claim already exists for this company")

    approved_result = await session.execute(
        select(EmployerClaim.id).where(
            EmployerClaim.company_id == company_id,
            EmployerClaim.status == ClaimStatus.APPROVED,
        )
    )
    if approved_result.scalar_one_or_none() is not None:
        raise ConflictError("Company already has an approved employer claim")


async def create_claim(
    session: AsyncSession,
    *,
    user: User,
    payload: CreateEmployerClaimRequest,
) -> EmployerClaim:
    """Submit an employer claim for admin review."""
    await _get_company_or_404(session, payload.company_id)
    await _ensure_user_can_submit_claim(session, user, payload.company_id)

    claim = EmployerClaim(
        company_id=payload.company_id,
        user_id=user.id,
        verification_documents=payload.verification_documents,
        status=ClaimStatus.PENDING,
    )
    session.add(claim)
    try:
        await session.flush()
    except IntegrityError as exc:
        await session.rollback()
        raise_conflict_from_integrity_error(exc)

    await log_employer_claim_created(
        session,
        actor_user_id=user.id,
        claim_id=claim.id,
        company_id=payload.company_id,
    )
    await session.commit()
    await session.refresh(claim)
    return claim


async def list_my_claims(
    session: AsyncSession,
    *,
    user: User,
    page: int,
    page_size: int,
) -> EmployerClaimListResponse:
    """Return paginated claims submitted by the current user."""
    safe_page = max(page, 1)
    safe_page_size = max(page_size, 1)
    offset = (safe_page - 1) * safe_page_size

    total_result = await session.execute(
        select(func.count()).select_from(EmployerClaim).where(EmployerClaim.user_id == user.id)
    )
    total = int(total_result.scalar_one())

    result = await session.execute(
        select(EmployerClaim)
        .where(EmployerClaim.user_id == user.id)
        .order_by(EmployerClaim.created_at.desc())
        .offset(offset)
        .limit(safe_page_size)
    )
    items = [EmployerClaimResponse.model_validate(claim) for claim in result.scalars().all()]
    return EmployerClaimListResponse(
        items=items,
        total=total,
        page=safe_page,
        page_size=safe_page_size,
    )


async def list_claims_for_admin(
    session: AsyncSession,
    *,
    status: ClaimStatus,
    page: int,
    page_size: int,
) -> EmployerClaimListResponse:
    """Return paginated claims for admin review."""
    safe_page = max(page, 1)
    safe_page_size = max(page_size, 1)
    offset = (safe_page - 1) * safe_page_size

    total_result = await session.execute(
        select(func.count()).select_from(EmployerClaim).where(EmployerClaim.status == status)
    )
    total = int(total_result.scalar_one())

    result = await session.execute(
        select(EmployerClaim)
        .where(EmployerClaim.status == status)
        .order_by(EmployerClaim.created_at.asc())
        .offset(offset)
        .limit(safe_page_size)
    )
    items = [EmployerClaimResponse.model_validate(claim) for claim in result.scalars().all()]
    return EmployerClaimListResponse(
        items=items,
        total=total,
        page=safe_page,
        page_size=safe_page_size,
    )


async def get_claim(session: AsyncSession, *, claim_id: UUID, user: User) -> EmployerClaim:
    """Return a claim when the caller owns it or is an admin."""
    claim = await _get_claim_or_404(session, claim_id)
    _ensure_user_can_view_claim(claim, user)
    return claim


async def approve_claim(
    session: AsyncSession,
    *,
    claim_id: UUID,
    admin: User,
) -> EmployerClaim:
    """Approve a pending employer claim and link the claimant to the company."""
    claim = await _get_claim_or_404(session, claim_id)
    if claim.status != ClaimStatus.PENDING:
        raise ValidationError("Only pending claims can be approved")

    claimant_result = await session.execute(select(User).where(User.id == claim.user_id))
    claimant = claimant_result.scalar_one()

    if claimant.is_employer and claimant.employer_company_id not in (None, claim.company_id):
        raise ConflictError("User is already linked to another company")

    approved_result = await session.execute(
        select(EmployerClaim.id).where(
            EmployerClaim.company_id == claim.company_id,
            EmployerClaim.status == ClaimStatus.APPROVED,
            EmployerClaim.id != claim.id,
        )
    )
    if approved_result.scalar_one_or_none() is not None:
        raise ConflictError("Company already has an approved employer claim")

    claim.status = ClaimStatus.APPROVED
    claim.reviewed_at = datetime.now(tz=UTC)
    claimant.is_employer = True
    claimant.employer_company_id = claim.company_id

    try:
        await session.flush()
    except IntegrityError as exc:
        await session.rollback()
        raise_conflict_from_integrity_error(exc)

    await log_employer_claim_approved(
        session,
        actor_user_id=admin.id,
        claim_id=claim.id,
        company_id=claim.company_id,
        claimant_user_id=claimant.id,
    )
    await session.commit()
    await session.refresh(claim)
    return claim


async def reject_claim(
    session: AsyncSession,
    *,
    claim_id: UUID,
    admin: User,
    reason: str | None,
) -> EmployerClaim:
    """Reject a pending employer claim."""
    claim = await _get_claim_or_404(session, claim_id)
    if claim.status != ClaimStatus.PENDING:
        raise ValidationError("Only pending claims can be rejected")

    claim.status = ClaimStatus.REJECTED
    claim.reviewed_at = datetime.now(tz=UTC)

    await log_employer_claim_rejected(
        session,
        actor_user_id=admin.id,
        claim_id=claim.id,
        company_id=claim.company_id,
        claimant_user_id=claim.user_id,
        reason=reason,
    )
    await session.commit()
    await session.refresh(claim)
    return claim
