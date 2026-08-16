"""Inspections router."""

from fastapi import APIRouter
from forgesight.domain.inspections import Inspection

router = APIRouter()


@router.get("")
def list_inspections():
    return []


@router.post("")
def create_inspection(inspection: Inspection):
    return inspection
