"""Offline Google Sheet row validation and dry-run import planning."""

from __future__ import annotations

import csv
import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

from app.models.enums import PostingSource, ReportType
from app.services.job_url_validation import (
    JobSourceProvider,
    detect_job_source_provider,
    normalize_job_url,
    validate_http_https_url,
)

_EMAIL_IN_TEXT = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

REQUIRED_SOP_COLUMNS = (
    "review_status",
    "reviewer",
    "reviewed_at",
    "decline_reason_code",
    "duplicate_of",
    "notes",
    "pii_redacted",
    "import_ready",
    "escalation_level",
)

FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "timestamp": ("Timestamp", "timestamp"),
    "job_posting_url": ("Job posting URL", "job posting url", "job_posting_url"),
    "company_name": ("Company name", "company name", "company_name"),
    "job_title": ("Job title", "job title", "job_title"),
    "location": ("Location or remote", "location or remote", "location"),
    "date_seen": ("Date seen", "date seen", "date_seen"),
    "narrative": (
        "Why do you suspect this is a ghost job?",
        "why do you suspect this is a ghost job?",
        "narrative",
    ),
    "company_responded": (
        "Has the company responded?",
        "has the company responded?",
        "company_responded",
    ),
    "consent": ("Consent", "consent"),
    "evidence_links": ("Evidence links", "evidence links", "evidence_links"),
    "optional_contact_email": (
        "Optional contact email",
        "optional contact email",
        "optional_contact_email",
    ),
    "review_status": ("review_status",),
    "reviewer": ("reviewer",),
    "reviewed_at": ("reviewed_at",),
    "decline_reason_code": ("decline_reason_code",),
    "duplicate_of": ("duplicate_of",),
    "notes": ("notes",),
    "pii_redacted": ("pii_redacted",),
    "import_ready": ("import_ready",),
    "escalation_level": ("escalation_level",),
}

_PROVIDER_TO_SOURCE: dict[JobSourceProvider, PostingSource] = {
    JobSourceProvider.WORKDAY: PostingSource.COMPANY_SITE,
    JobSourceProvider.GREENHOUSE: PostingSource.COMPANY_SITE,
    JobSourceProvider.LEVER: PostingSource.COMPANY_SITE,
    JobSourceProvider.ASHBY: PostingSource.COMPANY_SITE,
    JobSourceProvider.SMARTRECRUITERS: PostingSource.COMPANY_SITE,
    JobSourceProvider.COMPANY_CAREERS: PostingSource.COMPANY_SITE,
    JobSourceProvider.UNKNOWN: PostingSource.OTHER,
}


def _normalize_header(header: str) -> str:
    return header.strip().lower()


def resolve_column_map(headers: list[str]) -> dict[str, str]:
    """Map internal field names to CSV header strings present in the file."""
    normalized_headers = {_normalize_header(header): header for header in headers}
    column_map: dict[str, str] = {}
    for field_name, aliases in FIELD_ALIASES.items():
        for alias in aliases:
            key = _normalize_header(alias)
            if key in normalized_headers:
                column_map[field_name] = normalized_headers[key]
                break
    return column_map


def missing_sop_columns(headers: list[str]) -> list[str]:
    """Return SOP column names absent from the CSV header row."""
    normalized_headers = {_normalize_header(header) for header in headers}
    missing: list[str] = []
    for column in REQUIRED_SOP_COLUMNS:
        if column.lower() not in normalized_headers:
            missing.append(column)
    return missing


def _cell(row: dict[str, str], column_map: dict[str, str], field_name: str) -> str:
    header = column_map.get(field_name)
    if header is None:
        return ""
    return (row.get(header) or "").strip()


def _is_blank(value: str) -> bool:
    return not value.strip()


def _consent_checked(value: str) -> bool:
    normalized = value.strip().lower()
    if not normalized:
        return False
    if normalized in {"true", "yes", "x", "checked", "1"}:
        return True
    return "confirm" in normalized and "good faith" in normalized


def _escalation_clear(value: str) -> bool:
    normalized = value.strip().lower()
    return normalized in {"", "none", "n/a", "na"}


def _contains_email(text: str) -> bool:
    return bool(_EMAIL_IN_TEXT.search(text))


def _split_evidence_links(raw: str) -> tuple[list[str], list[str]]:
    if not raw.strip():
        return [], []
    tokens = re.split(r"[\s,;]+", raw.strip())
    valid: list[str] = []
    dropped: list[str] = []
    for token in tokens:
        trimmed = token.strip()
        if not trimmed:
            continue
        try:
            valid.append(validate_http_https_url(trimmed))
        except ValueError:
            dropped.append(trimmed)
    return valid, dropped


def _map_posting_source(normalized_url: str) -> PostingSource:
    provider = detect_job_source_provider(normalized_url)
    return _PROVIDER_TO_SOURCE.get(provider, PostingSource.OTHER)


def _build_description(
    *,
    date_seen: str,
    company_responded: str,
    location: str,
    narrative: str,
    evidence_urls: list[str],
) -> str:
    lines = [
        "[ghost-sweep Sheet import]",
        f"Date seen: {date_seen}",
        f"Company responded (reporter): {company_responded}",
        f"Location: {location}",
        "",
        narrative,
    ]
    if evidence_urls:
        lines.extend(["", "Evidence links (public URLs):"])
        lines.extend(f"- {url}" for url in evidence_urls)
    return "\n".join(lines)


def _row_fingerprint(
    *,
    timestamp: str,
    normalized_url: str | None,
    company_name: str,
    job_title: str,
) -> str:
    payload = "|".join(
        [
            timestamp,
            normalized_url or "",
            company_name.strip().lower(),
            job_title.strip().lower(),
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


@dataclass(frozen=True)
class EligibilityResult:
    """Outcome of Sheet row eligibility checks."""

    eligible: bool
    reason_code: str | None = None
    message: str | None = None


@dataclass(frozen=True)
class DryRunPlan:
    """Planned import actions for one Sheet row (no database writes)."""

    row_number: int
    action: str
    reason_code: str | None
    message: str | None
    company_action: str | None
    company_name: str | None
    company_domain: str | None
    posting_action: str | None
    original_job_url: str | None
    normalized_job_url: str | None
    posting_source: str | None
    report_type: str | None
    description_preview: str | None
    row_fingerprint: str | None
    warnings: tuple[str, ...] = field(default_factory=tuple)
    dropped_evidence_urls: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class DryRunSummary:
    """Aggregate dry-run results."""

    processed: int
    would_import: int
    skipped: int
    plans: tuple[DryRunPlan, ...]
    missing_columns: tuple[str, ...] = field(default_factory=tuple)


def check_eligibility(
    row: dict[str, str],
    column_map: dict[str, str],
) -> EligibilityResult:
    """Return whether a Sheet row passes import eligibility rules."""
    review_status = _cell(row, column_map, "review_status").lower()
    if review_status != "approved_for_import":
        return EligibilityResult(
            eligible=False,
            reason_code="review_status",
            message="review_status must be approved_for_import",
        )

    import_ready = _cell(row, column_map, "import_ready").lower()
    if import_ready != "yes":
        return EligibilityResult(
            eligible=False,
            reason_code="import_ready",
            message="import_ready must be yes",
        )

    pii_redacted = _cell(row, column_map, "pii_redacted").lower()
    if pii_redacted != "yes":
        return EligibilityResult(
            eligible=False,
            reason_code="pii_redacted",
            message="pii_redacted must be yes",
        )

    if not _is_blank(_cell(row, column_map, "decline_reason_code")):
        return EligibilityResult(
            eligible=False,
            reason_code="decline_reason_code",
            message="decline_reason_code must be empty",
        )

    if not _is_blank(_cell(row, column_map, "duplicate_of")):
        return EligibilityResult(
            eligible=False,
            reason_code="duplicate_of",
            message="duplicate_of must be empty",
        )

    if not _escalation_clear(_cell(row, column_map, "escalation_level")):
        return EligibilityResult(
            eligible=False,
            reason_code="escalation_level",
            message="escalation_level must be none or empty",
        )

    if not _consent_checked(_cell(row, column_map, "consent")):
        return EligibilityResult(
            eligible=False,
            reason_code="no_consent",
            message="Consent must be checked",
        )

    job_url = _cell(row, column_map, "job_posting_url")
    if not job_url:
        return EligibilityResult(
            eligible=False,
            reason_code="missing_job_url",
            message="Job posting URL is required",
        )

    company_name = _cell(row, column_map, "company_name")
    if not company_name:
        return EligibilityResult(
            eligible=False,
            reason_code="missing_company_name",
            message="Company name is required",
        )
    if len(company_name) > 255:
        return EligibilityResult(
            eligible=False,
            reason_code="company_name_too_long",
            message="Company name exceeds 255 characters",
        )

    job_title = _cell(row, column_map, "job_title")
    if not job_title:
        return EligibilityResult(
            eligible=False,
            reason_code="missing_job_title",
            message="Job title is required",
        )

    narrative = _cell(row, column_map, "narrative")
    if len(narrative.strip()) < 20:
        return EligibilityResult(
            eligible=False,
            reason_code="narrative_too_short",
            message="Narrative must be at least 20 characters",
        )

    if _contains_email(narrative):
        return EligibilityResult(
            eligible=False,
            reason_code="pii_in_narrative",
            message="Narrative must not contain email addresses",
        )

    normalized = normalize_job_url(job_url)
    if normalized is None:
        return EligibilityResult(
            eligible=False,
            reason_code="invalid_job_url",
            message="Job posting URL is not a valid http or https URL",
        )

    return EligibilityResult(eligible=True)


def plan_row_import(
    row: dict[str, str],
    *,
    column_map: dict[str, str],
    row_number: int,
) -> DryRunPlan:
    """Build a dry-run import plan for one Sheet row."""
    eligibility = check_eligibility(row, column_map)
    if not eligibility.eligible:
        return DryRunPlan(
            row_number=row_number,
            action="skip",
            reason_code=eligibility.reason_code,
            message=eligibility.message,
            company_action=None,
            company_name=None,
            company_domain=None,
            posting_action=None,
            original_job_url=_cell(row, column_map, "job_posting_url") or None,
            normalized_job_url=None,
            posting_source=None,
            report_type=None,
            description_preview=None,
            row_fingerprint=None,
        )

    job_url = _cell(row, column_map, "job_posting_url")
    normalized = normalize_job_url(job_url)
    if normalized is None:
        return DryRunPlan(
            row_number=row_number,
            action="skip",
            reason_code="invalid_job_url",
            message="Job posting URL is not a valid http or https URL",
            company_action=None,
            company_name=None,
            company_domain=None,
            posting_action=None,
            original_job_url=job_url or None,
            normalized_job_url=None,
            posting_source=None,
            report_type=None,
            description_preview=None,
            row_fingerprint=None,
        )

    company_name = _cell(row, column_map, "company_name")
    job_title = _cell(row, column_map, "job_title")
    warnings: list[str] = []
    if len(job_title) > 255:
        warnings.append("job_title_truncated_to_255")

    evidence_raw = _cell(row, column_map, "evidence_links")
    evidence_urls, dropped = _split_evidence_links(evidence_raw)

    description = _build_description(
        date_seen=_cell(row, column_map, "date_seen"),
        company_responded=_cell(row, column_map, "company_responded"),
        location=_cell(row, column_map, "location"),
        narrative=_cell(row, column_map, "narrative"),
        evidence_urls=evidence_urls,
    )

    host = urlsplit(normalized).hostname or ""
    fingerprint = _row_fingerprint(
        timestamp=_cell(row, column_map, "timestamp"),
        normalized_url=normalized,
        company_name=company_name,
        job_title=job_title,
    )

    return DryRunPlan(
        row_number=row_number,
        action="would_import",
        reason_code=None,
        message=None,
        company_action="match_or_create",
        company_name=company_name,
        company_domain=host.lower() if host else None,
        posting_action="match_or_create",
        original_job_url=job_url,
        normalized_job_url=normalized,
        posting_source=_map_posting_source(normalized).value,
        report_type=ReportType.GHOST_JOB.value,
        description_preview=description,
        row_fingerprint=fingerprint,
        warnings=tuple(warnings),
        dropped_evidence_urls=tuple(dropped),
    )


def dry_run_csv(path: Path) -> DryRunSummary:
    """Parse a Sheet CSV export and produce dry-run import plans."""
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            return DryRunSummary(processed=0, would_import=0, skipped=0, plans=())

        headers = list(reader.fieldnames)
        missing = missing_sop_columns(headers)
        column_map = resolve_column_map(headers)
        plans: list[DryRunPlan] = []

        for index, row in enumerate(reader, start=2):
            plans.append(
                plan_row_import(row, column_map=column_map, row_number=index),
            )

    would_import = sum(1 for plan in plans if plan.action == "would_import")
    skipped = sum(1 for plan in plans if plan.action == "skip")
    return DryRunSummary(
        processed=len(plans),
        would_import=would_import,
        skipped=skipped,
        plans=tuple(plans),
        missing_columns=tuple(missing),
    )
