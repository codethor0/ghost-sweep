"""Canonical normalization for user identity fields."""

import re

_USERNAME_PATTERN = re.compile(r"^[a-z0-9_\-]+$")


def normalize_email(email: str) -> str:
    """Normalize an email address for storage and lookup.

    Args:
        email: Raw email input.

    Returns:
        str: Trimmed, lowercased email.
    """
    return email.strip().lower()


def normalize_username(username: str) -> str:
    """Normalize a username for storage and lookup.

    Usernames are stored and compared case-insensitively by lowercasing.

    Args:
        username: Raw username input.

    Returns:
        str: Trimmed, lowercased username.

    Raises:
        ValueError: When the normalized username is empty or invalid.
    """
    normalized = username.strip().lower()
    if not normalized:
        raise ValueError("Username must be non-empty")
    if not _USERNAME_PATTERN.fullmatch(normalized):
        raise ValueError("Username must contain only letters, numbers, underscores, and hyphens")
    return normalized


def normalize_login_identifier(identifier: str) -> str:
    """Normalize a login identifier for lookup.

    Email-like identifiers are lowercased. Usernames follow username rules.

    Args:
        identifier: Email or username supplied at login.

    Returns:
        str: Normalized identifier.
    """
    trimmed = identifier.strip()
    if "@" in trimmed:
        return normalize_email(trimmed)
    return normalize_username(trimmed)
