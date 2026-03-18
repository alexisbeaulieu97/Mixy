"""CLI-oriented loguru configuration."""

from __future__ import annotations

import sys
from typing import Any, cast

from loguru import logger

USER_LOG_FORMAT = "<level>{level.icon}</level> <level>{message}</level>"
DEBUG_LOG_FORMAT = (
    "<dim>{time:YYYY-MM-DD HH:mm:ss}</dim> "
    "<level>{level: <8}</level> "
    "<cyan>{name}</cyan>:<cyan>{line}</cyan> "
    "{message}"
)


def configure_logging(level: str) -> None:
    """Reset stderr logging to the requested severity and format."""
    normalized_level = level.upper()
    logger.remove()
    logger.configure(patcher=cast(Any, _noop_patcher))
    logger.add(
        sys.stderr,
        colorize=True,
        format=DEBUG_LOG_FORMAT if normalized_level == "DEBUG" else USER_LOG_FORMAT,
        level=normalized_level,
    )


def _noop_patcher(record: dict[str, Any]) -> None:
    """Reset any previously configured patcher state."""
