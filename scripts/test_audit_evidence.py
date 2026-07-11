#!/usr/bin/env python3
"""Tests for audit evidence logging and validation-result generation."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def load_module(name: str, path: Path):
    """Load a script module from path."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_validation_results_use_exit_codes_not_stderr() -> None:
    """validation-results.json must mirror cmd-results exit codes."""
    repo_root = Path(__file__).resolve().parents[1]
    audit_evidence = load_module("audit_evidence", repo_root / "scripts" / "audit_evidence.py")
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        ndjson = root / "cmd-results.ndjson"
        session = audit_evidence.AuditSession.begin()
        record = audit_evidence.CommandRecord(
            name="frontend lint",
            workdir=str(repo_root / "frontend"),
            start=session.audit_start,
            end=session.audit_start,
            exit_code=0,
            status="PASS",
            expected="exit 0",
            stdout="out.txt",
            stderr="err.txt",
        )
        audit_evidence.append_command_record(ndjson, record)
        output = root / "validation-results.json"
        results = audit_evidence.write_validation_results(ndjson, output, session)
        assert results[0]["status"] == "PASS"
        assert results[0]["exit_code"] == 0
        assert results[0]["start_time"] == session.audit_start


def test_exit_zero_with_stderr_warning_is_pass() -> None:
    """Warnings on stderr must not downgrade a zero exit code."""
    repo_root = Path(__file__).resolve().parents[1]
    audit_evidence = load_module("audit_evidence", repo_root / "scripts" / "audit_evidence.py")
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        stdout = root / "stdout.txt"
        stderr = root / "stderr.txt"
        stderr.write_text("npm warn example warning on stderr\n", encoding="utf-8")
        stdout.write_text("ok\n", encoding="utf-8")
        session = audit_evidence.AuditSession.begin()
        record = audit_evidence.run_logged_command(
            "stderr warning command",
            [sys.executable, "-c", "import sys; sys.stderr.write('warn\\n'); print('ok')"],
            root,
            "exit 0",
            stdout,
            stderr,
            session=session,
        )
        assert record.exit_code == 0
        assert record.status == "PASS"


def test_nonzero_exit_with_empty_stderr_is_fail() -> None:
    """Nonzero exit codes must fail even when stderr is empty."""
    repo_root = Path(__file__).resolve().parents[1]
    audit_evidence = load_module("audit_evidence", repo_root / "scripts" / "audit_evidence.py")
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        stdout = root / "stdout.txt"
        stderr = root / "stderr.txt"
        session = audit_evidence.AuditSession.begin()
        record = audit_evidence.run_logged_command(
            "nonzero silent command",
            [sys.executable, "-c", "raise SystemExit(3)"],
            root,
            "exit 0",
            stdout,
            stderr,
            session=session,
        )
        assert record.exit_code == 3
        assert record.status == "FAIL"
        assert stderr.read_text(encoding="utf-8") == ""


def test_metadata_timestamp_disagreement_is_detected() -> None:
    """Canonical timestamp verification must reject mismatched metadata files."""
    repo_root = Path(__file__).resolve().parents[1]
    audit_evidence = load_module("audit_evidence", repo_root / "scripts" / "audit_evidence.py")
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        session = audit_evidence.AuditSession.begin()
        session.complete()
        good = root / "good.json"
        bad = root / "bad.json"
        audit_evidence.write_audit_metadata(good, session, command_count=1)
        bad.write_text(
            json.dumps(
                {
                    "audit_start": session.audit_start,
                    "audit_end": "2099-01-01T00:00:00Z",
                    "command_count": 1,
                }
            )
            + "\n",
            encoding="utf-8",
        )
        issues = audit_evidence.verify_metadata_timestamps_consistent(
            [good, bad], session
        )
        assert issues
        assert any("bad.json" in issue for issue in issues)


def test_backend_py_compile_collects_files() -> None:
    """py_compile source discovery must run from backend directory context."""
    repo_root = Path(__file__).resolve().parents[1]
    audit_evidence = load_module("audit_evidence", repo_root / "scripts" / "audit_evidence.py")
    files = audit_evidence.backend_py_compile_files(repo_root / "backend")
    assert len(files) > 0
    assert all(path.suffix == ".py" for path in files)


def test_run_post_release_audit_blocks_when_backend_unavailable() -> None:
    """Orchestrator must fail when backend readiness is required but unavailable."""
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "scripts" / "run_post_release_audit.py"
    with tempfile.TemporaryDirectory() as temp_dir:
        validation_root = Path(temp_dir) / "validation"
        result = subprocess.run(
            [
                sys.executable,
                str(script),
                "--repo-root",
                str(repo_root),
                "--validation-root",
                str(validation_root),
                "--backend-url",
                "http://127.0.0.1:59999",
                "--require-backend-ready",
                "--run-e2e",
            ],
            capture_output=True,
            text=True,
            check=False,
            cwd=str(repo_root / "scripts"),
        )
        assert result.returncode == 1
        validation = json.loads(
            (validation_root / "validation-results.json").read_text(encoding="utf-8")
        )
        names = [item["name"] for item in validation]
        assert "backend readiness gate" in names
        assert "baseline e2e" not in names
        metadata = json.loads(
            (validation_root / "BUNDLE_METADATA.json").read_text(encoding="utf-8")
        )
        assert metadata["audit_start"] == metadata["audit_start"]
        assert metadata["audit_end"]
        results = json.loads(
            (validation_root / "validation-results.json").read_text(encoding="utf-8")
        )
        assert all(item["start_time"] == metadata["audit_start"] for item in results)
        assert all(item["end_time"] == metadata["audit_end"] for item in results)


if __name__ == "__main__":
    test_validation_results_use_exit_codes_not_stderr()
    test_exit_zero_with_stderr_warning_is_pass()
    test_nonzero_exit_with_empty_stderr_is_fail()
    test_metadata_timestamp_disagreement_is_detected()
    test_backend_py_compile_collects_files()
    test_run_post_release_audit_blocks_when_backend_unavailable()
    print("PASS")
