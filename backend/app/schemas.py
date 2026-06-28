"""Pydantic request and response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.enums import (
    ClaimStatus,
    PostingSource,
    PostingStatus,
    ReportStatus,
    ReportType,
    SnapshotEntityType,
    VerifiedStatus,
    VoteValue,
)


class HealthResponse(BaseModel):
    """Service health response."""

    status: str
    service: str


class ScoreBreakdown(BaseModel):
    """Named score components returned to clients."""

    score: float = Field(ge=0.0, le=100.0)
    breakdown: dict[str, float]


class JobGhostRiskScoreResponse(ScoreBreakdown):
    """Ghost job risk score for a posting."""


class CompanyIntegrityScoreResponse(ScoreBreakdown):
    """Integrity score for a company."""


class RegisterRequest(BaseModel):
    """User registration payload."""

    email: EmailStr
    username: str = Field(min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9_\-]+$")
    password: str = Field(min_length=12, max_length=128)


class LoginRequest(BaseModel):
    """User login payload."""

    identifier: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=12, max_length=128)


class TokenResponse(BaseModel):
    """JWT access and refresh token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    """Refresh token exchange payload."""

    refresh_token: str = Field(min_length=1, max_length=512)


class LogoutRequest(BaseModel):
    """Logout payload."""

    refresh_token: str = Field(min_length=1, max_length=512)


class UserResponse(BaseModel):
    """Public user profile."""

    id: UUID
    email: EmailStr
    username: str
    reputation_score: float
    report_weight: float
    is_employer: bool
    is_admin: bool
    employer_company_id: UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}


class CompanyResponse(BaseModel):
    """Public company profile."""

    id: UUID
    name: str
    domain: str | None
    industry: str | None
    size: str | None
    locations: list[str]
    integrity_score: float
    verified_status: VerifiedStatus
    total_postings: int
    total_hires: int
    report_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CompanyListResponse(BaseModel):
    """Paginated company list."""

    items: list[CompanyResponse]
    total: int
    page: int
    page_size: int


class JobPostingResponse(BaseModel):
    """Public job posting details."""

    id: UUID
    company_id: UUID
    title: str
    description: str | None
    url: str
    source: PostingSource
    posted_date: datetime | None
    status: PostingStatus
    ghost_risk_score: float
    repost_count: int
    original_posting_id: UUID | None
    detected_at: datetime
    last_seen_at: datetime

    model_config = {"from_attributes": True}


class ReportResponse(BaseModel):
    """Submitted report details."""

    id: UUID
    job_posting_id: UUID
    reporter_id: UUID | None
    report_type: ReportType
    description: str
    status: ReportStatus
    confidence_score: float
    verification_votes: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CreateReportRequest(BaseModel):
    """Report submission payload."""

    job_posting_id: UUID
    report_type: ReportType
    description: str = Field(min_length=20, max_length=5000)


class ReportListResponse(BaseModel):
    """Paginated reports linked to a job posting."""

    items: list[ReportResponse]
    total: int
    page: int
    page_size: int


class CreateVoteRequest(BaseModel):
    """Vote submission payload."""

    vote: VoteValue


class EvidenceFileResponse(BaseModel):
    """Stored evidence file metadata."""

    id: UUID
    report_id: UUID
    file_url: str
    file_type: str
    sha256_hash: str
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class VoteResponse(BaseModel):
    """Vote record."""

    id: UUID
    report_id: UUID
    user_id: UUID
    vote: VoteValue
    created_at: datetime

    model_config = {"from_attributes": True}


class EmployerClaimResponse(BaseModel):
    """Employer claim request."""

    id: UUID
    company_id: UUID
    user_id: UUID
    status: ClaimStatus
    verification_documents: list[str]
    created_at: datetime
    reviewed_at: datetime | None

    model_config = {"from_attributes": True}


class CreateEmployerClaimRequest(BaseModel):
    """Employer claim submission payload."""

    company_id: UUID
    verification_documents: list[str] = Field(min_length=1, max_length=10)

    @field_validator("verification_documents")
    @classmethod
    def validate_verification_documents(cls, documents: list[str]) -> list[str]:
        """Ensure each verification document reference is non-empty and bounded."""
        validated: list[str] = []
        for document in documents:
            trimmed = document.strip()
            if not trimmed:
                raise ValueError("Verification documents must be non-empty strings")
            if len(trimmed) > 2048:
                raise ValueError("Verification documents must be 2048 characters or fewer")
            validated.append(trimmed)
        return validated


class RejectEmployerClaimRequest(BaseModel):
    """Optional rejection reason stored in audit metadata only."""

    reason: str | None = Field(default=None, max_length=2000)


class EmployerClaimListResponse(BaseModel):
    """Paginated employer claim list."""

    items: list[EmployerClaimResponse]
    total: int
    page: int
    page_size: int


class ScoreSnapshotResponse(BaseModel):
    """Historical score snapshot."""

    id: UUID
    entity_type: SnapshotEntityType
    entity_id: UUID
    score: float
    breakdown: dict[str, float]
    created_at: datetime

    model_config = {"from_attributes": True}


class ErrorResponse(BaseModel):
    """Standard API error payload."""

    detail: str
