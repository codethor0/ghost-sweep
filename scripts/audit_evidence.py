#!/usr/bin/env python3
"""Shared audit evidence logging and validation-result generation."""

from __future__ import annotations

import json
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class AuditSession:
    """Canonical audit timestamps shared by all generated metadata."""

    audit_start: str
    audit_end: str | None = None

    @classmethod
    def begin(cls) -> AuditSession:
        """Create a new audit session with a single canonical start time."""
        return cls(audit_start=utc_now())

    def complete(self) -> str:
        """Set and return the canonical completion time."""
        self.audit_end = utc_now()
        return self.audit_end

    def require_complete(self) -> str:
        """Return completion time, setting it when still open."""
        if self.audit_end is None:
            return self.complete()
        return self.audit_end


@dataclass
class CommandRecord:
    """Single command execution record for audit evidence."""

    name: str
    workdir: str
    start: str
    end: str
    exit_code: int
    status: str
    expected: str
    stdout: str
    stderr: str

    @property
    def passed(self) -> bool:
        return self.exit_code == 0


def utc_now() -> str:
    """Return current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_audit_metadata(
    output_path: Path,
    session: AuditSession,
    *,
    command_count: int,
    extra: dict[str, object] | None = None,
) -> dict[str, object]:
    """Write bundle metadata using canonical session timestamps only."""
    metadata: dict[str, object] = {
        "audit_start": session.audit_start,
        "audit_end": session.require_complete(),
        "command_count": command_count,
    }
    if extra:
        metadata.update(extra)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return metadata


def verify_metadata_timestamps_consistent(
    metadata_paths: list[Path],
    session: AuditSession,
) -> list[str]:
    """Return issues when metadata files disagree on canonical timestamps."""
    issues: list[str] = []
    expected_start = session.audit_start
    expected_end = session.require_complete()
    for path in metadata_paths:
        if not path.exists():
            issues.append(f"missing metadata file: {path}")
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        for key, expected in (
            ("audit_start", expected_start),
            ("audit_end", expected_end),
        ):
            actual = payload.get(key)
            if actual != expected:
                issues.append(f"{path.name} {key}={actual!r} expected {expected!r}")
        legacy = payload.get("audit_timestamp")
        if legacy is not None and legacy not in {expected_start, expected_end}:
            issues.append(
                f"{path.name} audit_timestamp={legacy!r} not canonical start/end"
            )
    return issues


def run_logged_command(
    name: str,
    args: list[str],
    cwd: Path,
    expected: str,
    stdout_path: Path,
    stderr_path: Path,
    *,
    session: AuditSession | None = None,
) -> CommandRecord:
    """Run a command and capture exit code from the process, not stderr content."""
    start = session.audit_start if session is not None else utc_now()
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    stderr_path.parent.mkdir(parents=True, exist_ok=True)
    with stdout_path.open("w", encoding="utf-8") as out_handle, stderr_path.open(
        "w", encoding="utf-8"
    ) as err_handle:
        result = subprocess.run(
            args,
            cwd=str(cwd),
            stdout=out_handle,
            stderr=err_handle,
            text=True,
            check=False,
        )
    end = session.require_complete() if session is not None else utc_now()
    status = "PASS" if result.returncode == 0 else "FAIL"
    return CommandRecord(
        name=name,
        workdir=str(cwd),
        start=start,
        end=end,
        exit_code=result.returncode,
        status=status,
        expected=expected,
        stdout=stdout_path.name,
        stderr=stderr_path.name,
    )


def append_command_record(ndjson_path: Path, record: CommandRecord) -> None:
    """Append one command record as NDJSON."""
    ndjson_path.parent.mkdir(parents=True, exist_ok=True)
    with ndjson_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(record)) + "\n")


def load_command_records(ndjson_path: Path) -> list[CommandRecord]:
    """Load all command records from NDJSON file."""
    if not ndjson_path.exists():
        return []
    records: list[CommandRecord] = []
    for line in ndjson_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        records.append(CommandRecord(**payload))
    return records


def build_validation_results(
    records: list[CommandRecord],
    session: AuditSession,
) -> list[dict[str, object]]:
    """Build validation-results.json strictly from command exit codes."""
    audit_end = session.require_complete()
    results: list[dict[str, object]] = []
    for record in records:
        actual = f"exit {record.exit_code}"
        if record.exit_code == 0 and "passed" in record.expected.lower():
            actual = record.expected
        results.append(
            {
                "name": record.name,
                "command": record.name,
                "working_directory": record.workdir,
                "start_time": session.audit_start,
                "end_time": audit_end,
                "duration_seconds": 0,
                "exit_code": record.exit_code,
                "status": record.status,
                "expected": record.expected,
                "actual": actual,
                "stdout_file": record.stdout,
                "stderr_file": record.stderr,
            }
        )
    return results


def write_validation_results(
    ndjson_path: Path,
    output_path: Path,
    session: AuditSession,
) -> list[dict[str, object]]:
    """Generate validation-results.json from authoritative cmd-results.ndjson."""
    records = load_command_records(ndjson_path)
    results = build_validation_results(records, session)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    return results


def backend_py_compile_files(backend_dir: Path) -> list[Path]:
    """Collect Python sources for py_compile from within the backend directory."""
    patterns = ("app", "tests", "alembic")
    files: list[Path] = []
    for pattern in patterns:
        root = backend_dir / pattern
        if root.is_dir():
            files.extend(sorted(root.rglob("*.py")))
    return files
