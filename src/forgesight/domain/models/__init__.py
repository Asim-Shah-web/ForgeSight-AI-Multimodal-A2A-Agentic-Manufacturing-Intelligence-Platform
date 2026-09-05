"""Exports all SQLModel table models so that:
1. `SQLModel.metadata` knows about every table when create_all()/Alembic run.
2. Application code can `from forgesight.domain.models import User, Incident, ...`
"""

from forgesight.domain.models.audit import AuditEvent, AuditEventType
from forgesight.domain.models.inspection import CvFinding, InspectionImage
from forgesight.domain.models.investigation import (
    CorrectiveAction,
    Incident,
    IncidentStatus,
    Report,
    RootCauseHypothesis,
)
from forgesight.domain.models.knowledge import (
    DocumentChunk,
    IncidentEmbedding,
    TechnicalDocument,
)
from forgesight.domain.models.maintenance import (
    MaintenanceRecord,
    WorkOrder,
    WorkOrderStatus,
)
from forgesight.domain.models.manufacturing import (
    Batch,
    Board,
    Feeder,
    Line,
    Machine,
    Nozzle,
    Product,
)
from forgesight.domain.models.supply_chain import Component, ComponentLot, Supplier
from forgesight.domain.models.telemetry import ProductionTelemetry, ReflowProfile
from forgesight.domain.models.users import User, UserRole

__all__ = [
    "AuditEvent",
    "AuditEventType",
    "CvFinding",
    "InspectionImage",
    "CorrectiveAction",
    "Incident",
    "IncidentStatus",
    "Report",
    "RootCauseHypothesis",
    "DocumentChunk",
    "IncidentEmbedding",
    "TechnicalDocument",
    "MaintenanceRecord",
    "WorkOrder",
    "WorkOrderStatus",
    "Batch",
    "Board",
    "Feeder",
    "Line",
    "Machine",
    "Nozzle",
    "Product",
    "Component",
    "ComponentLot",
    "Supplier",
    "ProductionTelemetry",
    "ReflowProfile",
    "User",
    "UserRole",
]