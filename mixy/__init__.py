"""Mixy package metadata."""

from importlib import metadata

__all__ = ["__version__", "get_version"]

__version__ = "0.1.0"


def get_version() -> str:
    """Return the installed package version, falling back to local metadata."""
    try:
        return metadata.version("mixy")
    except metadata.PackageNotFoundError:
        return __version__
