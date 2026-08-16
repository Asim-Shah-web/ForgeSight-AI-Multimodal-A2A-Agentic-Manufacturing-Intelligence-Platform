"""FastAPI dependency injection utilities."""

from forgesight.config.settings import settings


def get_settings():
    return settings
