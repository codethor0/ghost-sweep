#!/usr/bin/env python3
"""Regression tests for audit bundle macOS metadata exclusion."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path


def test_tarball_excludes_appledouble_files() -> None:
    """Tarball creation must exclude AppleDouble metadata files."""
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "scripts" / "create_audit_bundle.py"
    with tempfile.TemporaryDirectory() as temp_dir:
        bundle_root = Path(temp_dir) / "sample-bundle"
        bundle_root.mkdir()
        (bundle_root / "README.txt").write_text("sample", encoding="utf-8")
        (bundle_root / "._README.txt").write_bytes(b"appledouble")
        tarball = Path(temp_dir) / "sample-bundle.tar.gz"

        env = os.environ.copy()
        env["COPYFILE_DISABLE"] = "1"
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "from pathlib import Path; "
                    "import importlib.util; "
                    f"spec=importlib.util.spec_from_file_location('cab', '{script}'); "
                    "module=importlib.util.module_from_spec(spec); "
                    "spec.loader.exec_module(module); "
                    f"module.create_tarball(Path('{bundle_root}'), Path('{tarball}'))"
                ),
            ],
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )
        assert result.returncode == 0, result.stderr

        with tarfile.open(tarball, "r:gz") as archive:
            names = archive.getnames()
        assert any(name.endswith("README.txt") for name in names)
        assert not any("/._" in name or name.startswith("._") for name in names)


if __name__ == "__main__":
    test_tarball_excludes_appledouble_files()
    print("PASS")


def test_scan_bundle_allows_contributor_onboarding_policy_text() -> None:
    """Policy docs that mention forbidden markers in guidance must not fail hygiene scans."""
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "scripts" / "create_audit_bundle.py"
    import importlib.util

    spec = importlib.util.spec_from_file_location("cab", script)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    with tempfile.TemporaryDirectory() as temp_dir:
        bundle_root = Path(temp_dir) / "sample-bundle"
        source_dir = bundle_root / "source"
        source_dir.mkdir(parents=True)
        onboarding = repo_root / "docs" / "contributor-onboarding.md"
        shutil.copy2(onboarding, source_dir / "contributor-onboarding.md")
        shutil.copy2(script, source_dir / "create_audit_bundle.py")
        issues = module.scan_bundle(bundle_root)
        assert issues == []
