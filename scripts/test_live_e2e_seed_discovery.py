#!/usr/bin/env python3
"""Regression tests for live E2E seed discovery helper."""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from live_e2e_validation import discover_job_posting_id  # noqa: E402


def test_discover_job_posting_id_returns_uuid() -> None:
    """Seed discovery must return a valid posting UUID when demo data exists."""
    posting_id = discover_job_posting_id(str(REPO_ROOT))
    assert posting_id is not None, "expected demo job posting id from seed script"
    uuid.UUID(posting_id)


if __name__ == "__main__":
    test_discover_job_posting_id_returns_uuid()
    print("PASS: discover_job_posting_id")
