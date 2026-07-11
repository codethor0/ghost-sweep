#!/usr/bin/env python3
"""Post-release audit orchestrator with provenance-safe command logging."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

from audit_evidence import (
    AuditSession,
    CommandRecord,
    append_command_record,
    backend_py_compile_files,
    run_logged_command,
    verify_metadata_timestamps_consistent,
    write_audit_metadata,
    write_validation_results,
)


def backend_is_listening(url: str) -> bool:
    """Return True when backend health endpoint responds."""
    try:
        with urllib.request.urlopen(f"{url.rstrip('/')}/health", timeout=3) as response:
            return response.status == 200
    except (urllib.error.URLError, TimeoutError):
        return False


def write_provenance(
    path: Path,
    backend_url: str,
    repo_root: Path,
    session: AuditSession,
    backend_pid: int | None = None,
) -> None:
    """Record backend URL, repository SHA, process, and port before E2E."""
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )
    tree = subprocess.run(
        ["git", "rev-parse", "HEAD^{tree}"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )
    parsed = urlparse(backend_url)
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    lines = [
        f"backend_url={backend_url}",
        f"backend_port={port}",
        f"head={head.stdout.strip()}",
        f"tree={tree.stdout.strip()}",
        f"working_directory={repo_root}",
        f"audit_start={session.audit_start}",
        f"audit_end={session.require_complete()}",
    ]
    if backend_pid is not None:
        lines.append(f"backend_pid={backend_pid}")
        ps = subprocess.run(
            ["ps", "-p", str(backend_pid), "-o", "pid,ppid,command"],
            capture_output=True,
            text=True,
            check=False,
        )
        lines.append("process=" + ps.stdout.strip().replace("\n", " | "))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_py_compile(
    backend_dir: Path,
    validation_root: Path,
    ndjson_path: Path,
    session: AuditSession,
) -> tuple[int, int]:
    """Compile backend Python sources discovered from within backend_dir."""
    files = backend_py_compile_files(backend_dir)
    file_count = len(files)
    if not files:
        record = CommandRecord(
            name="backend py_compile",
            workdir=str(backend_dir),
            start=session.audit_start,
            end=session.require_complete(),
            exit_code=2,
            status="FAIL",
            expected="exit 0",
            stdout="",
            stderr="no python files discovered",
        )
        append_command_record(ndjson_path, record)
        return 2, file_count

    stdout_path = validation_root / "backend-py_compile.stdout.txt"
    stderr_path = validation_root / "backend-py_compile.stderr.txt"
    result = subprocess.run(
        [sys.executable, "-m", "py_compile", *[str(path) for path in files]],
        cwd=str(backend_dir),
        capture_output=True,
        text=True,
        check=False,
    )
    stdout_path.write_text(result.stdout, encoding="utf-8")
    stderr_path.write_text(result.stderr, encoding="utf-8")
    command_record = CommandRecord(
        name="backend py_compile",
        workdir=str(backend_dir),
        start=session.audit_start,
        end=session.require_complete(),
        exit_code=result.returncode,
        status="PASS" if result.returncode == 0 else "FAIL",
        expected="exit 0",
        stdout=stdout_path.name,
        stderr=stderr_path.name,
    )
    append_command_record(ndjson_path, command_record)
    return result.returncode, file_count


def finalize_reports(
    validation_root: Path,
    ndjson_path: Path,
    session: AuditSession,
    *,
    py_compile_file_count: int,
) -> list[str]:
    """Write validation-results and metadata using one canonical session."""
    validation_path = validation_root / "validation-results.json"
    metadata_path = validation_root / "BUNDLE_METADATA.json"
    write_validation_results(ndjson_path, validation_path, session)
    command_count = len(ndjson_path.read_text(encoding="utf-8").splitlines())
    write_audit_metadata(
        metadata_path,
        session,
        command_count=command_count,
        extra={"py_compile_file_count": py_compile_file_count},
    )
    return verify_metadata_timestamps_consistent([metadata_path], session)


def main() -> int:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description="Run provenance-safe post-release checks.")
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--validation-root", required=True)
    parser.add_argument("--backend-url", default="http://127.0.0.1:8000")
    parser.add_argument("--require-backend-ready", action="store_true")
    parser.add_argument("--run-e2e", action="store_true")
    parser.add_argument("--e2e-json")
    parser.add_argument("--e2e-md")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    validation_root = Path(args.validation_root).resolve()
    validation_root.mkdir(parents=True, exist_ok=True)
    ndjson_path = validation_root / "cmd-results.ndjson"
    if ndjson_path.exists():
        ndjson_path.unlink()

    session = AuditSession.begin()
    backend_dir = repo_root / "backend"

    py_compile_code, py_compile_count = run_py_compile(
        backend_dir, validation_root, ndjson_path, session
    )
    if py_compile_code != 0:
        issues = finalize_reports(
            validation_root, ndjson_path, session, py_compile_file_count=py_compile_count
        )
        if issues:
            print("\n".join(issues), file=sys.stderr)
        print("backend py_compile failed", file=sys.stderr)
        session.complete()
        return py_compile_code

    if args.require_backend_ready and not backend_is_listening(args.backend_url):
        append_command_record(
            ndjson_path,
            CommandRecord(
                name="backend readiness gate",
                workdir=str(repo_root),
                start=session.audit_start,
                end=session.require_complete(),
                exit_code=1,
                status="FAIL",
                expected="backend health 200",
                stdout="",
                stderr="backend not listening; E2E blocked",
            ),
        )
        issues = finalize_reports(
            validation_root, ndjson_path, session, py_compile_file_count=py_compile_count
        )
        if issues:
            print("\n".join(issues), file=sys.stderr)
        print("Backend not ready; E2E blocked", file=sys.stderr)
        session.complete()
        return 1

    if args.run_e2e:
        provenance_path = validation_root / "e2e-provenance.txt"
        write_provenance(provenance_path, args.backend_url, repo_root, session)
        e2e_cmd = [
            sys.executable,
            str(repo_root / "scripts" / "live_e2e_validation.py"),
            "--backend-url",
            args.backend_url,
            "--skip-public-mvp",
            "--repo-root",
            str(repo_root),
        ]
        if args.e2e_json:
            e2e_cmd.extend(["--output-json", args.e2e_json])
        if args.e2e_md:
            e2e_cmd.extend(["--output-md", args.e2e_md])
        record = run_logged_command(
            "baseline e2e",
            e2e_cmd,
            repo_root,
            "26/26 pass",
            validation_root / "baseline-e2e.stdout.txt",
            validation_root / "baseline-e2e.stderr.txt",
            session=session,
        )
        append_command_record(ndjson_path, record)
        if record.exit_code != 0:
            issues = finalize_reports(
                validation_root,
                ndjson_path,
                session,
                py_compile_file_count=py_compile_count,
            )
            session.complete()
            return record.exit_code

    issues = finalize_reports(
        validation_root, ndjson_path, session, py_compile_file_count=py_compile_count
    )
    session.complete()
    if issues:
        print("\n".join(issues), file=sys.stderr)
        return 1

    metadata = json.loads((validation_root / "BUNDLE_METADATA.json").read_text())
    print(json.dumps(metadata))
    return 0


if __name__ == "__main__":
    sys.exit(main())
