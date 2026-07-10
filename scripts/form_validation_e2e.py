#!/usr/bin/env python3
"""API-level form validation checks for ghost-sweep local stack."""

from __future__ import annotations

import argparse
import json
import sys
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import httpx

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from live_e2e_validation import discover_job_posting_id  # noqa: E402


@dataclass
class CheckResult:
    name: str
    passed: bool
    status_code: int
    detail: str


@dataclass
class ValidationReport:
    checks: list[CheckResult] = field(default_factory=list)

    def add(self, name: str, passed: bool, status_code: int, detail: str) -> None:
        self.checks.append(CheckResult(name, passed, status_code, detail))

    @property
    def passed(self) -> bool:
        return all(check.passed for check in self.checks)


def post_json(
    client: httpx.Client,
    path: str,
    payload: dict[str, Any],
    headers: dict[str, str] | None = None,
) -> httpx.Response:
    return client.post(path, json=payload, headers=headers)


def run_validation(base_url: str, repo_root: str) -> ValidationReport:
    report = ValidationReport()
    api = f"{base_url.rstrip('/')}/api/v1"
    ts = int(time.time())
    posting_id = discover_job_posting_id(repo_root)
    report.add(
        "discover job posting id",
        posting_id is not None,
        0 if posting_id is None else 200,
        posting_id or "seed script did not return posting id",
    )
    if posting_id is None:
        return report

    with httpx.Client(timeout=30.0) as client:
        cases = [
            (
                "register missing fields",
                f"{api}/auth/register",
                {},
                422,
            ),
            (
                "register short password",
                f"{api}/auth/register",
                {
                    "email": f"qa-val-{ts}@example.com",
                    "username": f"qa_val_{ts}",
                    "password": "short",
                },
                422,
            ),
            (
                "register invalid username",
                f"{api}/auth/register",
                {
                    "email": f"qa-val2-{ts}@example.com",
                    "username": "bad user!",
                    "password": "StrongPass123!",
                },
                422,
            ),
            (
                "register invalid email",
                f"{api}/auth/register",
                {
                    "email": "not-an-email",
                    "username": f"qa_val3_{ts}",
                    "password": "StrongPass123!",
                },
                422,
            ),
            (
                "login missing password",
                f"{api}/auth/login",
                {"identifier": "someone@example.com"},
                422,
            ),
            (
                "report unauthenticated",
                f"{api}/reports",
                {
                    "job_posting_id": posting_id,
                    "report_type": "ghost_job",
                    "description": "Unauthenticated report attempt with enough characters.",
                },
                401,
            ),
            (
                "report short description",
                f"{api}/reports",
                {
                    "job_posting_id": posting_id,
                    "report_type": "ghost_job",
                    "description": "too short",
                },
                401,
            ),
        ]

        for name, url, payload, expected_status in cases:
            response = post_json(client, url, payload)
            ok = response.status_code == expected_status
            detail = response.text[:240]
            report.add(name, ok, response.status_code, detail)

        register = post_json(
            client,
            f"{api}/auth/register",
            {
                "email": f"qa-val-ok-{ts}@example.com",
                "username": f"qa_val_ok_{ts}",
                "password": "StrongPass123!",
            },
        )
        report.add(
            "register valid baseline",
            register.status_code == 200,
            register.status_code,
            register.text[:240],
        )
        token = register.json().get("access_token") if register.status_code == 200 else None

        if token:
            short_report = post_json(
                client,
                f"{api}/reports",
                {
                    "job_posting_id": posting_id,
                    "report_type": "ghost_job",
                    "description": "too short",
                },
                headers={"Authorization": f"Bearer {token}"},
            )
            report.add(
                "report short description authed",
                short_report.status_code == 422,
                short_report.status_code,
                short_report.text[:240],
            )

            valid_report = post_json(
                client,
                f"{api}/reports",
                {
                    "job_posting_id": posting_id,
                    "report_type": "ghost_job",
                    "description": (
                        "QA validation report with sufficient length for schema validation."
                    ),
                },
                headers={"Authorization": f"Bearer {token}"},
            )
            report.add(
                "report valid submission",
                valid_report.status_code == 201,
                valid_report.status_code,
                valid_report.text[:240],
            )

            duplicate = post_json(
                client,
                f"{api}/auth/register",
                {
                    "email": f"qa-val-ok-{ts}@example.com",
                    "username": f"qa_val_dup_{ts}",
                    "password": "StrongPass123!",
                },
            )
            report.add(
                "register duplicate email",
                duplicate.status_code == 409,
                duplicate.status_code,
                duplicate.text[:240],
            )

            bad_posting = post_json(
                client,
                f"{api}/reports",
                {
                    "job_posting_id": str(uuid.uuid4()),
                    "report_type": "ghost_job",
                    "description": (
                        "QA validation report with sufficient length for schema validation."
                    ),
                },
                headers={"Authorization": f"Bearer {token}"},
            )
            report.add(
                "report unknown posting",
                bad_posting.status_code == 404,
                bad_posting.status_code,
                bad_posting.text[:240],
            )

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Run API form validation checks.")
    parser.add_argument("--backend-url", default="http://localhost:8000")
    parser.add_argument("--output-json")
    parser.add_argument(
        "--repo-root",
        default=str(REPO_ROOT),
    )
    args = parser.parse_args()

    report = run_validation(args.backend_url, args.repo_root)
    payload = {
        "passed": report.passed,
        "checks": [asdict(check) for check in report.checks],
    }
    print(json.dumps(payload, indent=2))
    if args.output_json:
        with open(args.output_json, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
    return 0 if report.passed else 1


if __name__ == "__main__":
    sys.exit(main())
