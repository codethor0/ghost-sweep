#!/usr/bin/env python3
"""Generate validation-results.json from cmd-results.ndjson exit codes."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from audit_evidence import AuditSession, write_validation_results


def main() -> int:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="Build validation-results.json from cmd-results.ndjson."
    )
    parser.add_argument(
        "--cmd-results",
        required=True,
        help="Path to authoritative cmd-results.ndjson",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to write validation-results.json",
    )
    parser.add_argument(
        "--audit-start",
        required=True,
        help="Canonical audit start timestamp",
    )
    parser.add_argument(
        "--audit-end",
        required=True,
        help="Canonical audit end timestamp",
    )
    args = parser.parse_args()

    cmd_results = Path(args.cmd_results).resolve()
    output = Path(args.output).resolve()
    if not cmd_results.exists():
        print(f"Missing cmd-results file: {cmd_results}", file=sys.stderr)
        return 1

    session = AuditSession(audit_start=args.audit_start, audit_end=args.audit_end)
    results = write_validation_results(cmd_results, output, session)
    print(f"Wrote {len(results)} validation results to {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
