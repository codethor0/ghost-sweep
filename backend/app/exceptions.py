"""Shared application exceptions."""

from fastapi import HTTPException, status


class ConflictError(HTTPException):
    """Raised when a resource already exists."""

    def __init__(self, detail: str) -> None:
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class UnauthorizedError(HTTPException):
    """Raised when authentication fails."""

    def __init__(self, detail: str = "Invalid credentials") -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class ValidationError(HTTPException):
    """Raised when submitted data fails business validation."""

    def __init__(self, detail: str) -> None:
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)


class NotFoundError(HTTPException):
    """Raised when a requested resource does not exist."""

    def __init__(self, detail: str) -> None:
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
