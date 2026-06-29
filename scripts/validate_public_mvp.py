#!/usr/bin/env python3
"""Validate the public-mvp static site before GitHub Pages deployment."""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PUBLIC_MVP = REPO_ROOT / "public-mvp"

REQUIRED_FILES = (
    PUBLIC_MVP / "index.html",
    PUBLIC_MVP / "styles.css",
    PUBLIC_MVP / ".nojekyll",
)

FORBIDDEN_ATTRIBUTION = re.compile(
    r"Co-authored-by|Cursor|cursoragent|Generated-by|ChatGPT|Claude|AI assistant",
    re.IGNORECASE,
)

FORBIDDEN_SECRET_PATTERNS = (
    re.compile(r"JWT_SECRET_KEY\s*=\s*[^\s#]+", re.IGNORECASE),
    re.compile(r"postgresql\+asyncpg://[^\s\"']+", re.IGNORECASE),
    re.compile(r"redis://[^\s\"']+", re.IGNORECASE),
    re.compile(r"Bearer\s+[A-Za-z0-9\-_.]+"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
)

LOCALHOST_API_PATTERN = re.compile(
    r"https?://(?:localhost|127\.0\.0\.1|backend:\d+)(?:[/:\s\"']|$)",
    re.IGNORECASE,
)

FORM_PLACEHOLDER = "https://forms.gle/REPLACE_WITH_REAL_FORM_URL"

EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F1E0-\U0001F1FF"
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "]+",
    flags=re.UNICODE,
)

FORBIDDEN_FILENAMES = {".env", ".DS_Store"}
FORBIDDEN_SUFFIXES = (".zip", ".tar.gz")


def fail(message: str) -> None:
    """Print a failure message and exit with code 1."""
    print(f"FAIL: {message}", file=sys.stderr)
    sys.exit(1)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def validate_required_files() -> None:
    for path in REQUIRED_FILES:
        if not path.is_file():
            fail(f"Missing required file: {path.relative_to(REPO_ROOT)}")


def validate_no_forbidden_files() -> None:
    for path in PUBLIC_MVP.rglob("*"):
        if not path.is_file():
            continue
        name = path.name
        if name in FORBIDDEN_FILENAMES or name.startswith("._"):
            fail(f"Forbidden file in public-mvp: {path.relative_to(REPO_ROOT)}")
        if any(name.endswith(suffix) for suffix in FORBIDDEN_SUFFIXES):
            fail(f"Forbidden archive in public-mvp: {path.relative_to(REPO_ROOT)}")


def validate_index_content(index_html: str) -> None:
    if "Submit a report" not in index_html:
        fail("index.html missing 'Submit a report' CTA text")
    if FORM_PLACEHOLDER not in index_html:
        fail(f"index.html missing placeholder Google Form URL: {FORM_PLACEHOLDER}")
    if LOCALHOST_API_PATTERN.search(index_html):
        fail("index.html contains localhost or backend API URL")
    for pattern in FORBIDDEN_SECRET_PATTERNS:
        if pattern.search(index_html):
            fail("index.html contains a suspected secret pattern")
    if FORBIDDEN_ATTRIBUTION.search(index_html):
        fail("index.html contains forbidden attribution string")
    if EMOJI_PATTERN.search(index_html):
        fail("index.html contains emoji characters")


def validate_styles(styles_css: str) -> None:
    if LOCALHOST_API_PATTERN.search(styles_css):
        fail("styles.css contains localhost or backend API URL")
    if FORBIDDEN_ATTRIBUTION.search(styles_css):
        fail("styles.css contains forbidden attribution string")
    if EMOJI_PATTERN.search(styles_css):
        fail("styles.css contains emoji characters")


def main() -> None:
    validate_required_files()
    validate_no_forbidden_files()

    index_html = read_text(PUBLIC_MVP / "index.html")
    styles_css = read_text(PUBLIC_MVP / "styles.css")

    validate_index_content(index_html)
    validate_styles(styles_css)

    print("PASS: public-mvp validation succeeded")
    print(f"  - Required files present under {PUBLIC_MVP.relative_to(REPO_ROOT)}/")
    print("  - No localhost backend API URLs")
    print(f"  - Placeholder Google Form URL present: {FORM_PLACEHOLDER}")
    print("  - No forbidden attribution strings")
    print("  - No suspected secrets")
    print("  - No emoji characters")
    print("  - No forbidden files (.env, archives, AppleDouble)")


if __name__ == "__main__":
    main()
