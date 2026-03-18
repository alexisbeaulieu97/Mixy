"""Mixy plugin system."""

from __future__ import annotations

import pluggy

from mixy.plugins.manager import create_manager, get_source_providers

hookimpl = pluggy.HookimplMarker("mixy")

__all__ = ["create_manager", "get_source_providers", "hookimpl"]
