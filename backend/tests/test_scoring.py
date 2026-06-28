"""Scoring algorithm tests."""

from app.services.scoring import ScoringInputs, VerificationStatus, calculate_ghost_risk_score


def test_calculate_ghost_risk_score_with_old_reposted_job_returns_high_risk() -> None:
    """Old reposted jobs with multiple reports should produce a high risk signal."""
    result = calculate_ghost_risk_score(
        ScoringInputs(
            report_count=5,
            reviewed_report_count=2,
            days_since_first_seen=200,
            days_since_last_repost=150,
            duplicate_report_count=2,
            verification_status=VerificationStatus.UNVERIFIED,
        )
    )

    assert result.score >= 0.7
    assert result.confidence > 0.0
    assert "Risk signal" in result.explanation


def test_calculate_ghost_risk_score_with_verified_active_posting_reduces_risk() -> None:
    """Verified active postings should reduce the calculated risk signal."""
    unverified = calculate_ghost_risk_score(
        ScoringInputs(
            report_count=2,
            reviewed_report_count=1,
            days_since_first_seen=60,
            days_since_last_repost=45,
            duplicate_report_count=0,
            verification_status=VerificationStatus.UNVERIFIED,
        )
    )
    verified = calculate_ghost_risk_score(
        ScoringInputs(
            report_count=2,
            reviewed_report_count=1,
            days_since_first_seen=60,
            days_since_last_repost=45,
            duplicate_report_count=0,
            verification_status=VerificationStatus.VERIFIED_ACTIVE,
        )
    )

    assert verified.score < unverified.score
