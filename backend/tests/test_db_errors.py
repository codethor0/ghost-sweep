"""Database integrity error mapping tests."""

from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import IntegrityError

from app.db_errors import (
    EMPLOYER_CLAIM_COMPANY_APPROVED,
    EMPLOYER_CLAIM_USER_COMPANY_PENDING,
    USER_EMAIL_UNIQUE,
    VOTE_REPORT_USER_UNIQUE,
    conflict_detail_from_integrity_error,
    raise_conflict_from_integrity_error,
)
from app.exceptions import ConflictError


def _integrity_error(constraint_name: str) -> IntegrityError:
    """Build an IntegrityError with a mocked PostgreSQL constraint name."""
    orig = MagicMock()
    orig.diag.constraint_name = constraint_name
    return IntegrityError("INSERT", {}, orig)


def test_conflict_detail_maps_vote_unique_constraint() -> None:
    """Vote unique constraint violations should map to vote conflict detail."""
    detail = conflict_detail_from_integrity_error(_integrity_error(VOTE_REPORT_USER_UNIQUE))
    assert detail == "Vote already recorded for this report"


def test_conflict_detail_maps_user_email_unique_constraint() -> None:
    """User email unique constraint violations should map to email conflict detail."""
    detail = conflict_detail_from_integrity_error(_integrity_error(USER_EMAIL_UNIQUE))
    assert detail == "Email already registered"


def test_conflict_detail_maps_employer_claim_pending_constraint() -> None:
    """Pending employer claim unique violations should map to pending conflict detail."""
    detail = conflict_detail_from_integrity_error(
        _integrity_error(EMPLOYER_CLAIM_USER_COMPANY_PENDING)
    )
    assert detail == "Pending claim already exists for this company"


def test_conflict_detail_maps_employer_claim_approved_constraint() -> None:
    """Approved employer claim unique violations should map to approved conflict detail."""
    detail = conflict_detail_from_integrity_error(_integrity_error(EMPLOYER_CLAIM_COMPANY_APPROVED))
    assert detail == "Company already has an approved employer claim"


def test_raise_conflict_from_integrity_error_raises_conflict_error() -> None:
    """Known unique violations should raise ConflictError."""
    with pytest.raises(ConflictError, match="Vote already recorded"):
        raise_conflict_from_integrity_error(_integrity_error(VOTE_REPORT_USER_UNIQUE))


def test_raise_conflict_from_integrity_error_reraises_unknown_violation() -> None:
    """Unknown integrity errors should be re-raised unchanged."""
    exc = _integrity_error("some_other_constraint")
    with pytest.raises(IntegrityError):
        raise_conflict_from_integrity_error(exc)
