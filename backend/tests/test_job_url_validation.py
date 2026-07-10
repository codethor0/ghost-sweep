"""Offline job URL validation tests."""

import pytest

from app.services.job_url_validation import (
    JobSourceProvider,
    detect_job_source_provider,
    normalize_job_url,
    validate_http_https_url,
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


def test_validate_http_https_url_accepts_https() -> None:
    """HTTPS URLs with a host should validate."""
    assert validate_http_https_url("https://example.com/proof.pdf") == (
        "https://example.com/proof.pdf"
    )


def test_validate_http_https_url_accepts_http() -> None:
    """HTTP URLs with a host should validate."""
    assert validate_http_https_url("http://example.com/proof") == "http://example.com/proof"


@pytest.mark.parametrize(
    "raw_url",
    [
        "javascript:alert(1)",
        "data:text/plain,hello",
        "file:///etc/passwd",
        "mailto:test@example.com",
        "ftp://example.com/file",
        "",
        "   ",
        "not-a-url",
    ],
)
def test_validate_http_https_url_rejects_invalid_or_dangerous(raw_url: str) -> None:
    """Dangerous schemes and malformed URLs should raise ValueError."""
    with pytest.raises(ValueError):
        validate_http_https_url(raw_url)


@pytest.mark.parametrize(
    "raw_url",
    [
        "https://example.com/jobs/x?UTM_SOURCE=twitter&id=1",
        "https://example.com/jobs/x?Utm_Source=twitter&id=1",
        "https://example.com/jobs/x?utm_source=https://www.lewismuseum.org&id=1",
        "https://example.com/jobs/x?UTM_SOURCE=https://www.lewismuseum.org&id=1",
        "https://example.com/jobs/x?uTm_SoUrCe=https://www.lewismuseum.org&id=1",
        "https://example.com/jobs/x?utm_source=https://www.lewismuseum.org/exhibits&id=1",
        "https://example.com/jobs/x?utm_source=HTTPS://WWW.LEWISMUSEUM.ORG&id=1",
        (
            "https://example.com/jobs/x?utm_source=https://www.lewismuseum.org"
            "&utm_medium=referral&id=1"
        ),
        (
            "https://example.com/jobs/x?utm_source=https://www.lewismuseum.org"
            "&utm_medium=email&utm_campaign=spring-2026&id=1"
        ),
        (
            "https://example.com/jobs/x?utm_source=https://www.lewismuseum.org"
            "&utm_medium=social&utm_campaign=jobs&utm_content=sidebar&utm_term=curator&id=1"
        ),
        (
            "https://example.com/jobs/x?utm_source=https://www.lewismuseum.org"
            "&utm_campaign=newsletter&fbclid=IwAR123abc&gclid=Cj0KCQ&id=1"
        ),
        (
            "https://example.com/jobs/x?id=1&utm_source=https://www.lewismuseum.org"
            "&utm_medium=referral&utm_content=hero-banner"
        ),
    ],
)
def test_normalize_job_url_strips_tracking_params_case_insensitively(raw_url: str) -> None:
    """Tracking params should be stripped regardless of key casing."""
    assert normalize_job_url(raw_url) == "https://example.com/jobs/x?id=1"


def test_normalize_job_url_removes_userinfo() -> None:
    """Credentials embedded in URLs should not survive normalization."""
    normalized = normalize_job_url("https://user:pass@example.com/jobs/x")
    assert normalized == "https://example.com/jobs/x"


def test_normalize_job_url_strips_default_https_port() -> None:
    """Default port 443 should be removed from https URLs."""
    assert normalize_job_url("https://example.com:443/jobs/x") == "https://example.com/jobs/x"


def test_normalize_job_url_strips_default_http_port() -> None:
    """Default port 80 should be removed from http URLs."""
    assert normalize_job_url("http://example.com:80/jobs/x") == "http://example.com/jobs/x"


def test_normalize_job_url_preserves_non_default_port() -> None:
    """Non-default ports should be preserved."""
    assert normalize_job_url("https://example.com:8443/jobs/x") == (
        "https://example.com:8443/jobs/x"
    )


def test_normalize_job_url_preserves_duplicate_query_keys() -> None:
    """Repeated query keys should all be preserved."""
    assert normalize_job_url("https://example.com/jobs/x?id=1&id=2") == (
        "https://example.com/jobs/x?id=1&id=2"
    )


def test_normalize_job_url_preserves_punycode_host() -> None:
    """Punycode hostnames should pass through unchanged."""
    raw = "https://xn--mnchen-jobs-zhb.de/careers/x"
    assert normalize_job_url(raw) == raw


def test_normalize_job_url_drops_query_of_only_tracking_params() -> None:
    """A query containing only tracking params should normalize to no query."""
    raw = "https://example.com/jobs/x?utm_source=a&gclid=b"
    assert normalize_job_url(raw) == "https://example.com/jobs/x"


def test_normalize_job_url_reencodes_query_space_but_keeps_path_encoding() -> None:
    """Percent-encoding in the path survives, but a query space is re-encoded as '+'."""
    raw = "https://example.com/jobs/senior%20engineer?utm_source=x&title=Sr%20Eng"
    assert normalize_job_url(raw) == "https://example.com/jobs/senior%20engineer?title=Sr+Eng"


def test_normalize_job_url_preserves_port_zero() -> None:
    """Port 0 is treated as a non-default port and preserved, not dropped."""
    assert normalize_job_url("https://example.com:0/jobs") == "https://example.com:0/jobs"


def test_normalize_job_url_preserves_consecutive_slashes_in_path() -> None:
    """Consecutive slashes in the path are preserved, not collapsed."""
    raw = "https://example.com//jobs///engineer"
    assert normalize_job_url(raw) == raw


@pytest.mark.parametrize(
    ("raw_url", "expected_provider", "expected_domain"),
    [
        (
            "https://careers-acme.icims.com/jobs/12345/software-engineer/job",
            JobSourceProvider.ICIMS,
            "careers-acme.icims.com",
        ),
        (
            "https://acme.taleo.net/careersection/2/jobdetail.ftl?job=12345",
            JobSourceProvider.TALEO,
            "acme.taleo.net",
        ),
        (
            "https://jobs.jobvite.com/acme/job/oUZbYfwF",
            JobSourceProvider.JOBVITE,
            "jobs.jobvite.com",
        ),
        (
            "https://apply.workable.com/acme/j/ABC123DEF4",
            JobSourceProvider.WORKABLE,
            "apply.workable.com",
        ),
        (
            "https://acme.workable.com/jobs/123456",
            JobSourceProvider.WORKABLE,
            "acme.workable.com",
        ),
        (
            "https://acme.bamboohr.com/careers/42",
            JobSourceProvider.BAMBOOHR,
            "acme.bamboohr.com",
        ),
    ],
)
def test_validate_job_url_detects_hosted_ats_tenant_urls(
    raw_url: str,
    expected_provider: JobSourceProvider,
    expected_domain: str,
) -> None:
    """Hosted ATS tenant URLs should classify with domain and URL preserved."""
    result = validate_job_url(raw_url)
    assert result.provider == expected_provider
    assert result.is_likely_job_url is True
    assert result.source_domain == expected_domain
    assert result.normalized_url == raw_url


@pytest.mark.parametrize(
    "raw_url",
    [
        "https://evilicims.com/postings/1",
        "https://nottaleo.net/postings/1",
        "https://fakejobvite.com/postings/1",
        "https://notworkable.com/postings/1",
        "https://mybamboohr.com/postings/1",
    ],
)
def test_detect_job_source_provider_rejects_lookalike_ats_hosts(raw_url: str) -> None:
    """Hosts that merely end with an ATS name must not match that provider."""
    normalized = normalize_job_url(raw_url)
    assert normalized is not None
    assert detect_job_source_provider(normalized) == JobSourceProvider.UNKNOWN
