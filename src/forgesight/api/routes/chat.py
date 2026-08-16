"""Chat router."""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


@router.post("")
def chat(request: ChatRequest):
    return {
        "reply": f"ForgeSight Copilot received: {request.message}",
        "agent": "supervisor",
    }
