"""Transparent ghost job risk scoring."""

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum


class VerificationStatus(str, Enum):
    """Employer verification state for a posting."""

    UNVERIFIED = "unverified"
    VERIFIED_ACTIVE = "verified_active"
    DISPUTED = "disputed"
    EVIDENCE_REVIEWED = "evidence_reviewed"


@dataclass(frozen=True)
class ScoringInputs:
    """Raw inputs used to compute a risk score."""

    report_count: int
    reviewed_report_count: int
    days_since_first_seen: int
    days_since_last_repost: int
    duplicate_report_count: int
    verification_status: VerificationStatus


@dataclass(frozen=True)
class ScoreComponent:
    """Single weighted component in the risk calculation."""

    name: str
    raw_value: float
    weight: float
    weighted_value: float


@dataclass(frozen=True)
class GhostRiskScore:
    """Fully explained ghost job risk signal."""

    score: float
    confidence: float
    explanation: str
    components: tuple[ScoreComponent, ...]
    calculated_at: datetime


def calculate_ghost_risk_score(inputs: ScoringInputs) -> GhostRiskScore:
    """Calculate a transparent ghost job risk score.

    Args:
        inputs: Normalized scoring inputs for a posting.

    Returns:
        GhostRiskScore: Score with weighted breakdown and confidence.
    """
    report_signal = min(inputs.report_count / 5.0, 1.0)
    reviewed_signal = min(inputs.reviewed_report_count / 3.0, 1.0)
    repost_signal = min(max(inputs.days_since_last_repost - 30, 0) / 120.0, 1.0)
    stale_signal = min(max(inputs.days_since_first_seen - 45, 0) / 180.0, 1.0)
    duplicate_signal = min(inputs.duplicate_report_count / 3.0, 1.0)

    verification_adjustment = {
        VerificationStatus.UNVERIFIED: 0.0,
        VerificationStatus.EVIDENCE_REVIEWED: 0.15,
        VerificationStatus.DISPUTED: -0.2,
        VerificationStatus.VERIFIED_ACTIVE: -0.35,
    }[inputs.verification_status]

    components = (
        ScoreComponent("report_volume", report_signal, 0.30, report_signal * 0.30),
        ScoreComponent("reviewed_reports", reviewed_signal, 0.25, reviewed_signal * 0.25),
        ScoreComponent("repost_age", repost_signal, 0.20, repost_signal * 0.20),
        ScoreComponent("posting_staleness", stale_signal, 0.15, stale_signal * 0.15),
        ScoreComponent("duplicate_reports", duplicate_signal, 0.10, duplicate_signal * 0.10),
    )

    weighted_total = sum(component.weighted_value for component in components)
    adjusted_score = max(0.0, min(1.0, weighted_total + verification_adjustment))

    confidence = min(
        1.0,
        0.35
        + (0.15 if inputs.report_count > 0 else 0.0)
        + (0.25 if inputs.reviewed_report_count > 0 else 0.0)
        + (0.15 if inputs.verification_status != VerificationStatus.UNVERIFIED else 0.0),
    )

    explanation = (
        "Risk signal based on reported user activity, review status, posting age, "
        "repost patterns, and employer verification state. This is not a finding of fraud."
    )

    return GhostRiskScore(
        score=round(adjusted_score, 4),
        confidence=round(confidence, 4),
        explanation=explanation,
        components=components,
        calculated_at=datetime.now(tz=UTC),
    )
