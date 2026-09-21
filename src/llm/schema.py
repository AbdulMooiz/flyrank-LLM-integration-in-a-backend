from enum import Enum

from pydantic import BaseModel, Field


class Category(str, Enum):
    billing = "billing"
    bug = "bug"
    feature = "feature"
    other = "other"


class Urgency(str, Enum):
    low = "low"
    normal = "normal"
    high = "high"


class TriageInput(BaseModel):
    """Stage 1: rejected before any model call if this fails to validate."""

    text: str = Field(..., min_length=1, max_length=2000)


class TriageOutput(BaseModel):
    """Stage 1 and Stage 3: what the model's answer must match, or it is repaired
    once and then quarantined. This is also the only shape the endpoint is ever
    allowed to return."""

    category: Category
    urgency: Urgency
    confidence: float = Field(..., ge=0.0, le=1.0)
    reason: str = Field(..., max_length=300)
