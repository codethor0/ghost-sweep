"""Offline job URL validation tests."""

from app.services.job_url_validation import (
    JobSourceProvider,
    detect_job_source_provider,
    normalize_job_url,
    validate_job_url,
)


def test_validate_job_url_detects_workday_url() -> None:
    """Workday career site URLs should be classified as Workday job URLs."""
    raw = "https://acme.wd5.myworkdayjobs.com/en-US/Careers/job/Engineer_R12345"
    result = validate_job_url(raw)
    assert result.is_valid_url is True
    assert result.is_likely_job_url is True
    assert result.provider == JobSourceProvider.WORKDAY
    assert result.source_domain == "acme.wd5.myworkdayjobs.com"
    assert result.normalized_url == raw


def test_validate_job_url_detects_greenhouse_url() -> None:
    """Greenhouse board URLs should be classified as Greenhouse job URLs."""
    raw = "https://boards.greenhouse.io/acme/jobs/1234567"
    result = validate_job_url(raw)
    assert result.provider == JobSourceProvider.GREENHOUSE
    assert result.is_likely_job_url is True
    assert result.source_domain == "boards.greenhouse.io"


def test_validate_job_url_detects_lever_url() -> None:
    """Lever hosted job URLs should be classified as Lever job URLs."""
    raw = "https://jobs.lever.co/acme/software-engineer-123"
    result = validate_job_url(raw)
    assert result.provider == JobSourceProvider.LEVER
    assert result.is_likely_job_url is True
    assert result.source_domain == "jobs.lever.co"


def test_validate_job_url_detects_ashby_url() -> None:
    """Ashby hosted job URLs should be classified as Ashby job URLs."""
    raw = "https://jobs.ashbyhq.com/acme/11111111-2222-3333-4444-555555555555"
    result = validate_job_url(raw)
    assert result.provider == JobSourceProvider.ASHBY
    assert result.is_likely_job_url is True
    assert result.source_domain == "jobs.ashbyhq.com"


def test_validate_job_url_detects_smartrecruiters_url() -> None:
    """SmartRecruiters hosted job URLs should be classified correctly."""
    raw = "https://jobs.smartrecruiters.com/AcmeCorp/743999887654321"
    result = validate_job_url(raw)
    assert result.provider == JobSourceProvider.SMARTRECRUITERS
    assert result.is_likely_job_url is True
    assert result.source_domain == "jobs.smartrecruiters.com"


def test_validate_job_url_detects_generic_company_careers_url() -> None:
    """Company career page paths should be classified as company careers."""
    raw = "https://www.example.com/careers/software-engineer"
    result = validate_job_url(raw)
    assert result.provider == JobSourceProvider.COMPANY_CAREERS
    assert result.is_likely_job_url is True
    assert result.source_domain == "www.example.com"


def test_validate_job_url_unknown_valid_url_is_not_likely_job() -> None:
    """Valid non-job URLs should remain valid but not likely job URLs."""
    raw = "https://www.example.com/about/team"
    result = validate_job_url(raw)
    assert result.is_valid_url is True
    assert result.is_likely_job_url is False
    assert result.provider == JobSourceProvider.UNKNOWN


def test_validate_job_url_invalid_url_is_rejected() -> None:
    """Non-URL input should be rejected."""
    result = validate_job_url("not-a-url")
    assert result.is_valid_url is False
    assert result.is_likely_job_url is False
    assert result.normalized_url is None
    assert result.provider == JobSourceProvider.UNKNOWN


def test_validate_job_url_rejects_dangerous_schemes() -> None:
    """Dangerous URL schemes should be rejected."""
    for raw in (
        "javascript:alert(1)",
        "data:text/html,hello",
        "file:///etc/passwd",
        "mailto:jobs@example.com",
    ):
        result = validate_job_url(raw)
        assert result.is_valid_url is False
        assert result.normalized_url is None


def test_normalize_job_url_removes_tracking_params() -> None:
    """Known tracking query params should be stripped during normalization."""
    raw = (
        "https://example.com/jobs/engineer"
        "?id=123&utm_source=twitter&utm_medium=social&fbclid=abc&gclid=xyz"
    )
    normalized = normalize_job_url(raw)
    assert normalized == "https://example.com/jobs/engineer?id=123"


def test_normalize_job_url_preserves_meaningful_query_params() -> None:
    """Non-tracking query params should be preserved."""
    raw = "https://example.com/jobs/engineer?gh_jid=1234567&mode=apply"
    normalized = normalize_job_url(raw)
    assert normalized is not None
    assert "gh_jid=1234567" in normalized
    assert "mode=apply" in normalized


def test_normalize_job_url_removes_fragments() -> None:
    """URL fragments should be removed during normalization."""
    raw = "https://example.com/careers/engineer#apply-now"
    normalized = normalize_job_url(raw)
    assert normalized == "https://example.com/careers/engineer"


def test_normalize_job_url_lowercases_host() -> None:
    """Hostnames should be lowercased during normalization."""
    raw = "HTTPS://WWW.Example.COM/jobs/engineer"
    normalized = normalize_job_url(raw)
    assert normalized == "https://www.example.com/jobs/engineer"


def test_normalize_job_url_trims_whitespace() -> None:
    """Leading and trailing whitespace should be trimmed."""
    raw = "  https://example.com/jobs/engineer  "
    normalized = normalize_job_url(raw)
    assert normalized == "https://example.com/jobs/engineer"


def test_normalize_job_url_rejects_empty_string() -> None:
    """Empty strings should not normalize to a URL."""
    assert normalize_job_url("") is None
    assert normalize_job_url("   ") is None


def test_detect_job_source_provider_workday_workdaysite_host() -> None:
    """Workday myworkdaysite hosts should map to Workday."""
    normalized = normalize_job_url("https://wd3.myworkdaysite.com/en-US/Acme/jobs")
    assert normalized is not None
    assert detect_job_source_provider(normalized) == JobSourceProvider.WORKDAY


def test_normalize_job_url_removes_trailing_slash() -> None:
    """Trailing slashes on non-root paths should be removed."""
    raw = "https://example.com/careers/engineer/"
    normalized = normalize_job_url(raw)
    assert normalized == "https://example.com/careers/engineer"
