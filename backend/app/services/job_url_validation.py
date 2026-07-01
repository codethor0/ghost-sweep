"""Offline job posting URL normalization and ATS provider detection."""

from dataclasses import dataclass
from enum import Enum
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

_TRACKING_QUERY_PARAMS = frozenset(
    {
        "utm_source",
        "utm_medium",
        "utm_campaign",
        "utm_term",
        "utm_content",
        "fbclid",
        "gclid",
    }
)

_DANGEROUS_SCHEMES = frozenset({"javascript", "data", "file", "mailto"})

_ALLOWED_SCHEMES = frozenset({"http", "https"})

_CAREER_PATH_MARKERS = (
    "/careers",
    "/jobs",
    "/job/",
    "/job",
    "/openings",
    "/positions",
    "/employment",
    "/join-us",
)

_WORKDAY_HOST_SUFFIXES = (
    "myworkdayjobs.com",
    "workdayjobs.com",
    "myworkdaysite.com",
)

_GREENHOUSE_HOST_SUFFIXES = (
    "greenhouse.io",
    "boards.greenhouse.io",
    "job-boards.greenhouse.io",
)

_LEVER_HOST_SUFFIXES = (
    "lever.co",
    "jobs.lever.co",
)

_ASHBY_HOST_SUFFIXES = (
    "ashbyhq.com",
    "jobs.ashbyhq.com",
)

_SMARTRECRUITERS_HOST_SUFFIXES = (
    "smartrecruiters.com",
    "jobs.smartrecruiters.com",
)


class JobSourceProvider(str, Enum):
    """Known ATS or career-page providers detected from URL structure."""

    WORKDAY = "workday"
    GREENHOUSE = "greenhouse"
    LEVER = "lever"
    ASHBY = "ashby"
    SMARTRECRUITERS = "smartrecruiters"
    COMPANY_CAREERS = "company_careers"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class JobUrlValidationResult:
    """Structured result from offline job URL validation."""

    original_url: str
    normalized_url: str | None
    source_domain: str | None
    provider: JobSourceProvider
    is_valid_url: bool
    is_likely_job_url: bool
    reason: str


def _host_matches_suffix(host: str, suffixes: tuple[str, ...]) -> bool:
    lowered = host.lower()
    for suffix in suffixes:
        if lowered == suffix or lowered.endswith(f".{suffix}"):
            return True
    return False


def _path_has_career_marker(path: str) -> bool:
    lowered = path.lower()
    for marker in _CAREER_PATH_MARKERS:
        if marker.endswith("/"):
            if marker in lowered:
                return True
        elif lowered == marker or lowered.startswith(f"{marker}/"):
            return True
    return False


def _workday_path_looks_like_job(path: str) -> bool:
    lowered = path.lower()
    return "/job/" in lowered or lowered.endswith("/job") or "/jobs/" in lowered


def normalize_job_url(raw_url: str) -> str | None:
    """Normalize a raw job URL string without network access.

    Args:
        raw_url: User-supplied URL text.

    Returns:
        Normalized URL string, or None when the input is not a valid http/https URL.
    """
    trimmed = raw_url.strip()
    if not trimmed:
        return None

    try:
        parts = urlsplit(trimmed)
    except ValueError:
        return None

    scheme = parts.scheme.lower()
    if not scheme:
        return None
    if scheme in _DANGEROUS_SCHEMES:
        return None
    if scheme not in _ALLOWED_SCHEMES:
        return None

    host = parts.hostname
    if not host:
        return None

    normalized_host = host.lower()
    if parts.port is not None:
        default_port = 443 if scheme == "https" else 80
        if parts.port != default_port:
            normalized_host = f"{normalized_host}:{parts.port}"

    filtered_query = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if key.lower() not in _TRACKING_QUERY_PARAMS
    ]
    normalized_query = urlencode(filtered_query, doseq=True)

    normalized_path = parts.path or ""
    if normalized_path != "/" and normalized_path.endswith("/"):
        normalized_path = normalized_path.rstrip("/")

    return urlunsplit(
        (
            scheme,
            normalized_host,
            normalized_path,
            normalized_query,
            "",
        )
    )


def detect_job_source_provider(normalized_url: str) -> JobSourceProvider:
    """Detect the likely ATS or career-page provider from a normalized URL.

    Args:
        normalized_url: Output from ``normalize_job_url``.

    Returns:
        Detected provider enum value.
    """
    parts = urlsplit(normalized_url)
    host = (parts.hostname or "").lower()
    path = parts.path or ""

    if _host_matches_suffix(host, _WORKDAY_HOST_SUFFIXES):
        return JobSourceProvider.WORKDAY
    if host == "workday.com" or host.endswith(".workday.com"):
        if _workday_path_looks_like_job(path):
            return JobSourceProvider.WORKDAY

    if _host_matches_suffix(host, _GREENHOUSE_HOST_SUFFIXES):
        return JobSourceProvider.GREENHOUSE

    if _host_matches_suffix(host, _LEVER_HOST_SUFFIXES):
        return JobSourceProvider.LEVER

    if _host_matches_suffix(host, _ASHBY_HOST_SUFFIXES):
        return JobSourceProvider.ASHBY

    if _host_matches_suffix(host, _SMARTRECRUITERS_HOST_SUFFIXES):
        return JobSourceProvider.SMARTRECRUITERS

    if _path_has_career_marker(path):
        return JobSourceProvider.COMPANY_CAREERS

    return JobSourceProvider.UNKNOWN


def _provider_is_likely_job_url(provider: JobSourceProvider) -> bool:
    return provider != JobSourceProvider.UNKNOWN


def _validation_reason(
    *,
    is_valid_url: bool,
    provider: JobSourceProvider,
    is_likely_job_url: bool,
) -> str:
    if not is_valid_url:
        return "Input is not a valid http or https URL."
    if is_likely_job_url:
        return f"URL structure matches {provider.value} job posting patterns."
    return "URL is structurally valid but does not match known job posting patterns."


def validate_http_https_url(raw_url: str) -> str:
    """Validate a reference URL allows http or https only.

    Used for verification document and evidence URL fields. Rejects dangerous
    schemes such as javascript:, data:, file:, and mailto:.

    Args:
        raw_url: User-supplied URL text.

    Returns:
        Validated URL string (leading and trailing whitespace removed).

    Raises:
        ValueError: When the URL is empty, too long, malformed, or disallowed.
    """
    trimmed = raw_url.strip()
    if not trimmed:
        raise ValueError("URLs must be non-empty strings")
    if len(trimmed) > 2048:
        raise ValueError("URLs must be 2048 characters or fewer")

    try:
        parts = urlsplit(trimmed)
    except ValueError as exc:
        raise ValueError("URLs must be well-formed") from exc

    scheme = parts.scheme.lower()
    if not scheme:
        raise ValueError("URLs must include a scheme")
    if scheme in _DANGEROUS_SCHEMES:
        raise ValueError(f"URL scheme '{scheme}' is not allowed")
    if scheme not in _ALLOWED_SCHEMES:
        raise ValueError("URLs must use http or https")
    if not parts.hostname:
        raise ValueError("URLs must include a host")

    return trimmed


def validate_job_url(raw_url: str) -> JobUrlValidationResult:
    """Validate and classify a raw job URL offline.

    Args:
        raw_url: User-supplied URL text.

    Returns:
        JobUrlValidationResult with normalization and provider classification.
    """
    normalized = normalize_job_url(raw_url)
    if normalized is None:
        return JobUrlValidationResult(
            original_url=raw_url,
            normalized_url=None,
            source_domain=None,
            provider=JobSourceProvider.UNKNOWN,
            is_valid_url=False,
            is_likely_job_url=False,
            reason="Input is not a valid http or https URL.",
        )

    parts = urlsplit(normalized)
    source_domain = parts.hostname
    provider = detect_job_source_provider(normalized)
    is_likely_job_url = _provider_is_likely_job_url(provider)
    reason = _validation_reason(
        is_valid_url=True,
        provider=provider,
        is_likely_job_url=is_likely_job_url,
    )

    return JobUrlValidationResult(
        original_url=raw_url,
        normalized_url=normalized,
        source_domain=source_domain,
        provider=provider,
        is_valid_url=True,
        is_likely_job_url=is_likely_job_url,
        reason=reason,
    )
