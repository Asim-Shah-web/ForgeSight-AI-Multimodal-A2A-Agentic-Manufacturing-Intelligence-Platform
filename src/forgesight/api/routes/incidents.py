"""Incidents router."""

from fastapi import APIRouter
from forgesight.domain.incidents import QualityIncident

router = APIRouter()


@router.get("")
def list_incidents():
    return []


@router.post("")
def create_incident(incident: QualityIncident):
    return incident
