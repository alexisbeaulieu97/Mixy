"""Loader for Mixy variable files."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from mixy.domain.exceptions import ConfigValidationError


def load_vars_file(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    if not isinstance(data, dict):
        raise ConfigValidationError(
            "Vars file must contain a YAML mapping at the top level.",
            field_path="<root>",
            suggestion=(
                "Replace the top-level YAML value with a mapping of variable names to values."
            ),
        )

    return dict(data)
