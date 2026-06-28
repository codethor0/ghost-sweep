"""Pydantic schema validation tests."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.models.enums import ReportStatus, ReportType, VerifiedStatus, VoteValue
from app.schemas import (
    CompanyResponse,
    HealthResponse,
    JobGhostRiskScoreResponse,
    LoginRequest,
    RegisterRequest,
    ReportResponse,
    ScoreBreakdown,
    TokenResponse,
    VoteResponse,
)


def test_health_response_accepts_valid_payload() -> None:
    """Health responses should serialize expected fields."""
    response = HealthResponse(status="ok", service="ghost-sweep")
    assert response.model_dump() == {"status": "ok", "service": "ghost-sweep"}


def test_register_request_rejects_short_password() -> None:
    """Registration passwords must meet minimum length requirements."""
    with pytest.raises(ValidationError):
        RegisterRequest(email="user@example.com", username="valid_user", password="short")


def test_register_request_rejects_invalid_username_pattern() -> None:
    """Registration usernames must match the allowed character pattern."""
    with pytest.raises(ValidationError):
        RegisterRequest(email="user@example.com", username="bad user", password="StrongPass123!")


def test_login_request_accepts_valid_credentials() -> None:
    """Login requests should accept valid identifier and password fields."""
    request = LoginRequest(identifier="user@example.com", password="StrongPass123!")
    assert request.identifier == "user@example.com"


def test_score_breakdown_rejects_out_of_range_score() -> None:
    """Score breakdown totals must remain within the 0 to 100 range."""
    with pytest.raises(ValidationError):
        ScoreBreakdown(score=101.0, breakdown={"posting_age": 25.0})


def test_job_ghost_risk_score_response_accepts_valid_breakdown() -> None:
    """Job ghost risk responses should accept in-range scores and breakdown maps."""
    response = JobGhostRiskScoreResponse(score=72.5, breakdown={"posting_age": 25.0})
    assert response.score == 72.5
    assert response.breakdown["posting_age"] == 25.0


def test_token_response_defaults_to_bearer_type() -> None:
    """Token responses should default to bearer token type."""
    response = TokenResponse(access_token="signed-token", refresh_token="refresh-token")
    assert response.token_type == "bearer"


def test_report_response_accepts_enum_fields() -> None:
    """Report responses should preserve enum values from model attributes."""
    now = datetime.now(tz=UTC)
    response = ReportResponse(
        id=uuid4(),
        job_posting_id=uuid4(),
        reporter_id=uuid4(),
        report_type=ReportType.STALE_POSTING,
        description="Posting remained open for months.",
        status=ReportStatus.PENDING,
        confidence_score=0.5,
        verification_votes=0,
        created_at=now,
        updated_at=now,
    )
    assert response.status == ReportStatus.PENDING


def test_company_response_accepts_integrity_fields() -> None:
    """Company responses should accept integrity and verification fields."""
    now = datetime.now(tz=UTC)
    response = CompanyResponse(
        id=uuid4(),
        name="Example Corp",
        domain="example.com",
        industry="Technology",
        size="100-500",
        locations=["Remote"],
        integrity_score=82.0,
        verified_status=VerifiedStatus.VERIFIED,
        total_postings=10,
        total_hires=6,
        report_count=1,
        created_at=now,
        updated_at=now,
    )
    assert response.verified_status == VerifiedStatus.VERIFIED


def test_vote_response_accepts_vote_value_enum() -> None:
    """Vote responses should preserve vote value enums."""
    response = VoteResponse(
        id=uuid4(),
        report_id=uuid4(),
        user_id=uuid4(),
        vote=VoteValue.UP,
        created_at=datetime.now(tz=UTC),
    )
    assert response.vote == VoteValue.UP


def test_report_response_rejects_invalid_status_value() -> None:
    """Report responses should reject invalid enum values."""
    now = datetime.now(tz=UTC)
    with pytest.raises(ValidationError):
        ReportResponse.model_validate(
            {
                "id": uuid4(),
                "job_posting_id": uuid4(),
                "reporter_id": uuid4(),
                "report_type": ReportType.STALE_POSTING.value,
                "description": "Invalid status test.",
                "status": "not-a-valid-status",
                "confidence_score": 0.5,
                "verification_votes": 0,
                "created_at": now,
                "updated_at": now,
            }
        )
