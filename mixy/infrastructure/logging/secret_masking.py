"""Loguru masking helpers for resolved secret values."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, cast

from loguru import logger


def configure_secret_masking(secret_values: Iterable[str]) -> None:
    """Mask all configured secret values in future Loguru messages."""
    secrets = {secret for secret in secret_values if secret}

    def patch_log_record(record: dict[str, Any]) -> None:
        message = record["message"]
        for secret in secrets:
            message = message.replace(secret, "***")
        record["message"] = message

    logger.configure(patcher=cast(Any, patch_log_record))
