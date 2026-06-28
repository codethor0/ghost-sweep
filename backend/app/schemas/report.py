"""Report schemas."""

from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class ReportEvidenceInput(BaseModel):
    """Evidence item submitted with a report."""

    evidence_type: str = Field(min_length=3, max_length=64)
    source_url: HttpUrl | None = None
    description: str = Field(min_length=10, max_length=5000)


class ReportCreateRequest(BaseModel):
    """Payload for submitting an integrity report."""

    company_name: str = Field(min_length=2, max_length=255)
    job_title: str = Field(min_length=2, max_length=255)
    posting_url: HttpUrl
    category: str = Field(min_length=3, max_length=64)
    timeline_description: str = Field(min_length=20, max_length=5000)
    evidence: list[ReportEvidenceInput] = Field(min_length=1)


class ReportEvidenceResponse(BaseModel):
    """Stored evidence item."""

    id: int
    evidence_type: str
    source_url: str | None
    description: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ReportResponse(BaseModel):
    """Submitted report details."""

    id: int
    job_posting_id: int
    category: str
    timeline_description: str
    status: str
    created_at: datetime
    evidence_items: list[ReportEvidenceResponse]

    model_config = {"from_attributes": True}
