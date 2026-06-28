"""Shared enumeration types for ORM models."""

from enum import Enum


class VerifiedStatus(str, Enum):
    """Company verification state."""

    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    DISPUTED = "disputed"


class PostingSource(str, Enum):
    """Origin of a tracked job posting."""

    LINKEDIN = "linkedin"
    INDEED = "indeed"
    GLASSDOOR = "glassdoor"
    COMPANY_SITE = "company_site"
    OTHER = "other"


class PostingStatus(str, Enum):
    """Lifecycle state of a job posting."""

    ACTIVE = "active"
    FILLED = "filled"
    REMOVED = "removed"
    SUSPECTED_GHOST = "suspected_ghost"
    DISPUTED = "disputed"


class ReportType(str, Enum):
    """Category of integrity report."""

    GHOST_JOB = "ghost_job"
    NO_RESPONSE = "no_response"
    SCAM = "scam"
    DATA_HARVEST = "data_harvest"
    REPOST_LOOP = "repost_loop"
    STALE_POSTING = "stale_posting"
    FAKE_INTERVIEW = "fake_interview"


class ReportStatus(str, Enum):
    """Moderation state of a report."""

    PENDING = "pending"
    VERIFIED = "verified"
    DISMISSED = "dismissed"
    DISPUTED = "disputed"


class ClaimStatus(str, Enum):
    """Employer claim review state."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class VoteValue(str, Enum):
    """Community vote direction on a report."""

    UP = "up"
    DOWN = "down"


class SnapshotEntityType(str, Enum):
    """Entity type stored in a score snapshot."""

    COMPANY = "company"
    JOB_POSTING = "job_posting"
