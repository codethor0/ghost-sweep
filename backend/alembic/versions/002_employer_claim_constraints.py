"""Add partial unique indexes for employer claim invariants."""

from typing import Sequence, Union

from alembic import op

revision: str = "002_employer_claim_constraints"
down_revision: Union[str, None] = "001_initial_uuid_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create partial unique indexes for approved and pending employer claims."""
    op.execute("""
        CREATE UNIQUE INDEX uq_employer_claims_company_approved
        ON employer_claims (company_id)
        WHERE status = 'approved'
        """)
    op.execute("""
        CREATE UNIQUE INDEX uq_employer_claims_user_company_pending
        ON employer_claims (user_id, company_id)
        WHERE status = 'pending'
        """)


def downgrade() -> None:
    """Remove employer claim partial unique indexes."""
    op.execute("DROP INDEX IF EXISTS uq_employer_claims_user_company_pending")
    op.execute("DROP INDEX IF EXISTS uq_employer_claims_company_approved")
