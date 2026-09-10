from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class InspectionType(str, Enum):
    MOVE_IN = "move-in"
    MOVE_OUT = "move-out"


class EvidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INCONCLUSIVE = "inconclusive"


class ConditionStatus(str, Enum):
    NEW = "new"
    PRE_EXISTING = "pre-existing"
    UNCHANGED = "unchanged"
    MISSING = "missing"
    IMPROVED = "improved"
    UNCERTAIN = "uncertain"


class Observation(BaseModel):
    inspection_id: str
    image_id: str
    label: str
    description: str
    condition: str = "not specified"
    confidence: float = Field(ge=0, le=1)
    region: dict[str, int] | None = None
    source: str = "cv"
    created_at: str = Field(default_factory=now_iso)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChangeFinding(BaseModel):
    object_label: str
    status: ConditionStatus
    confidence: float = Field(ge=0, le=1)
    explanation: str
    move_in_image: str | None = None
    move_out_image: str | None = None
    region: dict[str, int] | None = None
    evidence_ids: list[str] = Field(default_factory=list)
    review_required: bool = False


class Inspection(BaseModel):
    id: str
    room_name: str
    inspection_type: InspectionType
    captured_at: str = Field(default_factory=now_iso)
    notes: str = ""
    media_paths: list[str] = Field(default_factory=list)


class ClaimAnalysis(BaseModel):
    claim: str
    outcome: str
    confidence: EvidenceLevel
    rationale: str
    evidence: list[str] = Field(default_factory=list)
    caveat: str = "This is evidence organization, not a legal determination."
