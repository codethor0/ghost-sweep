#!/usr/bin/env python3
"""Live end-to-end validation against local Docker backend and frontend."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import uuid
from dataclasses import asdict, dataclass, field
from http.cookiejar import CookieJar
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener, HTTPCookieProcessor

TOKEN_RE = re.compile(r"eyJ[A-Za-z0-9._-]+")
REFRESH_RE = re.compile(r'"refresh_token"\s*:\s*"[^"]+"')
ACCESS_RE = re.compile(r'"access_token"\s*:\s*"[^"]+"')
AUTH_HEADER_RE = re.compile(r"Authorization:\s*Bearer\s+\S+", re.IGNORECASE)
ERROR_MARKERS = (
    "Application error",
    "Internal Server Error",
    "Unhandled",
    "Traceback (most recent call last)",
)


@dataclass
class CheckResult:
    """Single validation check outcome."""

    name: str
    passed: bool
    detail: str
    status_code: int | None = None


@dataclass
class ValidationReport:
    """Aggregate validation report."""

    checks: list[CheckResult] = field(default_factory=list)
    report_id: str | None = None
    company_id: str | None = None
    posting_id: str | None = None

    def add(
        self, name: str, passed: bool, detail: str, status_code: int | None = None
    ) -> None:
        self.checks.append(CheckResult(name, passed, detail, status_code))

    @property
    def passed(self) -> bool:
        return all(check.passed for check in self.checks)


def redact(text: str) -> str:
    """Redact tokens and authorization headers from text."""
    text = TOKEN_RE.sub("[REDACTED_JWT]", text)
    text = ACCESS_RE.sub('"access_token":"[REDACTED]"', text)
    text = REFRESH_RE.sub('"refresh_token":"[REDACTED]"', text)
    text = AUTH_HEADER_RE.sub("Authorization: Bearer [REDACTED]", text)
    return text


def request_json(
    opener: Any,
    method: str,
    url: str,
    payload: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, dict[str, Any] | str, dict[str, str]]:
    """Perform HTTP request and return status, body, response headers."""
    body_bytes: bytes | None = None
    req_headers = {"Accept": "application/json"}
    if headers:
        req_headers.update(headers)
    if payload is not None:
        body_bytes = json.dumps(payload).encode("utf-8")
        req_headers["Content-Type"] = "application/json"
    req = Request(url, data=body_bytes, method=method, headers=req_headers)
    try:
        with opener.open(req, timeout=30) as response:
            raw = response.read().decode("utf-8", errors="replace")
            resp_headers = dict(response.headers)
            if raw:
                try:
                    return response.status, json.loads(raw), resp_headers
                except json.JSONDecodeError:
                    return response.status, raw, resp_headers
            return response.status, {}, resp_headers
    except HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            parsed: dict[str, Any] | str = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            parsed = raw
        return exc.code, parsed, dict(exc.headers)
    except URLError as exc:
        return 0, str(exc.reason), {}


def request_text(
    opener: Any,
    method: str,
    url: str,
    headers: dict[str, str] | None = None,
) -> tuple[int, str]:
    """Perform HTTP request and return status and text body."""
    req_headers = {"Accept": "text/html,application/json"}
    if headers:
        req_headers.update(headers)
    req = Request(url, method=method, headers=req_headers)
    try:
        with opener.open(req, timeout=30) as response:
            return response.status, response.read().decode("utf-8", errors="replace")
    except HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")
    except URLError as exc:
        return 0, str(exc.reason)


def discover_job_posting_id(repo_root: str) -> str | None:
    """Discover demo job posting ID via seed script stdout."""
    env = {
        **os.environ,
        "DATABASE_URL": "postgresql+asyncpg://ghost_sweep:ghost_sweep@localhost:5432/ghost_sweep",
        "ENVIRONMENT": "development",
    }
    result = subprocess.run(
        ["python3.11", "scripts/seed_demo_data.py"],
        cwd=f"{repo_root}/backend",
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    output = result.stdout + result.stderr
    for line in output.splitlines():
        if "demo job posting" in line.lower():
            parts = line.strip().split(": ")
            if len(parts) == 2:
                try:
                    uuid.UUID(parts[1])
                    return parts[1]
                except ValueError:
                    continue
    return None


def pick_company_id(companies_body: dict[str, Any]) -> str | None:
    """Pick a company ID, preferring the demo company when present."""
    items = companies_body.get("items", [])
    for item in items:
        if item.get("name") == "ghost-sweep Demo Company":
            return str(item["id"])
    if items:
        return str(items[0]["id"])
    return None


def run_validation(
    backend_url: str,
    frontend_url: str,
    public_mvp_url: str | None,
    repo_root: str,
) -> ValidationReport:
    """Run live E2E validation checks."""
    report = ValidationReport()
    jar = CookieJar()
    opener = build_opener(HTTPCookieProcessor(jar))
    api = f"{backend_url.rstrip('/')}/api/v1"
    ts = int(time.time())
    email = f"e2e-{ts}@example.com"
    username = f"e2e_user_{ts}"
    password = "StrongPass123!"

    status, body, _ = request_json(
        opener,
        "POST",
        f"{api}/auth/register",
        {"email": email, "username": username, "password": password},
    )
    ok = status == 200 and isinstance(body, dict) and "access_token" in body
    report.add("auth register", ok, redact(json.dumps(body)), status)
    if not ok:
        return report

    access_token = body["access_token"]
    refresh_token = body["refresh_token"]
    auth_headers = {"Authorization": f"Bearer {access_token}"}

    status, body, _ = request_json(
        opener,
        "POST",
        f"{api}/auth/login",
        {"identifier": email, "password": password},
    )
    ok = status == 200 and isinstance(body, dict) and "access_token" in body
    report.add("auth login", ok, redact(json.dumps(body)), status)
    if ok:
        access_token = body["access_token"]
        refresh_token = body["refresh_token"]
        auth_headers = {"Authorization": f"Bearer {access_token}"}

    status, body, _ = request_json(
        opener, "GET", f"{api}/auth/me", headers=auth_headers
    )
    report.add("auth me", status == 200, redact(json.dumps(body)), status)

    status, body, _ = request_json(
        opener,
        "POST",
        f"{api}/auth/refresh",
        {"refresh_token": refresh_token},
    )
    ok = status == 200 and isinstance(body, dict) and "access_token" in body
    report.add("auth refresh", ok, redact(json.dumps(body)), status)
    if ok:
        access_token = body["access_token"]
        refresh_token = body["refresh_token"]
        auth_headers = {"Authorization": f"Bearer {access_token}"}

    status, body, _ = request_json(
        opener,
        "POST",
        f"{api}/auth/logout",
        {"refresh_token": refresh_token},
    )
    report.add("auth logout", status == 204, f"status={status}", status)

    status, body, _ = request_json(
        opener,
        "POST",
        f"{api}/auth/refresh",
        {"refresh_token": refresh_token},
    )
    report.add(
        "auth refresh after logout", status == 401, redact(json.dumps(body)), status
    )

    login_status, login_body, _ = request_json(
        opener,
        "POST",
        f"{api}/auth/login",
        {"identifier": email, "password": password},
    )
    if login_status == 200 and isinstance(login_body, dict):
        access_token = login_body["access_token"]
        auth_headers = {"Authorization": f"Bearer {access_token}"}

    status, body, _ = request_json(opener, "GET", f"{api}/companies")
    ok = status == 200 and isinstance(body, dict) and "items" in body
    report.add(
        "companies list",
        ok,
        f"items={len(body.get('items', [])) if isinstance(body, dict) else 0}",
        status,
    )
    company_id = pick_company_id(body) if isinstance(body, dict) else None
    report.company_id = company_id

    if company_id:
        status, body, _ = request_json(opener, "GET", f"{api}/companies/{company_id}")
        report.add(
            "company detail", status == 200, redact(json.dumps(body)[:200]), status
        )

        status, body, _ = request_json(
            opener, "GET", f"{api}/companies/{company_id}/integrity-score"
        )
        report.add(
            "company integrity-score",
            status == 200,
            redact(json.dumps(body)[:200]),
            status,
        )

    posting_id = discover_job_posting_id(repo_root)
    report.posting_id = posting_id
    report.add(
        "discover job posting id",
        posting_id is not None,
        posting_id or "seed script did not return posting id",
    )

    if posting_id:
        status, body, _ = request_json(
            opener, "GET", f"{api}/job-postings/{posting_id}"
        )
        report.add(
            "job posting detail", status == 200, redact(json.dumps(body)[:200]), status
        )

        status, body, _ = request_json(
            opener,
            "GET",
            f"{api}/job-postings/{posting_id}/risk-score",
        )
        report.add(
            "job posting risk-score",
            status == 200,
            redact(json.dumps(body)[:200]),
            status,
        )

        create_payload = {
            "job_posting_id": posting_id,
            "report_type": "ghost_job",
            "description": (
                "Live E2E validation report with sufficient length for schema validation."
            ),
        }
        status, body, _ = request_json(
            opener,
            "POST",
            f"{api}/reports",
            create_payload,
            headers=auth_headers,
        )
        ok = status == 201 and isinstance(body, dict) and "id" in body
        report.add("report create", ok, redact(json.dumps(body)[:300]), status)
        report_id = str(body["id"]) if ok else None
        report.report_id = report_id

        if report_id:
            status, body, _ = request_json(opener, "GET", f"{api}/reports/{report_id}")
            report.add(
                "report get", status == 200, redact(json.dumps(body)[:300]), status
            )

            status, body, _ = request_json(
                opener,
                "POST",
                f"{api}/reports/{report_id}/votes",
                {"vote": "up"},
                headers=auth_headers,
            )
            report.add(
                "vote create", status == 201, redact(json.dumps(body)[:200]), status
            )

    status, body, _ = request_json(opener, "GET", f"{api}/moderation/reports")
    report.add(
        "moderation unauth", status == 401, redact(json.dumps(body)[:200]), status
    )

    status, body, _ = request_json(
        opener,
        "GET",
        f"{api}/moderation/reports",
        headers=auth_headers,
    )
    report.add(
        "moderation non-admin", status == 403, redact(json.dumps(body)[:200]), status
    )

    routes = [
        "/",
        "/register",
        "/login",
        "/dashboard",
        "/companies",
    ]
    if company_id:
        routes.append(f"/companies/{company_id}")
    if posting_id:
        routes.append(f"/postings/{posting_id}")
        routes.append(f"/postings/{posting_id}/report")

    for route in routes:
        status, html = request_text(opener, "GET", f"{frontend_url.rstrip('/')}{route}")
        marker = next((m for m in ERROR_MARKERS if m in html), None)
        ok = status == 200 and marker is None
        report.add(
            f"frontend {route}",
            ok,
            f"status={status} marker={marker or 'none'}",
            status,
        )

    if public_mvp_url:
        status, html = request_text(opener, "GET", f"{public_mvp_url.rstrip('/')}/")
        ok = (
            status == 200
            and "Submit a report" in html
            and "REPLACE_WITH_REAL_FORM_URL" in html
            and "manual review" in html.lower()
        )
        report.add("public mvp preview", ok, f"status={status}", status)

    return report


def render_markdown(report: ValidationReport) -> str:
    """Render validation report as markdown."""
    lines = ["# Live E2E Validation Report", ""]
    lines.append(f"Overall: {'PASS' if report.passed else 'FAIL'}")
    lines.append("")
    lines.append("| Check | Pass | Status | Detail |")
    lines.append("| ----- | ---- | ------ | ------ |")
    for check in report.checks:
        lines.append(
            f"| {check.name} | {'yes' if check.passed else 'no'} | "
            f"{check.status_code or '-'} | {check.detail.replace('|', '/')} |"
        )
    if report.report_id:
        lines.append("")
        lines.append(f"Report ID: {report.report_id}")
    return "\n".join(lines) + "\n"


def main() -> int:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="Run live E2E validation against local stack."
    )
    parser.add_argument("--backend-url", default="http://localhost:8000")
    parser.add_argument("--frontend-url", default="http://localhost:3000")
    parser.add_argument("--public-mvp-url", default="http://localhost:8080")
    parser.add_argument("--skip-public-mvp", action="store_true")
    parser.add_argument("--output-json")
    parser.add_argument("--output-md")
    parser.add_argument(
        "--repo-root",
        default=str(__import__("pathlib").Path(__file__).resolve().parent.parent),
    )
    args = parser.parse_args()

    public_url = None if args.skip_public_mvp else args.public_mvp_url
    validation = run_validation(
        args.backend_url, args.frontend_url, public_url, args.repo_root
    )

    payload = {
        "passed": validation.passed,
        "company_id": validation.company_id,
        "posting_id": validation.posting_id,
        "report_id": validation.report_id,
        "checks": [asdict(check) for check in validation.checks],
    }
    markdown = render_markdown(validation)

    print(markdown)
    if args.output_json:
        with open(args.output_json, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
    if args.output_md:
        with open(args.output_md, "w", encoding="utf-8") as handle:
            handle.write(markdown)

    return 0 if validation.passed else 1


if __name__ == "__main__":
    sys.exit(main())
