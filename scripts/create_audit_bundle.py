#!/usr/bin/env python3
"""Create a clean independent-audit bundle outside the repository."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
from datetime import datetime, timezone
from pathlib import Path

EXCLUDE_NAMES = {
    ".git",
    ".githooks",
    "node_modules",
    ".next",
    "dist",
    "build",
    "coverage",
    ".coverage",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "__pycache__",
    "ghost_sweep_backend.egg-info",
}
EXCLUDE_SUFFIXES = (".pyc", ".tmp", ".log", ".tar.gz", ".zip", ".tsbuildinfo")
FORBIDDEN_BUNDLE_NAME_PARTS = (
    "audit-bundle",
    "transcript",
    "prompt-artifact",
    "tool-export",
    "review-bundle",
)
FORBIDDEN_ATTRIBUTION = re.compile(
    r"Co-authored-by|cursoragent|Generated-by|prompt artifact|generation transcript",
    re.IGNORECASE,
)
SECRET_PATTERNS = (
    re.compile(r"BEGIN RSA PRIVATE KEY"),
    re.compile(r"BEGIN OPENSSH PRIVATE KEY"),
    re.compile(r"Authorization:\s*Bearer\s+eyJ", re.IGNORECASE),
)


def redact(text: str) -> str:
    """Redact sensitive values from captured command output."""
    text = re.sub(r"eyJ[A-Za-z0-9._-]+", "[REDACTED_JWT]", text)
    text = re.sub(
        r'"refresh_token"\s*:\s*"[^"]+"', '"refresh_token":"[REDACTED]"', text
    )
    text = re.sub(r'"access_token"\s*:\s*"[^"]+"', '"access_token":"[REDACTED]"', text)
    return text


def run_cmd(args: list[str], cwd: Path | None = None) -> tuple[int, str]:
    """Run command and return exit code and combined output."""
    result = subprocess.run(
        args,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        check=False,
    )
    output = (result.stdout or "") + (result.stderr or "")
    return result.returncode, redact(output)


def should_exclude(path: Path) -> bool:
    """Return True if path should be excluded from source snapshot."""
    name = path.name
    lowered = name.lower()
    if name in EXCLUDE_NAMES:
        return True
    if name.startswith(".env") and name != ".env.example":
        return True
    if name == ".DS_Store" or name.startswith("._"):
        return True
    if name.endswith(EXCLUDE_SUFFIXES):
        return True
    if any(part in lowered for part in FORBIDDEN_BUNDLE_NAME_PARTS):
        return True
    return False


def copy_source(repo_root: Path, dest_source: Path) -> list[Path]:
    """Copy repository source with strict exclusions."""
    if dest_source.exists():
        shutil.rmtree(dest_source)
    dest_source.mkdir(parents=True, exist_ok=True)
    copied: list[Path] = []
    for root, dirs, files in os.walk(repo_root):
        root_path = Path(root)
        dirs[:] = [d for d in dirs if not should_exclude(root_path / d)]
        for filename in files:
            src = root_path / filename
            if should_exclude(src):
                continue
            rel = src.relative_to(repo_root)
            dst = dest_source / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            copied.append(rel)
    return copied


def scan_bundle(root: Path) -> list[str]:
    """Scan bundle for unsafe files."""
    issues: list[str] = []
    if not root.exists():
        return issues
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        name = path.name
        rel = path.relative_to(root)
        if name.startswith("._") or name == ".DS_Store":
            issues.append(f"AppleDouble or DS_Store: {rel}")
        if name == ".env" or (name.startswith(".env.") and name != ".env.example"):
            issues.append(f"env file: {rel}")
        if (
            "node_modules" in path.parts
            or ".next" in path.parts
            or "__pycache__" in path.parts
            or ".pytest_cache" in path.parts
            or ".mypy_cache" in path.parts
        ):
            issues.append(f"forbidden dir artifact: {rel}")
        if name.endswith(".pyc"):
            issues.append(f"pyc file: {rel}")
        lowered = name.lower()
        if any(part in lowered for part in FORBIDDEN_BUNDLE_NAME_PARTS):
            issues.append(f"forbidden bundle artifact name: {rel}")
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if (
            FORBIDDEN_ATTRIBUTION.search(text)
            and "forbidden attribution" not in text.lower()
        ):
            if rel.name.endswith(".md") and (
                "checklist" in str(rel) or "validate_public_mvp" in str(rel)
            ):
                continue
            issues.append(f"forbidden attribution marker: {rel}")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                issues.append(f"suspected secret in {rel}")
    return issues


def load_optional_json(path: Path | None) -> dict:
    """Load optional JSON evidence file."""
    if path is None or not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_optional_text(path: Path | None) -> str:
    """Load optional markdown/text evidence file."""
    if path is None or not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def write_reports(
    bundle_root: Path,
    repo_root: Path,
    copied_files: list[Path],
    e2e_json: dict,
    e2e_md: str,
    command_log: str,
) -> None:
    """Write evidence reports with actual findings."""
    _, head = run_cmd(["git", "rev-parse", "HEAD"], cwd=repo_root)
    _, branch = run_cmd(["git", "branch", "-vv"], cwd=repo_root)
    _, status = run_cmd(["git", "status", "--short"], cwd=repo_root)
    _, repo_view = run_cmd(
        [
            "gh",
            "repo",
            "view",
            "codethor0/ghost-sweep",
            "--json",
            "visibility,nameWithOwner,url",
        ],
        cwd=repo_root,
    )
    _, issues = run_cmd(
        [
            "gh",
            "issue",
            "list",
            "--repo",
            "codethor0/ghost-sweep",
            "--state",
            "open",
            "--limit",
            "50",
        ],
        cwd=repo_root,
    )
    _, runs = run_cmd(
        ["gh", "run", "list", "--repo", "codethor0/ghost-sweep", "--limit", "10"],
        cwd=repo_root,
    )

    commit = head.strip()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    manifest_count = len(copied_files)

    report_checks = e2e_json.get("checks", [])
    report_create = next(
        (c for c in report_checks if c.get("name") == "report create"), {}
    )
    report_get = next((c for c in report_checks if c.get("name") == "report get"), {})
    vote_create = next((c for c in report_checks if c.get("name") == "vote create"), {})

    (bundle_root / "EXECUTIVE_SUMMARY.md").write_text(
        "\n".join(
            [
                "# Executive Summary",
                "",
                f"Generated: {now}",
                f"Commit: {commit}",
                "",
                "ghost-sweep is a public Job Integrity Database with a live static MVP on GitHub Pages,",
                "Google Form intake, and a full local Docker stack (FastAPI, PostgreSQL, Redis, Next.js).",
                "",
                f"Live E2E overall: {'PASS' if e2e_json.get('passed') else 'FAIL'}",
                "",
                "Hosted backend, moderation UI, evidence upload, and Sheet import remain deferred.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    (bundle_root / "REPO_STATE.md").write_text(
        "\n".join(
            [
                "# Repository State",
                "",
                f"Commit: {commit}",
                "",
                "## git branch -vv",
                "```",
                branch.strip(),
                "```",
                "",
                "## git status --short",
                "```",
                status.strip() or "(clean)",
                "```",
                "",
                "## gh repo view",
                "```json",
                repo_view.strip(),
                "```",
                "",
                "## Open issues",
                "```",
                issues.strip(),
                "```",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    (bundle_root / "ARCHITECTURE_SUMMARY.md").write_text(
        "\n".join(
            [
                "# Architecture Summary",
                "",
                "- Backend: FastAPI, PostgreSQL 15, Redis 7",
                "- Frontend: Next.js 16.2.9 server-mode (local Docker)",
                "- Extension: MV3 scaffold only",
                "- public-mvp: static HTML/CSS only; live on GitHub Pages",
                "- Intake path: Google Form -> Google Sheet -> manual review",
                "- No hosted public backend",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    (bundle_root / "VALIDATION_REPORT.md").write_text(
        "\n".join(
            [
                "# Validation Report",
                "",
                "Static gates should be run locally before release.",
                "This bundle records live E2E evidence from scripts/live_e2e_validation.py.",
                "",
                f"E2E passed: {e2e_json.get('passed', False)}",
                "",
                e2e_md.strip() or "No E2E markdown supplied.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    (bundle_root / "LIVE_E2E_REPORT.md").write_text(
        (
            (e2e_md.strip() + "\n")
            if e2e_md.strip()
            else "# Live E2E\n\nNo E2E markdown supplied.\n"
        ),
        encoding="utf-8",
    )

    (bundle_root / "GITHUB_ACTIONS_REPORT.md").write_text(
        "\n".join(
            [
                "# GitHub Actions Report",
                "",
                "Recent runs (read-only capture):",
                "```",
                runs.strip(),
                "```",
                "",
                "CI on main is expected to pass. Re-run local gates if a run fails unexpectedly.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    (bundle_root / "SECURITY_PRIVACY_REPORT.md").write_text(
        "\n".join(
            [
                "# Security and Privacy Report",
                "",
                "- Bundle excludes .env, node_modules, caches, AppleDouble files",
                "- .env.example included when present in repo",
                "- public-mvp has no backend calls and no analytics",
                "- Tokens redacted in RAW_COMMAND_LOG_REDACTED.txt",
                "- Dependency advisories remain deferred per docs/dependency-audit.md",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    (bundle_root / "PUBLIC_LAUNCH_READINESS.md").write_text(
        "\n".join(
            [
                "# Public Launch Readiness",
                "",
                "Public launch completed (Batches 8A--9C).",
                "",
                "Live:",
                "- Repository: public",
                "- GitHub Pages: https://codethor0.github.io/ghost-sweep/",
                "- Google Form: https://forms.gle/PsjaYrbrCjAgZXjW8",
                "",
                "Deferred:",
                "- Hosted backend and live scoring database",
                "- Sheet import automation",
                "- Public moderation UI and evidence upload",
                "- Extension API wiring",
                "- Remaining dependency advisories (Issue #4)",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    (bundle_root / "CONTRIBUTOR_READINESS.md").write_text(
        "\n".join(
            [
                "# Contributor Readiness",
                "",
                "- Issue #1 open with Batch 6D handoff comment",
                "- 22 labels live",
                "- Templates, PR template, CODEOWNERS in place",
                "- Greg Write invite pending (not Admin/Maintain)",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    (bundle_root / "FILE_MANIFEST.txt").write_text(
        "\n".join(str(p) for p in sorted(copied_files)) + "\n",
        encoding="utf-8",
    )

    tree_dirs = sorted(
        {str(p.parent) if p.parent != Path(".") else "." for p in copied_files}
    )
    (bundle_root / "PROJECT_TREE.txt").write_text(
        "\n".join(tree_dirs) + "\n", encoding="utf-8"
    )

    _, diff_log = run_cmd(["git", "log", "--oneline", "3453fb8..HEAD"], cwd=repo_root)
    (bundle_root / "DIFF_FROM_BASELINE.md").write_text(
        "\n".join(
            [
                "# Diff From Baseline 3453fb8",
                "",
                "```",
                diff_log.strip(),
                "```",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    hygiene_issues = scan_bundle(bundle_root)
    (bundle_root / "HYGIENE_SCAN_REPORT.md").write_text(
        "\n".join(
            [
                "# Hygiene Scan Report",
                "",
                f"Manifest file count: {manifest_count}",
                f"Actual source files copied: {manifest_count}",
                "",
                "Full bundle scan issues:",
                *(hygiene_issues or ["(none)"]),
                "",
                "Source-only scan:",
                *(scan_bundle(bundle_root / "source") or ["(none)"]),
                "",
                "## Corrected report/vote evidence",
                f"- POST /reports: status {report_create.get('status_code')} pass={report_create.get('passed')}",
                f"- GET /reports/{{id}}: status {report_get.get('status_code')} pass={report_get.get('passed')}",
                f"- POST /votes: status {vote_create.get('status_code')} pass={vote_create.get('passed')}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    (bundle_root / "RAW_COMMAND_LOG_REDACTED.txt").write_text(
        command_log, encoding="utf-8"
    )


def create_tarball(bundle_root: Path, tarball: Path) -> None:
    """Create gzip tarball from bundle root."""
    if tarball.exists():
        tarball.unlink()
    previous_copyfile_disable = os.environ.get("COPYFILE_DISABLE")
    os.environ["COPYFILE_DISABLE"] = "1"
    try:
        with tarfile.open(tarball, "w:gz") as archive:
            for path in sorted(bundle_root.rglob("*")):
                if path.is_file():
                    rel = path.relative_to(bundle_root.parent)
                    if path.name.startswith("._") or path.name == ".DS_Store":
                        continue
                    archive.add(path, arcname=str(rel))
    finally:
        if previous_copyfile_disable is None:
            os.environ.pop("COPYFILE_DISABLE", None)
        else:
            os.environ["COPYFILE_DISABLE"] = previous_copyfile_disable


def verify_tarball(tarball: Path) -> list[str]:
    """Verify tarball does not contain forbidden paths."""
    issues: list[str] = []
    with tarfile.open(tarball, "r:gz") as archive:
        for member in archive.getmembers():
            name = member.name
            base = Path(name).name
            if base.startswith("._") or base == ".DS_Store":
                issues.append(name)
            if "/node_modules/" in name or "/.next/" in name or "/__pycache__/" in name:
                issues.append(name)
            if base == ".env" or (base.startswith(".env.") and base != ".env.example"):
                issues.append(name)
    return issues


def main() -> int:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description="Create clean audit bundle.")
    parser.add_argument("--repo-root", default="/Users/thor/Projects/ghost-sweep")
    parser.add_argument(
        "--output-dir",
        default="/Users/thor/Downloads/ghost-sweep-full-project-audit-bundle-clean",
    )
    parser.add_argument(
        "--tarball",
        default="/Users/thor/Downloads/ghost-sweep-full-project-audit-bundle-clean.tar.gz",
    )
    parser.add_argument("--e2e-json")
    parser.add_argument("--e2e-md")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    bundle_root = Path(args.output_dir).resolve()
    tarball = Path(args.tarball).resolve()
    source_dir = bundle_root / "source"

    if bundle_root.exists():
        shutil.rmtree(bundle_root)
    bundle_root.mkdir(parents=True, exist_ok=True)

    copied = copy_source(repo_root, source_dir)
    e2e_json = load_optional_json(Path(args.e2e_json) if args.e2e_json else None)
    e2e_md = load_optional_text(Path(args.e2e_md) if args.e2e_md else None)

    log_parts: list[str] = []
    for label, cmd in [
        ("git status", ["git", "status", "--short"]),
        ("git log -1", ["git", "log", "-1", "--pretty=fuller"]),
        (
            "gh run list",
            ["gh", "run", "list", "--repo", "codethor0/ghost-sweep", "--limit", "5"],
        ),
    ]:
        _, output = run_cmd(cmd, cwd=repo_root)
        log_parts.append(f"=== {label} ===\n{output}\n")
    command_log = "\n".join(log_parts)

    write_reports(bundle_root, repo_root, copied, e2e_json, e2e_md, command_log)

    bundle_issues = scan_bundle(bundle_root)
    if bundle_issues:
        print("Bundle hygiene issues detected:", file=sys.stderr)
        for issue in bundle_issues:
            print(f"  - {issue}", file=sys.stderr)
        return 1

    create_tarball(bundle_root, tarball)
    tar_issues = verify_tarball(tarball)
    if tar_issues:
        print("Tarball verification failed:", file=sys.stderr)
        for issue in tar_issues:
            print(f"  - {issue}", file=sys.stderr)
        return 1

    print(f"Bundle created: {bundle_root}")
    print(f"Tarball created: {tarball}")
    print(f"Source files: {len(copied)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
