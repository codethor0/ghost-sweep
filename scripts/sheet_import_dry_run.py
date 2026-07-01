#!/usr/bin/env python3
"""Dry-run planner for Google Sheet rows approved for backend import."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_ROOT = REPO_ROOT / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

from app.services.sheet_import import DryRunPlan, dry_run_csv  # noqa: E402


def _format_plan(plan: DryRunPlan) -> str:
    if plan.action == "skip":
        return (
            f"row={plan.row_number} SKIP reason={plan.reason_code} "
            f"message={plan.message}"
        )
    dropped = ""
    if plan.dropped_evidence_urls:
        dropped = f" dropped_evidence={len(plan.dropped_evidence_urls)}"
    warnings = ""
    if plan.warnings:
        warnings = f" warnings={','.join(plan.warnings)}"
    return (
        f"row={plan.row_number} WOULD_IMPORT company={plan.company_name!r} "
        f"domain={plan.company_domain} posting_url={plan.normalized_job_url} "
        f"source={plan.posting_source} report_type={plan.report_type} "
        f"fingerprint={plan.row_fingerprint}{dropped}{warnings}"
    )


def main() -> int:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="Dry-run Google Sheet import planning (no database writes).",
    )
    parser.add_argument(
        "csv_path",
        type=Path,
        help="Path to a maintainer-exported Google Sheet CSV file",
    )
    parser.add_argument(
        "--show-descriptions",
        action="store_true",
        help="Print full planned report descriptions for would_import rows",
    )
    args = parser.parse_args()

    if not args.csv_path.is_file():
        print(f"FAIL: CSV file not found: {args.csv_path}", file=sys.stderr)
        return 1

    summary = dry_run_csv(args.csv_path)

    if summary.missing_columns:
        print("WARN: missing SOP columns in CSV header:")
        for column in summary.missing_columns:
            print(f"  - {column}")
        print("Export the linked Google Sheet after adding maintainer columns.")
        print("See docs/moderation-sop.md and scripts/verify_sheet_columns.py")

    for plan in summary.plans:
        print(_format_plan(plan))
        if args.show_descriptions and plan.action == "would_import":
            assert plan.description_preview is not None
            print("--- description preview ---")
            print(plan.description_preview)
            print("--- end preview ---")

    print(
        f"SUMMARY processed={summary.processed} would_import={summary.would_import} "
        f"skipped={summary.skipped}"
    )

    if summary.missing_columns:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
