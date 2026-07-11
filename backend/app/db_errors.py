"""Map database integrity errors to application-level conflicts."""

from sqlalchemy.exc import IntegrityError

from app.exceptions import ConflictError

USER_EMAIL_UNIQUE = "users_email_key"
USER_USERNAME_UNIQUE = "users_username_key"
USER_EMAIL_LOWER_UNIQUE = "uq_users_email_lower"
USER_USERNAME_LOWER_UNIQUE = "uq_users_username_lower"
VOTE_REPORT_USER_UNIQUE = "uq_votes_report_user"
EMPLOYER_CLAIM_COMPANY_APPROVED = "uq_employer_claims_company_approved"
EMPLOYER_CLAIM_USER_COMPANY_PENDING = "uq_employer_claims_user_company_pending"
EMPLOYER_RESPONSE_REPORT_USER_UNIQUE = "uq_employer_responses_report_user"
REPORT_ACTIVE_DUPLICATE_UNIQUE = "uq_reports_active_duplicate"


def _unique_constraint_name(exc: IntegrityError) -> str | None:
    """Return the PostgreSQL unique constraint name when available."""
    orig = getattr(exc, "orig", None)
    if orig is None:
        return None
    diag = getattr(orig, "diag", None)
    if diag is None:
        return None
    constraint_name = getattr(diag, "constraint_name", None)
    if constraint_name is None:
        return None
    return str(constraint_name)


def conflict_detail_from_integrity_error(exc: IntegrityError) -> str | None:
    """Map a unique constraint violation to a client-facing conflict message."""
    constraint_name = _unique_constraint_name(exc)
    if constraint_name == USER_EMAIL_UNIQUE:
        return "Email already registered"
    if constraint_name == USER_USERNAME_UNIQUE:
        return "Username already taken"
    if constraint_name in {USER_EMAIL_LOWER_UNIQUE, USER_EMAIL_UNIQUE}:
        return "Email already registered"
    if constraint_name in {USER_USERNAME_LOWER_UNIQUE, USER_USERNAME_UNIQUE}:
        return "Username already taken"
    if constraint_name == VOTE_REPORT_USER_UNIQUE:
        return "Vote already recorded for this report"
    if constraint_name == EMPLOYER_CLAIM_COMPANY_APPROVED:
        return "Company already has an approved employer claim"
    if constraint_name == EMPLOYER_CLAIM_USER_COMPANY_PENDING:
        return "Pending claim already exists for this company"
    if constraint_name == EMPLOYER_RESPONSE_REPORT_USER_UNIQUE:
        return "An employer response from this account already exists for this report"
    if constraint_name == REPORT_ACTIVE_DUPLICATE_UNIQUE:
        return "A similar report from this account is already active for this posting"
    return None


def raise_conflict_from_integrity_error(exc: IntegrityError) -> None:
    """Re-raise a unique constraint violation as ConflictError when recognized."""
    detail = conflict_detail_from_integrity_error(exc)
    if detail is not None:
        raise ConflictError(detail) from exc
    raise exc
