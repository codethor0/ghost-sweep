"""Vote model integrity tests."""

from sqlalchemy import Table, UniqueConstraint

from app.models.vote import Vote


def test_vote_table_has_unique_report_user_constraint() -> None:
    """Each user may vote only once per report."""
    vote_table = Vote.__table__
    assert isinstance(vote_table, Table)
    unique_constraints = [
        constraint
        for constraint in vote_table.constraints
        if isinstance(constraint, UniqueConstraint)
    ]
    assert len(unique_constraints) == 1
    constraint = unique_constraints[0]
    assert constraint.name == "uq_votes_report_user"
    assert set(constraint.columns.keys()) == {"report_id", "user_id"}
