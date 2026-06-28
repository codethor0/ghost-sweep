"""Pydantic request and response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

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
    """JWT access token response."""

    access_token: str
    token_type: str = "bearer"


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
