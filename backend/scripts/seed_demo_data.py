"""Local development demo seed for ghost-sweep.

Creates a demo company and active job posting when run in development only.
Idempotent: skips creation when demo records already exist.

Usage (from backend directory with DATABASE_URL configured):

    python3.11 scripts/seed_demo_data.py

Do not run in production or staging.
"""

from __future__ import annotations

import asyncio
import sys
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select

from app.config import get_settings
from app.database import SessionLocal
from app.models.company import Company
from app.models.enums import PostingSource, PostingStatus, VerifiedStatus
from app.models.job_posting import JobPosting

DEMO_COMPANY_NAME = "ghost-sweep Demo Company"
DEMO_COMPANY_DOMAIN = "demo.ghost-sweep.local"
DEMO_POSTING_URL = "https://demo.ghost-sweep.local/jobs/demo-engineer"
DEMO_POSTING_TITLE = "Demo Software Engineer"


async def seed_demo_data() -> None:
    """Insert demo company and job posting when missing."""
    settings = get_settings()
    if settings.environment != "development":
        print(
            f"Refusing to seed: ENVIRONMENT is {settings.environment!r}; "
            "only development is allowed.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    now = datetime.now(tz=UTC)
    async with SessionLocal() as session:
        company = await session.scalar(select(Company).where(Company.name == DEMO_COMPANY_NAME))
        if company is None:
            company = Company(
                name=DEMO_COMPANY_NAME,
                domain=DEMO_COMPANY_DOMAIN,
                industry="Technology",
                size="1-50",
                locations=["Remote"],
                integrity_score=Decimal("50.0"),
                verified_status=VerifiedStatus.UNVERIFIED,
                total_postings=1,
                total_hires=0,
                report_count=0,
            )
            session.add(company)
            await session.flush()
            print(f"Created demo company: {company.id}")
        else:
            print(f"Demo company already exists: {company.id}")

        posting = await session.scalar(select(JobPosting).where(JobPosting.url == DEMO_POSTING_URL))
        if posting is None:
            posting = JobPosting(
                company_id=company.id,
                title=DEMO_POSTING_TITLE,
                description="Local demo posting for contributor validation.",
                url=DEMO_POSTING_URL,
                source=PostingSource.OTHER,
                status=PostingStatus.ACTIVE,
                ghost_risk_score=Decimal("50.0"),
                repost_count=0,
                detected_at=now,
                last_seen_at=now,
            )
            session.add(posting)
            await session.flush()
            print(f"Created demo job posting: {posting.id}")
        else:
            print(f"Demo job posting already exists: {posting.id}")

        await session.commit()


def main() -> None:
    """Run the demo seed."""
    asyncio.run(seed_demo_data())


if __name__ == "__main__":
    main()
