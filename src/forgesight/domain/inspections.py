"""Inspection domain model."""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional


class Inspection(BaseModel):
    id: str
    component_id: str
    image_url: Optional[str] = None
    defect_detected: bool = False
    defect_type: Optional[str] = None
    confidence: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)
