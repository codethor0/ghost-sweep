"""Password validation helpers aligned with bcrypt input limits."""

BCRYPT_MAX_PASSWORD_BYTES = 72


def password_utf8_byte_length(password: str) -> int:
    """Return the UTF-8 byte length of a password string."""
    return len(password.encode("utf-8"))


def validate_password_byte_length(password: str) -> None:
    """Reject passwords whose UTF-8 encoding exceeds bcrypt's supported boundary.

    Args:
        password: Candidate password.

    Raises:
        ValueError: When the password exceeds the bcrypt byte limit.
    """
    if password_utf8_byte_length(password) > BCRYPT_MAX_PASSWORD_BYTES:
        raise ValueError(f"Password must be {BCRYPT_MAX_PASSWORD_BYTES} UTF-8 bytes or fewer")
