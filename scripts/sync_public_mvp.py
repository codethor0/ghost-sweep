#!/usr/bin/env python3
"""Copy canonical public-mvp files to repository root for GitHub Pages."""

from __future__ import annotations

import filecmp
import shutil
import sys
from pathlib import Path

MIRROR_FILES = (
    "index.html",
    "styles.css",
    ".nojekyll",
)


def sync_public_mvp(repo_root: Path) -> int:
    """Copy public-mvp assets to root and verify they match."""
    source_dir = repo_root / "public-mvp"
    missing = [name for name in MIRROR_FILES if not (source_dir / name).exists()]
    if missing:
        print(f"Missing canonical files under public-mvp/: {', '.join(missing)}", file=sys.stderr)
        return 1

    for name in MIRROR_FILES:
        src = source_dir / name
        dst = repo_root / name
        shutil.copy2(src, dst)

    mismatches: list[str] = []
    for name in MIRROR_FILES:
        src = source_dir / name
        dst = repo_root / name
        if not dst.exists() or not filecmp.cmp(src, dst, shallow=False):
            mismatches.append(name)

    if mismatches:
        print(
            "Root mirror verification failed for: " + ", ".join(mismatches),
            file=sys.stderr,
        )
        return 1

    print("public-mvp mirror synced to repository root")
    for name in MIRROR_FILES:
        print(f"  - {name}")
    return 0


def main() -> int:
    """CLI entrypoint."""
    repo_root = Path(__file__).resolve().parent.parent
    return sync_public_mvp(repo_root)


if __name__ == "__main__":
    sys.exit(main())
