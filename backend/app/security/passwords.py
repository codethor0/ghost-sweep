"""Password hashing utilities."""

import bcrypt


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password with bcrypt.

    Args:
        plain_password: User supplied password.

    Returns:
        str: bcrypt hash string.
    """
    password_bytes = plain_password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify a plaintext password against a stored hash.

    Args:
        plain_password: Candidate password.
        password_hash: Stored bcrypt hash.

    Returns:
        bool: True when the password matches.
    """
    return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))
