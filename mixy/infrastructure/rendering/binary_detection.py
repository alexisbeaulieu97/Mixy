"""Binary-file detection helpers."""

from __future__ import annotations

from pathlib import Path

BINARY_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".woff",
    ".woff2",
    ".ttf",
    ".zip",
    ".gz",
    ".tar",
    ".exe",
    ".dll",
    ".so",
    ".dylib",
}
HEADER_SCAN_BYTES = 8192


def is_binary(path: Path) -> bool:
    """Return True when the file should be treated as binary.

    This is a best-effort classifier for template rendering, not a MIME detector.
    """
    if path.suffix.lower() in BINARY_EXTENSIONS:
        return True

    with path.open("rb") as handle:
        chunk = handle.read(HEADER_SCAN_BYTES)

    return b"\x00" in chunk
