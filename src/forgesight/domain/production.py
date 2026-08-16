"""Production domain model."""

from pydantic import BaseModel
from typing import Optional


class ProductionBatch(BaseModel):
    batch_id: str
    line_id: str
    product_sku: str
    quantity: int
    operator_id: Optional[str] = None
