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


class JobSourceProvider(str, Enum):
    """Known ATS or career-page providers detected from URL structure."""

    WORKDAY = "workday"
    GREENHOUSE = "greenhouse"
    LEVER = "lever"
    ASHBY = "ashby"
    SMARTRECRUITERS = "smartrecruiters"
    ICIMS = "icims"
    WORKABLE = "workable"
    BAMBOOHR = "bamboohr"
    TALEO = "taleo"
    JOBVITE = "jobvite"
    COMPANY_CAREERS = "company_careers"
    UNKNOWN = "unknown"


_PROVIDER_HOST_SUFFIXES: tuple[tuple[JobSourceProvider, tuple[str, ...]], ...] = (
    (
        JobSourceProvider.WORKDAY,
        ("myworkdayjobs.com", "workdayjobs.com", "myworkdaysite.com"),
    ),
    (
        JobSourceProvider.GREENHOUSE,
        ("greenhouse.io", "boards.greenhouse.io", "job-boards.greenhouse.io"),
    ),
    (JobSourceProvider.LEVER, ("lever.co", "jobs.lever.co")),
    (JobSourceProvider.ASHBY, ("ashbyhq.com", "jobs.ashbyhq.com")),
    (
        JobSourceProvider.SMARTRECRUITERS,
        ("smartrecruiters.com", "jobs.smartrecruiters.com"),
    ),
    (JobSourceProvider.ICIMS, ("icims.com",)),
    (JobSourceProvider.WORKABLE, ("workable.com",)),
    (JobSourceProvider.BAMBOOHR, ("bamboohr.com",)),
    (JobSourceProvider.TALEO, ("taleo.net",)),
    (JobSourceProvider.JOBVITE, ("jobvite.com",)),
)


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

    if _host_matches_suffix(host, ("workday.com",)):
        if _workday_path_looks_like_job(path):
            return JobSourceProvider.WORKDAY

    for provider, host_suffixes in _PROVIDER_HOST_SUFFIXES:
        if _host_matches_suffix(host, host_suffixes):
            return provider

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


@dataclass(frozen=True)
class EmployerIdentity:
    """Employer identity hints extracted from a hosted ATS or careers URL."""

    provider: JobSourceProvider
    hosted_platform_domain: str | None
    tenant_identifier: str | None
    company_domain_hint: str | None


def _first_path_segment(path: str) -> str | None:
    segments = [segment for segment in path.split("/") if segment]
    if not segments:
        return None
    return segments[0]


def extract_employer_identity(normalized_url: str) -> EmployerIdentity:
    """Extract employer identity hints without inventing a shared ATS domain."""
    parts = urlsplit(normalized_url)
    host = (parts.hostname or "").lower()
    path = parts.path or ""
    provider = detect_job_source_provider(normalized_url)
    tenant: str | None = None
    company_domain_hint: str | None = None

    if provider == JobSourceProvider.GREENHOUSE and host.endswith("greenhouse.io"):
        tenant = _first_path_segment(path)
    elif provider == JobSourceProvider.LEVER and host.endswith("lever.co"):
        tenant = _first_path_segment(path)
    elif provider == JobSourceProvider.ASHBY and host.endswith("ashbyhq.com"):
        tenant = _first_path_segment(path)
    elif provider == JobSourceProvider.SMARTRECRUITERS and host.endswith("smartrecruiters.com"):
        tenant = _first_path_segment(path)
    elif provider == JobSourceProvider.WORKABLE and host.endswith("workable.com"):
        tenant = _first_path_segment(path)
    elif provider == JobSourceProvider.JOBVITE and host.endswith("jobvite.com"):
        tenant = _first_path_segment(path)
    elif provider == JobSourceProvider.BAMBOOHR and host.endswith("bamboohr.com"):
        tenant = host.split(".", maxsplit=1)[0] if host.count(".") >= 2 else None
    elif provider == JobSourceProvider.WORKDAY:
        if host.endswith("myworkdayjobs.com"):
            tenant = host.split(".", maxsplit=1)[0]
        elif host.endswith("myworkdaysite.com"):
            tenant = _first_path_segment(path)
    elif provider == JobSourceProvider.COMPANY_CAREERS:
        company_domain_hint = host

    hosted_platform_domains = {
        JobSourceProvider.GREENHOUSE,
        JobSourceProvider.LEVER,
        JobSourceProvider.ASHBY,
        JobSourceProvider.SMARTRECRUITERS,
        JobSourceProvider.WORKABLE,
        JobSourceProvider.JOBVITE,
        JobSourceProvider.ICIMS,
        JobSourceProvider.TALEO,
        JobSourceProvider.WORKDAY,
        JobSourceProvider.BAMBOOHR,
    }
    hosted_domain = host if provider in hosted_platform_domains else None

    return EmployerIdentity(
        provider=provider,
        hosted_platform_domain=hosted_domain,
        tenant_identifier=tenant,
        company_domain_hint=company_domain_hint,
    )


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
