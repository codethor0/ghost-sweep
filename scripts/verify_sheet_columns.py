#!/usr/bin/env python3
"""Verify a Google Sheet CSV export contains required maintainer columns."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_ROOT = REPO_ROOT / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

from app.services.sheet_import import (  # noqa: E402
    missing_sop_columns,
    resolve_column_map,
)

EXPECTED_FORM_FIELDS = (
    "timestamp",
    "job_posting_url",
    "company_name",
    "job_title",
    "location",
    "date_seen",
    "narrative",
    "company_responded",
    "consent",
)


def main() -> int:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="Verify Sheet CSV headers against moderation SOP columns.",
    )
    parser.add_argument(
        "csv_path",
        type=Path,
        help="Path to a maintainer-exported Google Sheet CSV file",
    )
    args = parser.parse_args()

    if not args.csv_path.is_file():
        print(f"FAIL: CSV file not found: {args.csv_path}", file=sys.stderr)
        return 1

    with args.csv_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        try:
            headers = next(reader)
        except StopIteration:
            print("FAIL: CSV file is empty", file=sys.stderr)
            return 1

    sop_missing = missing_sop_columns(headers)
    column_map = resolve_column_map(headers)
    form_missing = [
        field_name for field_name in EXPECTED_FORM_FIELDS if field_name not in column_map
    ]

    print(f"CSV: {args.csv_path}")
    print(f"Header columns ({len(headers)}):")
    for header in headers:
        print(f"  - {header}")

    if sop_missing:
        print("FAIL: missing required SOP columns:")
        for column in sop_missing:
            print(f"  - {column}")
    else:
        print("PASS: all required SOP columns present")

    if form_missing:
        print("WARN: missing expected Form field mappings:")
        for field_name in form_missing:
            print(f"  - {field_name}")
    else:
        print("PASS: all expected Form fields mapped")

    if sop_missing:
        print("See docs/moderation-sop.md for column setup.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
