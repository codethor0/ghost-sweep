"""Job posting and risk score schemas."""

from datetime import datetime

from pydantic import BaseModel, HttpUrl

from app.services.scoring import ScoreComponent


class ScoreComponentResponse(BaseModel):
    """Weighted score component exposed to clients."""

    name: str
    raw_value: float
    weight: float
    weighted_value: float

    @classmethod
    def from_component(cls, component: ScoreComponent) -> "ScoreComponentResponse":
        """Build a response model from a score component.

        Args:
            component: Internal score component.

        Returns:
            ScoreComponentResponse: API response model.
        """
        return cls(
            name=component.name,
            raw_value=component.raw_value,
            weight=component.weight,
            weighted_value=component.weighted_value,
        )


class GhostRiskScoreResponse(BaseModel):
    """Transparent ghost job risk signal for a posting."""

    job_posting_id: int
    score: float
    confidence: float
    explanation: str
    components: list[ScoreComponentResponse]
    calculated_at: datetime


class JobPostingResponse(BaseModel):
    """Public job posting details."""

    id: int
    company_id: int
    title: str
    posting_url: HttpUrl
    status: str
    first_seen_at: datetime
    last_seen_at: datetime

    model_config = {"from_attributes": True}
