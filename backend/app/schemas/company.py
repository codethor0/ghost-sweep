"""Company schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class CompanyResponse(BaseModel):
    """Public company profile."""

    id: int
    name: str
    website: str | None
    profile_status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CompanyListResponse(BaseModel):
    """Paginated company list."""

    items: list[CompanyResponse]
    total: int
    page: int
    page_size: int


class CompanyCreateRequest(BaseModel):
    """Payload for creating a company record."""

    name: str = Field(min_length=2, max_length=255)
    website: str | None = Field(default=None, max_length=512)
