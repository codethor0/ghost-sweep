"""Employer claim API tests."""

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.company import Company
from app.models.employer_claim import EmployerClaim
from app.models.enums import ClaimStatus

VERIFICATION_DOCUMENT = "https://example.com/verification/domain-control.txt"


def _claim_payload(company_id: str) -> dict[str, object]:
    """Build a valid employer claim submission payload."""
    return {
        "company_id": company_id,
        "verification_documents": [VERIFICATION_DOCUMENT],
    }


async def _submit_claim(
    client: AsyncClient,
    company_id: str,
    headers: dict[str, str],
) -> str:
    """Submit a claim and return its identifier."""
    response = await client.post(
        "/api/v1/employer-claims",
        json=_claim_payload(company_id),
        headers=headers,
    )
    assert response.status_code == 201
    return str(response.json()["id"])


@pytest.mark.asyncio
async def test_submit_claim_requires_auth(client: AsyncClient, sample_company: Company) -> None:
    """Claim submission should require authentication."""
    response = await client.post(
        "/api/v1/employer-claims",
        json=_claim_payload(str(sample_company.id)),
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_submit_claim_success(
    client: AsyncClient,
    sample_company: Company,
    auth_headers: dict[str, str],
    db_session: AsyncSession,
) -> None:
    """Authenticated users should be able to submit employer claims."""
    response = await client.post(
        "/api/v1/employer-claims",
        json=_claim_payload(str(sample_company.id)),
        headers=auth_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["company_id"] == str(sample_company.id)
    assert body["status"] == ClaimStatus.PENDING.value
    assert body["verification_documents"] == [VERIFICATION_DOCUMENT]

    audit_count = await db_session.scalar(
        select(func.count())
        .select_from(AuditLog)
        .where(AuditLog.action == "employer_claim.created")
    )
    assert audit_count == 1


@pytest.mark.asyncio
async def test_submit_claim_unknown_company_returns_404(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Claims for missing companies should return 404."""
    response = await client.post(
        "/api/v1/employer-claims",
        json=_claim_payload(str(uuid4())),
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_submit_duplicate_pending_claim_returns_409(
    client: AsyncClient,
    sample_company: Company,
    auth_headers: dict[str, str],
) -> None:
    """Duplicate pending claims for the same company should return 409."""
    first = await client.post(
        "/api/v1/employer-claims",
        json=_claim_payload(str(sample_company.id)),
        headers=auth_headers,
    )
    assert first.status_code == 201

    duplicate = await client.post(
        "/api/v1/employer-claims",
        json=_claim_payload(str(sample_company.id)),
        headers=auth_headers,
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == "Pending claim already exists for this company"


@pytest.mark.asyncio
async def test_submit_claim_when_company_already_approved_returns_409(
    client: AsyncClient,
    sample_company: Company,
    auth_headers: dict[str, str],
    admin_auth_headers: dict[str, str],
) -> None:
    """New claims should fail when the company already has an approved employer."""
    claim_id = await _submit_claim(client, str(sample_company.id), auth_headers)
    approve = await client.post(
        f"/api/v1/employer-claims/{claim_id}/approve",
        headers=admin_auth_headers,
    )
    assert approve.status_code == 200

    suffix = uuid4().hex[:8]
    second_user = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"claimant2-{suffix}@example.com",
            "username": f"claimant2_{suffix}",
            "password": "StrongPass123!",
        },
    )
    assert second_user.status_code == 200
    second_headers = {"Authorization": f"Bearer {second_user.json()['access_token']}"}

    response = await client.post(
        "/api/v1/employer-claims",
        json=_claim_payload(str(sample_company.id)),
        headers=second_headers,
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "Company already has an approved employer claim"


@pytest.mark.asyncio
async def test_submit_claim_when_user_already_linked_returns_409(
    client: AsyncClient,
    db_session: AsyncSession,
    auth_headers: dict[str, str],
    admin_auth_headers: dict[str, str],
    sample_company: Company,
) -> None:
    """Users already linked to a company cannot submit claims for another company."""
    claim_id = await _submit_claim(client, str(sample_company.id), auth_headers)
    approve = await client.post(
        f"/api/v1/employer-claims/{claim_id}/approve",
        headers=admin_auth_headers,
    )
    assert approve.status_code == 200

    other_company = Company(name=f"Other Corp {uuid4().hex[:8]}", locations=["Remote"])
    db_session.add(other_company)
    await db_session.flush()

    response = await client.post(
        "/api/v1/employer-claims",
        json=_claim_payload(str(other_company.id)),
        headers=auth_headers,
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "User is already linked to another company"


@pytest.mark.asyncio
async def test_list_my_claims_returns_submitted_claims(
    client: AsyncClient,
    sample_company: Company,
    auth_headers: dict[str, str],
) -> None:
    """Users should see their own submitted claims."""
    await _submit_claim(client, str(sample_company.id), auth_headers)

    response = await client.get("/api/v1/employer-claims/me", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["company_id"] == str(sample_company.id)


@pytest.mark.asyncio
async def test_get_claim_returns_own_claim(
    client: AsyncClient,
    sample_company: Company,
    auth_headers: dict[str, str],
) -> None:
    """Claim owners should be able to fetch their claim by id."""
    claim_id = await _submit_claim(client, str(sample_company.id), auth_headers)
    response = await client.get(f"/api/v1/employer-claims/{claim_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == claim_id


@pytest.mark.asyncio
async def test_get_claim_forbidden_for_other_user(
    client: AsyncClient,
    sample_company: Company,
    auth_headers: dict[str, str],
) -> None:
    """Non-admin users should not read another user's claim."""
    claim_id = await _submit_claim(client, str(sample_company.id), auth_headers)

    suffix = uuid4().hex[:8]
    other_user = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"other-{suffix}@example.com",
            "username": f"other_{suffix}",
            "password": "StrongPass123!",
        },
    )
    assert other_user.status_code == 200
    other_headers = {"Authorization": f"Bearer {other_user.json()['access_token']}"}

    response = await client.get(f"/api/v1/employer-claims/{claim_id}", headers=other_headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_admin_list_claims_returns_pending_queue(
    client: AsyncClient,
    sample_company: Company,
    auth_headers: dict[str, str],
    admin_auth_headers: dict[str, str],
) -> None:
    """Admins should list pending claims for review."""
    await _submit_claim(client, str(sample_company.id), auth_headers)

    response = await client.get("/api/v1/employer-claims", headers=admin_auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 1
    assert all(item["status"] == ClaimStatus.PENDING.value for item in body["items"])


@pytest.mark.asyncio
async def test_admin_list_claims_requires_admin(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Non-admin users should not access the admin claim queue."""
    response = await client.get("/api/v1/employer-claims", headers=auth_headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_approve_claim_links_user_to_company(
    client: AsyncClient,
    sample_company: Company,
    auth_headers: dict[str, str],
    admin_auth_headers: dict[str, str],
    db_session: AsyncSession,
) -> None:
    """Approving a claim should mark the user as employer for the company."""
    claim_id = await _submit_claim(client, str(sample_company.id), auth_headers)
    response = await client.post(
        f"/api/v1/employer-claims/{claim_id}/approve",
        headers=admin_auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == ClaimStatus.APPROVED.value
    assert body["reviewed_at"] is not None

    me_response = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert me_response.status_code == 200
    me_body = me_response.json()
    assert me_body["is_employer"] is True
    assert me_body["employer_company_id"] == str(sample_company.id)

    company = await db_session.get(Company, sample_company.id)
    assert company is not None
    assert company.verified_status == sample_company.verified_status

    audit_count = await db_session.scalar(
        select(func.count())
        .select_from(AuditLog)
        .where(AuditLog.action == "employer_claim.approved")
    )
    assert audit_count == 1


@pytest.mark.asyncio
async def test_approve_claim_requires_admin(
    client: AsyncClient,
    sample_company: Company,
    auth_headers: dict[str, str],
) -> None:
    """Only admins should approve employer claims."""
    claim_id = await _submit_claim(client, str(sample_company.id), auth_headers)
    response = await client.post(
        f"/api/v1/employer-claims/{claim_id}/approve",
        headers=auth_headers,
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_approve_non_pending_claim_returns_422(
    client: AsyncClient,
    sample_company: Company,
    auth_headers: dict[str, str],
    admin_auth_headers: dict[str, str],
) -> None:
    """Only pending claims can be approved."""
    claim_id = await _submit_claim(client, str(sample_company.id), auth_headers)
    reject = await client.post(
        f"/api/v1/employer-claims/{claim_id}/reject",
        headers=admin_auth_headers,
    )
    assert reject.status_code == 200

    response = await client.post(
        f"/api/v1/employer-claims/{claim_id}/approve",
        headers=admin_auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_reject_claim_writes_audit_metadata(
    client: AsyncClient,
    sample_company: Company,
    auth_headers: dict[str, str],
    admin_auth_headers: dict[str, str],
    db_session: AsyncSession,
) -> None:
    """Rejecting a claim should store optional reasons in audit metadata only."""
    claim_id = await _submit_claim(client, str(sample_company.id), auth_headers)
    response = await client.post(
        f"/api/v1/employer-claims/{claim_id}/reject",
        headers=admin_auth_headers,
        json={"reason": "Domain verification documents were insufficient."},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == ClaimStatus.REJECTED.value

    audit = await db_session.scalar(
        select(AuditLog).where(
            AuditLog.action == "employer_claim.rejected",
            AuditLog.entity_id == body["id"],
        )
    )
    assert audit is not None
    assert audit.metadata_json["reason"] == "Domain verification documents were insufficient."

    claim = await db_session.get(EmployerClaim, body["id"])
    assert claim is not None
    assert claim.status == ClaimStatus.REJECTED


@pytest.mark.asyncio
async def test_reject_claim_without_body_succeeds(
    client: AsyncClient,
    sample_company: Company,
    auth_headers: dict[str, str],
    admin_auth_headers: dict[str, str],
) -> None:
    """Reject should succeed without a request body."""
    claim_id = await _submit_claim(client, str(sample_company.id), auth_headers)
    response = await client.post(
        f"/api/v1/employer-claims/{claim_id}/reject",
        headers=admin_auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == ClaimStatus.REJECTED.value
