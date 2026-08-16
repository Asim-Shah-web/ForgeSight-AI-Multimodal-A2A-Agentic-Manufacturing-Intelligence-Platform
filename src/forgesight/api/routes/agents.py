"""Agents management & discovery router."""

from fastapi import APIRouter

router = APIRouter()


@router.get("")
def list_agents():
    return [
        {"id": "supervisor", "name": "Supervisor Agent", "status": "active"},
        {"id": "vision", "name": "Vision Inspection Agent", "status": "active"},
        {"id": "quality", "name": "Quality Agent", "status": "active"},
        {"id": "production", "name": "Production Agent", "status": "active"},
        {"id": "maintenance", "name": "Maintenance Agent", "status": "active"},
        {"id": "root_cause", "name": "Root Cause Agent", "status": "active"},
        {"id": "supplier", "name": "Supplier Agent", "status": "active"},
        {"id": "reporting", "name": "Reporting Agent", "status": "active"},
    ]
