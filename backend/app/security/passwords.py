"""Password hashing utilities."""

import bcrypt


def hash_password(password: str) -> str:
    """Hash a plaintext password with bcrypt.

    Args:
        password: User supplied password.

    Returns:
        str: Stored bcrypt hash.
    """
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a plaintext password against a stored hash.

    Args:
        password: Candidate password.
        password_hash: Stored bcrypt hash.

    Returns:
        bool: True when the password matches.
    """
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
