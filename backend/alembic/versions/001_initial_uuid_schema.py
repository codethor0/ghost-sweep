"""Initial UUID schema with PostgreSQL native ENUM types."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_initial_uuid_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

VERIFIED_STATUS_ENUM = postgresql.ENUM(
    "verified",
    "unverified",
    "disputed",
    name="verified_status_enum",
    create_type=False,
)
POSTING_SOURCE_ENUM = postgresql.ENUM(
    "linkedin",
    "indeed",
    "glassdoor",
    "company_site",
    "other",
    name="posting_source_enum",
    create_type=False,
)
POSTING_STATUS_ENUM = postgresql.ENUM(
    "active",
    "filled",
    "removed",
    "suspected_ghost",
    "disputed",
    name="posting_status_enum",
    create_type=False,
)
REPORT_TYPE_ENUM = postgresql.ENUM(
    "ghost_job",
    "no_response",
    "scam",
    "data_harvest",
    "repost_loop",
    "stale_posting",
    "fake_interview",
    name="report_type_enum",
    create_type=False,
)
REPORT_STATUS_ENUM = postgresql.ENUM(
    "pending",
    "verified",
    "dismissed",
    "disputed",
    name="report_status_enum",
    create_type=False,
)
CLAIM_STATUS_ENUM = postgresql.ENUM(
    "pending",
    "approved",
    "rejected",
    name="claim_status_enum",
    create_type=False,
)
VOTE_VALUE_ENUM = postgresql.ENUM(
    "up",
    "down",
    name="vote_value_enum",
    create_type=False,
)
SNAPSHOT_ENTITY_TYPE_ENUM = postgresql.ENUM(
    "company",
    "job_posting",
    name="snapshot_entity_type_enum",
    create_type=False,
)

ENUM_TYPES = (
    VERIFIED_STATUS_ENUM,
    POSTING_SOURCE_ENUM,
    POSTING_STATUS_ENUM,
    REPORT_TYPE_ENUM,
    REPORT_STATUS_ENUM,
    CLAIM_STATUS_ENUM,
    VOTE_VALUE_ENUM,
    SNAPSHOT_ENTITY_TYPE_ENUM,
)


def upgrade() -> None:
    """Create PostgreSQL ENUM types and UUID schema tables."""
    bind = op.get_bind()
    for enum_type in ENUM_TYPES:
        enum_type.create(bind, checkfirst=True)

    op.create_table(
        "companies",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("domain", sa.String(length=255), nullable=True),
        sa.Column("industry", sa.String(length=128), nullable=True),
        sa.Column("size", sa.String(length=64), nullable=True),
        sa.Column(
            "locations",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "integrity_score",
            sa.Numeric(precision=5, scale=2),
            server_default=sa.text("50.0"),
            nullable=True,
        ),
        sa.Column(
            "verified_status",
            VERIFIED_STATUS_ENUM,
            server_default=sa.text("'unverified'"),
            nullable=False,
        ),
        sa.Column("total_postings", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("total_hires", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("report_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_companies_domain"), "companies", ["domain"], unique=False)
    op.create_index(
        op.f("ix_companies_verified_status"), "companies", ["verified_status"], unique=False
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column(
            "reputation_score",
            sa.Numeric(precision=6, scale=2),
            server_default=sa.text("0.0"),
            nullable=True,
        ),
        sa.Column(
            "report_weight",
            sa.Numeric(precision=4, scale=2),
            server_default=sa.text("1.0"),
            nullable=True,
        ),
        sa.Column("is_employer", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("is_admin", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("employer_company_id", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["employer_company_id"], ["companies.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("username"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=False)
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=False)

    op.create_table(
        "job_postings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("url", sa.String(length=1024), nullable=False),
        sa.Column(
            "source",
            POSTING_SOURCE_ENUM,
            server_default=sa.text("'other'"),
            nullable=False,
        ),
        sa.Column("posted_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status",
            POSTING_STATUS_ENUM,
            server_default=sa.text("'active'"),
            nullable=False,
        ),
        sa.Column(
            "ghost_risk_score",
            sa.Numeric(precision=5, scale=2),
            server_default=sa.text("50.0"),
            nullable=True,
        ),
        sa.Column("repost_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("original_posting_id", sa.Uuid(), nullable=True),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["original_posting_id"], ["job_postings.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("url"),
    )
    op.create_index(
        op.f("ix_job_postings_company_id"), "job_postings", ["company_id"], unique=False
    )
    op.create_index(op.f("ix_job_postings_source"), "job_postings", ["source"], unique=False)
    op.create_index(op.f("ix_job_postings_status"), "job_postings", ["status"], unique=False)
    op.create_index(op.f("ix_job_postings_title"), "job_postings", ["title"], unique=False)

    op.create_table(
        "reports",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("job_posting_id", sa.Uuid(), nullable=False),
        sa.Column("reporter_id", sa.Uuid(), nullable=True),
        sa.Column("report_type", REPORT_TYPE_ENUM, nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "status",
            REPORT_STATUS_ENUM,
            server_default=sa.text("'pending'"),
            nullable=False,
        ),
        sa.Column(
            "confidence_score",
            sa.Numeric(precision=5, scale=2),
            server_default=sa.text("0.0"),
            nullable=True,
        ),
        sa.Column(
            "verification_votes",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["job_posting_id"], ["job_postings.id"]),
        sa.ForeignKeyConstraint(["reporter_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_reports_job_posting_id"), "reports", ["job_posting_id"], unique=False)
    op.create_index(op.f("ix_reports_report_type"), "reports", ["report_type"], unique=False)
    op.create_index(op.f("ix_reports_reporter_id"), "reports", ["reporter_id"], unique=False)
    op.create_index(op.f("ix_reports_status"), "reports", ["status"], unique=False)

    op.create_table(
        "evidence_files",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("report_id", sa.Uuid(), nullable=False),
        sa.Column("file_url", sa.String(length=1024), nullable=False),
        sa.Column("file_type", sa.String(length=64), nullable=False),
        sa.Column("sha256_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "uploaded_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["report_id"], ["reports.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_evidence_files_report_id"), "evidence_files", ["report_id"], unique=False
    )
    op.create_index(
        op.f("ix_evidence_files_sha256_hash"), "evidence_files", ["sha256_hash"], unique=False
    )

    op.create_table(
        "votes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("report_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("vote", VOTE_VALUE_ENUM, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["report_id"], ["reports.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("report_id", "user_id", name="uq_votes_report_user"),
    )
    op.create_index(op.f("ix_votes_report_id"), "votes", ["report_id"], unique=False)
    op.create_index(op.f("ix_votes_user_id"), "votes", ["user_id"], unique=False)

    op.create_table(
        "employer_claims",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "status",
            CLAIM_STATUS_ENUM,
            server_default=sa.text("'pending'"),
            nullable=False,
        ),
        sa.Column(
            "verification_documents",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_employer_claims_company_id"), "employer_claims", ["company_id"], unique=False
    )
    op.create_index(op.f("ix_employer_claims_status"), "employer_claims", ["status"], unique=False)
    op.create_index(
        op.f("ix_employer_claims_user_id"), "employer_claims", ["user_id"], unique=False
    )

    op.create_table(
        "employer_responses",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("report_id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("response_text", sa.Text(), nullable=False),
        sa.Column(
            "evidence_urls",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["report_id"], ["reports.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_employer_responses_company_id"),
        "employer_responses",
        ["company_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_employer_responses_report_id"),
        "employer_responses",
        ["report_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_employer_responses_user_id"), "employer_responses", ["user_id"], unique=False
    )

    op.create_table(
        "score_snapshots",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("entity_type", SNAPSHOT_ENTITY_TYPE_ENUM, nullable=False),
        sa.Column("entity_id", sa.Uuid(), nullable=False),
        sa.Column("score", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("breakdown", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_score_snapshots_entity_id"), "score_snapshots", ["entity_id"], unique=False
    )
    op.create_index(
        op.f("ix_score_snapshots_entity_type"),
        "score_snapshots",
        ["entity_type"],
        unique=False,
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("actor_user_id", sa.Uuid(), nullable=True),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.Uuid(), nullable=False),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_logs_action"), "audit_logs", ["action"], unique=False)
    op.create_index(
        op.f("ix_audit_logs_actor_user_id"), "audit_logs", ["actor_user_id"], unique=False
    )
    op.create_index(op.f("ix_audit_logs_entity_id"), "audit_logs", ["entity_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_entity_type"), "audit_logs", ["entity_type"], unique=False)


def downgrade() -> None:
    """Drop UUID schema tables and PostgreSQL ENUM types."""
    op.drop_index(op.f("ix_audit_logs_entity_type"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_entity_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_actor_user_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_action"), table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index(op.f("ix_score_snapshots_entity_type"), table_name="score_snapshots")
    op.drop_index(op.f("ix_score_snapshots_entity_id"), table_name="score_snapshots")
    op.drop_table("score_snapshots")

    op.drop_index(op.f("ix_employer_responses_user_id"), table_name="employer_responses")
    op.drop_index(op.f("ix_employer_responses_report_id"), table_name="employer_responses")
    op.drop_index(op.f("ix_employer_responses_company_id"), table_name="employer_responses")
    op.drop_table("employer_responses")

    op.drop_index(op.f("ix_employer_claims_user_id"), table_name="employer_claims")
    op.drop_index(op.f("ix_employer_claims_status"), table_name="employer_claims")
    op.drop_index(op.f("ix_employer_claims_company_id"), table_name="employer_claims")
    op.drop_table("employer_claims")

    op.drop_index(op.f("ix_votes_user_id"), table_name="votes")
    op.drop_index(op.f("ix_votes_report_id"), table_name="votes")
    op.drop_table("votes")

    op.drop_index(op.f("ix_evidence_files_sha256_hash"), table_name="evidence_files")
    op.drop_index(op.f("ix_evidence_files_report_id"), table_name="evidence_files")
    op.drop_table("evidence_files")

    op.drop_index(op.f("ix_reports_status"), table_name="reports")
    op.drop_index(op.f("ix_reports_reporter_id"), table_name="reports")
    op.drop_index(op.f("ix_reports_report_type"), table_name="reports")
    op.drop_index(op.f("ix_reports_job_posting_id"), table_name="reports")
    op.drop_table("reports")

    op.drop_index(op.f("ix_job_postings_title"), table_name="job_postings")
    op.drop_index(op.f("ix_job_postings_status"), table_name="job_postings")
    op.drop_index(op.f("ix_job_postings_source"), table_name="job_postings")
    op.drop_index(op.f("ix_job_postings_company_id"), table_name="job_postings")
    op.drop_table("job_postings")

    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")

    op.drop_index(op.f("ix_companies_verified_status"), table_name="companies")
    op.drop_index(op.f("ix_companies_domain"), table_name="companies")
    op.drop_table("companies")

    bind = op.get_bind()
    for enum_type in reversed(ENUM_TYPES):
        enum_type.drop(bind, checkfirst=True)
