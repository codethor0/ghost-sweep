"""Canonical moderation and score-eligibility rules for reports."""

from sqlalchemy.sql import ColumnElement

from app.models.enums import ReportStatus
from app.models.report import Report

PUBLIC_VISIBLE_STATUSES: frozenset[ReportStatus] = frozenset({ReportStatus.VERIFIED})

SCORE_ELIGIBLE_STATUSES: frozenset[ReportStatus] = frozenset({ReportStatus.VERIFIED})

ACTIVE_DUPLICATE_STATUSES: frozenset[ReportStatus] = frozenset(
    {
        ReportStatus.PENDING,
        ReportStatus.VERIFIED,
        ReportStatus.DISPUTED,
    }
)


def is_publicly_visible(status: ReportStatus) -> bool:
    """Return whether a report may be exposed through public unauthenticated APIs."""
    return status in PUBLIC_VISIBLE_STATUSES


def is_score_eligible(status: ReportStatus) -> bool:
    """Return whether a report may influence public integrity or risk scores."""
    return status in SCORE_ELIGIBLE_STATUSES


def is_active_duplicate_status(status: ReportStatus) -> bool:
    """Return whether a report status blocks materially duplicate submissions."""
    return status in ACTIVE_DUPLICATE_STATUSES


def public_visibility_filter() -> ColumnElement[bool]:
    """SQLAlchemy filter for publicly visible reports."""
    return Report.status.in_(tuple(PUBLIC_VISIBLE_STATUSES))


def score_eligibility_filter() -> ColumnElement[bool]:
    """SQLAlchemy filter for score-eligible reports."""
    return Report.status.in_(tuple(SCORE_ELIGIBLE_STATUSES))


def active_duplicate_filter() -> ColumnElement[bool]:
    """SQLAlchemy filter for active duplicate-blocking report statuses."""
    return Report.status.in_(tuple(ACTIVE_DUPLICATE_STATUSES))
