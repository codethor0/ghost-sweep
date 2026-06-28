"""Transparent integrity scoring for job postings and companies."""

from dataclasses import dataclass

from app.models.enums import PostingStatus, ReportStatus, VerifiedStatus


@dataclass(frozen=True)
class JobGhostRiskInputs:
    """Raw inputs for job ghost risk scoring."""

    posting_age_days: int
    repost_count: int
    company_integrity_score: float
    verified_report_count: int
    language_risk_signal: float
    no_response_report_count: int
    fake_interview_report_count: int
    posting_status: PostingStatus


@dataclass(frozen=True)
class CompanyIntegrityInputs:
    """Raw inputs for company integrity scoring."""

    total_postings: int
    total_hires: int
    verified_report_count: int
    total_reports: int
    employer_response_count: int
    verified_status: VerifiedStatus
    average_days_to_fill: float | None
    recruiter_follow_through_rate: float
    correction_count: int


@dataclass(frozen=True)
class ScoreResult:
    """Score output with component breakdown."""

    score: float
    breakdown: dict[str, float]


def _clamp(value: float, minimum: float, maximum: float) -> float:
    """Clamp a numeric value to an inclusive range."""
    return max(minimum, min(maximum, value))


def _safe_ratio(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Compute a ratio while avoiding division by zero."""
    if denominator <= 0:
        return default
    return numerator / denominator


def _scale_to_max(raw: float, max_points: float) -> float:
    """Scale a 0..1 signal to a point allocation."""
    return _clamp(raw, 0.0, 1.0) * max_points


def calculate_job_ghost_risk_score(inputs: JobGhostRiskInputs) -> ScoreResult:
    """Calculate a job ghost risk score from 0 to 100.

    Higher scores indicate stronger risk signals. This is not a legal finding.

    Args:
        inputs: Normalized posting and report signals.

    Returns:
        ScoreResult: Total score and named breakdown components.
    """
    posting_age_points = _scale_to_max(min(inputs.posting_age_days / 180.0, 1.0), 25.0)
    repost_points = _scale_to_max(min(inputs.repost_count / 8.0, 1.0), 20.0)
    company_history_points = _scale_to_max(
        (100.0 - _clamp(inputs.company_integrity_score, 0.0, 100.0)) / 100.0,
        15.0,
    )
    verified_report_points = _scale_to_max(min(inputs.verified_report_count / 5.0, 1.0), 15.0)
    language_points = _scale_to_max(_clamp(inputs.language_risk_signal, 0.0, 1.0), 10.0)
    no_response_points = _scale_to_max(min(inputs.no_response_report_count / 4.0, 1.0), 10.0)
    interview_points = _scale_to_max(min(inputs.fake_interview_report_count / 3.0, 1.0), 5.0)

    if inputs.posting_status == PostingStatus.FILLED:
        posting_age_points *= 0.25
        repost_points *= 0.25
    elif inputs.posting_status == PostingStatus.DISPUTED:
        verified_report_points *= 0.5

    breakdown = {
        "posting_age": round(posting_age_points, 2),
        "repost_history": round(repost_points, 2),
        "company_history": round(company_history_points, 2),
        "verified_report_evidence": round(verified_report_points, 2),
        "language_risk_signals": round(language_points, 2),
        "no_response_reports": round(no_response_points, 2),
        "interview_without_offer_pattern": round(interview_points, 2),
    }
    total = _clamp(sum(breakdown.values()), 0.0, 100.0)
    return ScoreResult(score=round(total, 2), breakdown=breakdown)


def calculate_company_integrity_score(inputs: CompanyIntegrityInputs) -> ScoreResult:
    """Calculate a company integrity score from 0 to 100.

    Higher scores indicate stronger integrity signals based on available evidence.

    Args:
        inputs: Normalized company activity and response signals.

    Returns:
        ScoreResult: Total score and named breakdown components.
    """
    hire_ratio = _safe_ratio(float(inputs.total_hires), float(inputs.total_postings), default=0.0)
    post_to_hire_points = _scale_to_max(min(hire_ratio, 1.0), 25.0)

    report_ratio = _safe_ratio(
        float(inputs.verified_report_count), float(inputs.total_postings), 0.0
    )
    report_points = _scale_to_max(max(1.0 - min(report_ratio, 1.0), 0.0), 20.0)

    response_rate = _safe_ratio(
        float(inputs.employer_response_count),
        float(max(inputs.total_reports, 1)),
        default=0.0,
    )
    response_points = _scale_to_max(min(response_rate, 1.0), 15.0)

    verification_points = {
        VerifiedStatus.VERIFIED: 15.0,
        VerifiedStatus.UNVERIFIED: 7.5,
        VerifiedStatus.DISPUTED: 3.0,
    }[inputs.verified_status]

    if inputs.average_days_to_fill is None:
        fill_points = 5.0
    else:
        fill_points = _scale_to_max(
            max(1.0 - min(inputs.average_days_to_fill / 120.0, 1.0), 0.0), 10.0
        )

    follow_through_points = _scale_to_max(
        _clamp(inputs.recruiter_follow_through_rate, 0.0, 1.0),
        10.0,
    )
    correction_points = _scale_to_max(min(inputs.correction_count / 5.0, 1.0), 5.0)

    breakdown = {
        "post_to_hire_ratio": round(post_to_hire_points, 2),
        "report_ratio": round(report_points, 2),
        "response_rate": round(response_points, 2),
        "verification_status": round(verification_points, 2),
        "average_time_to_fill": round(fill_points, 2),
        "recruiter_follow_through": round(follow_through_points, 2),
        "correction_history": round(correction_points, 2),
    }
    total = _clamp(sum(breakdown.values()), 0.0, 100.0)
    return ScoreResult(score=round(total, 2), breakdown=breakdown)


def count_verified_reports(report_statuses: list[ReportStatus]) -> int:
    """Count reports with verified moderation status.

    Args:
        report_statuses: Report statuses linked to an entity.

    Returns:
        int: Number of verified reports.
    """
    return sum(1 for status in report_statuses if status == ReportStatus.VERIFIED)
