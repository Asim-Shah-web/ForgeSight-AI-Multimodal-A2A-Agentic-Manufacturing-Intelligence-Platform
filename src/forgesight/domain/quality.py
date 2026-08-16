"""Quality metric domain model."""

from pydantic import BaseModel


class QualityMetric(BaseModel):
    defect_code: str
    description: str
    tolerance_threshold: float
