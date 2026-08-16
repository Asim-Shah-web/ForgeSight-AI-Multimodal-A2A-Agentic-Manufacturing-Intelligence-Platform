"""Quality Incident domain model."""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional


class QualityIncident(BaseModel):
    id: str
    title: str
    description: str
    severity: str = "medium"
    status: str = "open"
    batch_id: Optional[str] = None
    machine_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
