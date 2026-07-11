"""Add integrity constraints for audit remediation."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003_audit_remediation"
down_revision: Union[str, None] = "002_employer_claim_constraints"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _assert_no_case_collisions(table: str, column: str) -> None:
    """Fail the migration when case-equivalent duplicates exist."""
    connection = op.get_bind()
    result = connection.execute(sa.text(f"""
            SELECT lower({column}) AS normalized_value, count(*) AS collision_count
            FROM {table}
            GROUP BY lower({column})
            HAVING count(*) > 1
            LIMIT 1
            """))
    row = result.first()
    if row is not None:
        raise RuntimeError(
            f"Cannot add case-insensitive unique index on {table}.{column}; "
            "resolve case-equivalent duplicates first."
        )


def upgrade() -> None:
    """Add employer-response, duplicate-report, and identity constraints."""
    _assert_no_case_collisions("users", "email")
    _assert_no_case_collisions("users", "username")

    op.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS users_email_key")
    op.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS users_username_key")
    op.execute("CREATE UNIQUE INDEX uq_users_email_lower ON users (lower(email))")
    op.execute("CREATE UNIQUE INDEX uq_users_username_lower ON users (lower(username))")
    op.execute("""
        CREATE UNIQUE INDEX uq_employer_responses_report_user
        ON employer_responses (report_id, user_id)
        """)
    op.execute("""
        CREATE UNIQUE INDEX uq_reports_active_duplicate
        ON reports (reporter_id, job_posting_id, report_type)
        WHERE status IN ('pending', 'verified', 'disputed')
        """)


def downgrade() -> None:
    """Remove audit remediation constraints and restore original user uniqueness."""
    op.execute("DROP INDEX IF EXISTS uq_reports_active_duplicate")
    op.execute("DROP INDEX IF EXISTS uq_employer_responses_report_user")
    op.execute("DROP INDEX IF EXISTS uq_users_username_lower")
    op.execute("DROP INDEX IF EXISTS uq_users_email_lower")
    op.execute("ALTER TABLE users ADD CONSTRAINT users_email_key UNIQUE (email)")
    op.execute("ALTER TABLE users ADD CONSTRAINT users_username_key UNIQUE (username)")
