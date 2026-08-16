"""FastAPI main application entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from forgesight.config.settings import settings
from forgesight.api.routes import health, chat, incidents, inspections, agents

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Multimodal Agentic Manufacturing Intelligence Platform",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["Health"])
app.include_router(incidents.router, prefix="/incidents", tags=["Incidents"])
app.include_router(inspections.router, prefix="/inspections", tags=["Inspections"])
app.include_router(agents.router, prefix="/agents", tags=["Agents"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])


@app.get("/")
def root():
    return {
        "app": settings.app_name,
        "status": "running",
        "docs": "/docs",
    }
