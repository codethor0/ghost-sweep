"""Scoring algorithm tests."""

from app.models.enums import PostingStatus, ReportStatus, VerifiedStatus
from app.services.scoring import (
    CompanyIntegrityInputs,
    JobGhostRiskInputs,
    calculate_company_integrity_score,
    calculate_job_ghost_risk_score,
    count_verified_reports,
)


def test_calculate_job_ghost_risk_score_with_old_reposted_job_returns_high_risk() -> None:
    """Old reposted jobs with verified reports should produce a high risk score."""
    result = calculate_job_ghost_risk_score(
        JobGhostRiskInputs(
            posting_age_days=200,
            repost_count=6,
            company_integrity_score=25.0,
            verified_report_count=4,
            language_risk_signal=0.8,
            no_response_report_count=3,
            fake_interview_report_count=2,
            posting_status=PostingStatus.ACTIVE,
        )
    )
    assert result.score >= 70.0
    assert result.breakdown["posting_age"] == 25.0
    assert result.breakdown["repost_history"] == 15.0


def test_calculate_job_ghost_risk_score_with_filled_posting_reduces_age_and_repost_points() -> None:
    """Filled postings should reduce stale posting and repost contributions."""
    active = calculate_job_ghost_risk_score(
        JobGhostRiskInputs(
            posting_age_days=180,
            repost_count=8,
            company_integrity_score=50.0,
            verified_report_count=0,
            language_risk_signal=0.0,
            no_response_report_count=0,
            fake_interview_report_count=0,
            posting_status=PostingStatus.ACTIVE,
        )
    )
    filled = calculate_job_ghost_risk_score(
        JobGhostRiskInputs(
            posting_age_days=180,
            repost_count=8,
            company_integrity_score=50.0,
            verified_report_count=0,
            language_risk_signal=0.0,
            no_response_report_count=0,
            fake_interview_report_count=0,
            posting_status=PostingStatus.FILLED,
        )
    )
    assert filled.score < active.score


def test_calculate_job_ghost_risk_score_with_disputed_posting_reduces_verified_report_points() -> (
    None
):
    """Disputed postings should reduce verified report evidence to 50 percent."""
    active = calculate_job_ghost_risk_score(
        JobGhostRiskInputs(
            posting_age_days=0,
            repost_count=0,
            company_integrity_score=50.0,
            verified_report_count=5,
            language_risk_signal=0.0,
            no_response_report_count=0,
            fake_interview_report_count=0,
            posting_status=PostingStatus.ACTIVE,
        )
    )
    disputed = calculate_job_ghost_risk_score(
        JobGhostRiskInputs(
            posting_age_days=0,
            repost_count=0,
            company_integrity_score=50.0,
            verified_report_count=5,
            language_risk_signal=0.0,
            no_response_report_count=0,
            fake_interview_report_count=0,
            posting_status=PostingStatus.DISPUTED,
        )
    )
    assert active.breakdown["verified_report_evidence"] == 15.0
    assert disputed.breakdown["verified_report_evidence"] == 7.5
    assert disputed.score < active.score


def test_calculate_job_ghost_risk_score_with_no_signals_returns_low_score() -> None:
    """New postings without reports should remain near the low end."""
    result = calculate_job_ghost_risk_score(
        JobGhostRiskInputs(
            posting_age_days=0,
            repost_count=0,
            company_integrity_score=90.0,
            verified_report_count=0,
            language_risk_signal=0.0,
            no_response_report_count=0,
            fake_interview_report_count=0,
            posting_status=PostingStatus.ACTIVE,
        )
    )
    assert result.score <= 10.0


def test_calculate_job_ghost_risk_score_clamps_output_to_100() -> None:
    """Risk scores must never exceed 100."""
    result = calculate_job_ghost_risk_score(
        JobGhostRiskInputs(
            posting_age_days=1000,
            repost_count=100,
            company_integrity_score=0.0,
            verified_report_count=100,
            language_risk_signal=1.0,
            no_response_report_count=100,
            fake_interview_report_count=100,
            posting_status=PostingStatus.SUSPECTED_GHOST,
        )
    )
    assert result.score == 100.0


def test_calculate_job_ghost_risk_score_with_high_company_integrity_reduces_risk() -> None:
    """Strong company integrity should reduce posting risk through company history."""
    low_integrity = calculate_job_ghost_risk_score(
        JobGhostRiskInputs(
            posting_age_days=60,
            repost_count=1,
            company_integrity_score=10.0,
            verified_report_count=0,
            language_risk_signal=0.0,
            no_response_report_count=0,
            fake_interview_report_count=0,
            posting_status=PostingStatus.ACTIVE,
        )
    )
    high_integrity = calculate_job_ghost_risk_score(
        JobGhostRiskInputs(
            posting_age_days=60,
            repost_count=1,
            company_integrity_score=95.0,
            verified_report_count=0,
            language_risk_signal=0.0,
            no_response_report_count=0,
            fake_interview_report_count=0,
            posting_status=PostingStatus.ACTIVE,
        )
    )
    assert high_integrity.score < low_integrity.score


def test_calculate_company_integrity_score_with_zero_postings_avoids_division_errors() -> None:
    """Companies with zero postings must not raise division errors."""
    result = calculate_company_integrity_score(
        CompanyIntegrityInputs(
            total_postings=0,
            total_hires=0,
            verified_report_count=0,
            total_reports=0,
            employer_response_count=0,
            verified_status=VerifiedStatus.UNVERIFIED,
            average_days_to_fill=None,
            recruiter_follow_through_rate=0.0,
            correction_count=0,
        )
    )
    assert 0.0 <= result.score <= 100.0
    assert result.breakdown["post_to_hire_ratio"] == 0.0
    assert result.breakdown["report_ratio"] == 20.0


def test_calculate_company_integrity_score_with_strong_hiring_history_returns_high_score() -> None:
    """Healthy post-to-hire ratios should increase integrity scores."""
    result = calculate_company_integrity_score(
        CompanyIntegrityInputs(
            total_postings=20,
            total_hires=15,
            verified_report_count=0,
            total_reports=1,
            employer_response_count=1,
            verified_status=VerifiedStatus.VERIFIED,
            average_days_to_fill=30.0,
            recruiter_follow_through_rate=0.9,
            correction_count=2,
        )
    )
    assert result.score >= 80.0
    assert result.breakdown["post_to_hire_ratio"] == 18.75


def test_calculate_company_integrity_score_with_verified_status_adds_full_verification_points() -> (
    None
):
    """Verified companies receive the full verification allocation."""
    result = calculate_company_integrity_score(
        CompanyIntegrityInputs(
            total_postings=5,
            total_hires=2,
            verified_report_count=0,
            total_reports=0,
            employer_response_count=0,
            verified_status=VerifiedStatus.VERIFIED,
            average_days_to_fill=45.0,
            recruiter_follow_through_rate=0.5,
            correction_count=0,
        )
    )
    assert result.breakdown["verification_status"] == 15.0


def test_calculate_company_integrity_score_with_disputed_status_reduces_verification_points() -> (
    None
):
    """Disputed companies receive reduced verification credit."""
    verified = calculate_company_integrity_score(
        CompanyIntegrityInputs(
            total_postings=5,
            total_hires=2,
            verified_report_count=0,
            total_reports=0,
            employer_response_count=0,
            verified_status=VerifiedStatus.VERIFIED,
            average_days_to_fill=45.0,
            recruiter_follow_through_rate=0.5,
            correction_count=0,
        )
    )
    disputed = calculate_company_integrity_score(
        CompanyIntegrityInputs(
            total_postings=5,
            total_hires=2,
            verified_report_count=0,
            total_reports=0,
            employer_response_count=0,
            verified_status=VerifiedStatus.DISPUTED,
            average_days_to_fill=45.0,
            recruiter_follow_through_rate=0.5,
            correction_count=0,
        )
    )
    assert disputed.score < verified.score


def test_calculate_company_integrity_score_clamps_output_to_100() -> None:
    """Integrity scores must never exceed 100."""
    result = calculate_company_integrity_score(
        CompanyIntegrityInputs(
            total_postings=10,
            total_hires=10,
            verified_report_count=0,
            total_reports=0,
            employer_response_count=10,
            verified_status=VerifiedStatus.VERIFIED,
            average_days_to_fill=0.0,
            recruiter_follow_through_rate=1.0,
            correction_count=10,
        )
    )
    assert result.score == 100.0


def test_calculate_company_integrity_score_with_high_report_ratio_reduces_score() -> None:
    """Higher verified report ratios should reduce integrity scores."""
    low_reports = calculate_company_integrity_score(
        CompanyIntegrityInputs(
            total_postings=20,
            total_hires=10,
            verified_report_count=1,
            total_reports=1,
            employer_response_count=1,
            verified_status=VerifiedStatus.UNVERIFIED,
            average_days_to_fill=60.0,
            recruiter_follow_through_rate=0.5,
            correction_count=0,
        )
    )
    high_reports = calculate_company_integrity_score(
        CompanyIntegrityInputs(
            total_postings=20,
            total_hires=10,
            verified_report_count=10,
            total_reports=10,
            employer_response_count=1,
            verified_status=VerifiedStatus.UNVERIFIED,
            average_days_to_fill=60.0,
            recruiter_follow_through_rate=0.5,
            correction_count=0,
        )
    )
    assert high_reports.score < low_reports.score


def test_count_verified_reports_returns_only_verified_statuses() -> None:
    """Verified report counting must ignore pending and dismissed reports."""
    statuses = [
        ReportStatus.PENDING,
        ReportStatus.VERIFIED,
        ReportStatus.DISMISSED,
        ReportStatus.VERIFIED,
        ReportStatus.DISPUTED,
    ]
    assert count_verified_reports(statuses) == 2
