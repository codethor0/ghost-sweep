"""Dry-run Google Sheet import planning tests."""

from pathlib import Path

from app.services.sheet_import import (
    check_eligibility,
    dry_run_csv,
    missing_sop_columns,
    plan_row_import,
    resolve_column_map,
)

HEADERS = [
    "Timestamp",
    "Job posting URL",
    "Company name",
    "Job title",
    "Location or remote",
    "Date seen",
    "Why do you suspect this is a ghost job?",
    "Has the company responded?",
    "Consent",
    "Evidence links",
    "Optional contact email",
    "review_status",
    "reviewer",
    "reviewed_at",
    "decline_reason_code",
    "duplicate_of",
    "notes",
    "pii_redacted",
    "import_ready",
    "escalation_level",
]


def _eligible_row(**overrides: str) -> dict[str, str]:
    base = {
        "Timestamp": "2026-07-01 12:00:00",
        "Job posting URL": "https://boards.greenhouse.io/acme/jobs/1234567",
        "Company name": "Acme Corp",
        "Job title": "Software Engineer",
        "Location or remote": "Remote",
        "Date seen": "2026-06-30",
        "Why do you suspect this is a ghost job?": (
            "Listing has been open for months with no hiring updates."
        ),
        "Has the company responded?": "No",
        "Consent": "I confirm this submission is made in good faith.",
        "Evidence links": "https://example.com/archive",
        "Optional contact email": "reporter@example.com",
        "review_status": "approved_for_import",
        "reviewer": "maintainer",
        "reviewed_at": "2026-07-01",
        "decline_reason_code": "",
        "duplicate_of": "",
        "notes": "Approved after duplicate check.",
        "pii_redacted": "yes",
        "import_ready": "yes",
        "escalation_level": "none",
    }
    base.update(overrides)
    return base


def test_missing_sop_columns_detects_absent_headers() -> None:
    """Missing SOP columns should be reported."""
    missing = missing_sop_columns(["Timestamp", "review_status"])
    assert "import_ready" in missing
    assert "reviewer" in missing


def test_resolve_column_map_matches_form_and_sop_headers() -> None:
    """Column resolver should map Form labels and SOP headers."""
    column_map = resolve_column_map(HEADERS)
    assert column_map["job_posting_url"] == "Job posting URL"
    assert column_map["import_ready"] == "import_ready"
    assert column_map["narrative"] == "Why do you suspect this is a ghost job?"


def test_check_eligibility_accepts_valid_row() -> None:
    """Eligible rows should pass all import gates."""
    column_map = resolve_column_map(HEADERS)
    result = check_eligibility(_eligible_row(), column_map)
    assert result.eligible is True


def test_check_eligibility_rejects_non_ready_row() -> None:
    """Rows without import_ready=yes should be rejected."""
    column_map = resolve_column_map(HEADERS)
    result = check_eligibility(_eligible_row(**{"import_ready": "no"}), column_map)
    assert result.eligible is False
    assert result.reason_code == "import_ready"


def test_check_eligibility_rejects_javascript_job_url() -> None:
    """Dangerous job URL schemes should be rejected."""
    column_map = resolve_column_map(HEADERS)
    result = check_eligibility(
        _eligible_row(**{"Job posting URL": "javascript:alert(1)"}),
        column_map,
    )
    assert result.eligible is False
    assert result.reason_code == "invalid_job_url"


def test_check_eligibility_rejects_email_in_narrative() -> None:
    """Email addresses in narrative should trigger pii_in_narrative."""
    column_map = resolve_column_map(HEADERS)
    result = check_eligibility(
        _eligible_row(
            **{
                "Why do you suspect this is a ghost job?": (
                    "Contact me at reporter@example.com about this fake job posting."
                )
            }
        ),
        column_map,
    )
    assert result.eligible is False
    assert result.reason_code == "pii_in_narrative"


def test_plan_row_import_builds_description_preview() -> None:
    """Dry-run plans should include structured report descriptions."""
    column_map = resolve_column_map(HEADERS)
    plan = plan_row_import(_eligible_row(), column_map=column_map, row_number=2)
    assert plan.action == "would_import"
    assert plan.normalized_job_url == "https://boards.greenhouse.io/acme/jobs/1234567"
    assert plan.report_type == "ghost_job"
    assert plan.description_preview is not None
    assert "[ghost-sweep Sheet import]" in plan.description_preview
    assert "Evidence links (public URLs):" in plan.description_preview
    assert "reporter@example.com" not in plan.description_preview


def test_plan_row_import_drops_invalid_evidence_urls() -> None:
    """Invalid evidence URLs should be dropped with dry-run metadata."""
    column_map = resolve_column_map(HEADERS)
    plan = plan_row_import(
        _eligible_row(**{"Evidence links": "javascript:alert(1) https://example.com/ok"}),
        column_map=column_map,
        row_number=3,
    )
    assert plan.action == "would_import"
    assert plan.dropped_evidence_urls == ("javascript:alert(1)",)
    assert plan.description_preview is not None
    assert "https://example.com/ok" in plan.description_preview


def test_dry_run_csv_processes_export(tmp_path: Path) -> None:
    """CSV dry-run should summarize would_import and skipped rows."""
    import csv

    csv_path = tmp_path / "sheet.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=HEADERS)
        writer.writeheader()
        writer.writerow(_eligible_row())
        writer.writerow(_eligible_row(**{"import_ready": "no"}))

    summary = dry_run_csv(csv_path)
    assert summary.processed == 2
    assert summary.would_import == 1
    assert summary.skipped == 1
    assert summary.missing_columns == ()


def test_dry_run_csv_warns_on_missing_sop_columns(tmp_path: Path) -> None:
    """Dry-run should report missing SOP columns in CSV headers."""
    csv_path = tmp_path / "incomplete.csv"
    csv_path.write_text(
        "Timestamp,Job posting URL,review_status\n"
        '"2026-07-01","https://example.com/jobs/1","approved_for_import"\n',
        encoding="utf-8",
    )
    summary = dry_run_csv(csv_path)
    assert "import_ready" in summary.missing_columns
