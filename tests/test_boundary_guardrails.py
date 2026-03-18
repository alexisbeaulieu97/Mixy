from __future__ import annotations

import ast
from pathlib import Path


def test_repo_does_not_import_retired_boundary_paths() -> None:
    offenders: list[str] = []

    for path in _python_sources():
        if path == Path(__file__):
            continue

        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module in BANNED_IMPORTS:
                offenders.append(f"{path}: from {node.module}")
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in BANNED_IMPORTS:
                        offenders.append(f"{path}: import {alias.name}")

    assert not offenders, (
        "Retired boundary paths were reintroduced:\n" + "\n".join(sorted(offenders))
    )


def _python_sources() -> list[Path]:
    return [
        *Path("mixy").rglob("*.py"),
        *Path("tests").rglob("*.py"),
    ]


def _legacy_import_path(*segments: str) -> str:
    return ".".join(segments)


BANNED_IMPORTS = {
    _legacy_import_path("mixy", "domain", "services", "source_resolver"),
    _legacy_import_path("mixy", "domain", "services", "template_renderer"),
    _legacy_import_path("mixy", "infrastructure", "sources", "base"),
}
