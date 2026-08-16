"""Logging configuration for ForgeSight AI."""

import logging
import sys
from forgesight.config.settings import settings


def setup_logging() -> logging.Logger:
    logger = logging.getLogger("forgesight")
    logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


logger = setup_logging()
