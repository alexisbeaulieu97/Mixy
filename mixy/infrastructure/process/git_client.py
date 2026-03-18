"""Git CLI wrapper used by Mixy's Git source provider."""

from __future__ import annotations

import shutil
import subprocess
import tarfile
from collections.abc import Sequence
from io import BytesIO
from pathlib import Path
from typing import Protocol, cast

from mixy.domain.exceptions import MixyError


class RunCommand(Protocol):
    def __call__(
        self,
        args: Sequence[str],
        *,
        capture_output: bool = False,
    ) -> subprocess.CompletedProcess[str] | subprocess.CompletedProcess[bytes]: ...


class GitClient:
    """Run Git commands with consistent error handling."""

    def __init__(
        self,
        runner: RunCommand | None = None,
    ) -> None:
        self._runner = runner or _run_command

    def check_available(self) -> bool:
        try:
            self._runner(["git", "--version"])
        except MixyError:
            return False
        return True

    def clone_bare(self, url: str, dest: Path) -> None:
        self._runner(["git", "clone", "--bare", url, str(dest)])

    def fetch(self, repo_path: Path) -> None:
        self._runner(["git", f"--git-dir={repo_path}", "fetch", "--all", "--tags", "--prune"])

    def rev_parse(self, repo_path: Path, ref: str) -> str:
        result = cast(
            subprocess.CompletedProcess[bytes],
            self._runner(
                ["git", f"--git-dir={repo_path}", "rev-parse", ref],
                capture_output=True,
            ),
        )
        return result.stdout.decode().strip()

    def extract(self, repo_path: Path, sha: str, dest: Path) -> None:
        if dest.exists():
            shutil.rmtree(dest)
        dest.mkdir(parents=True, exist_ok=True)

        result = cast(
            subprocess.CompletedProcess[bytes],
            self._runner(
                ["git", f"--git-dir={repo_path}", "archive", sha],
                capture_output=True,
            ),
        )

        with tarfile.open(fileobj=BytesIO(result.stdout), mode="r|*") as archive:
            archive.extractall(dest, filter="data")


def _run_command(
    args: Sequence[str],
    *,
    capture_output: bool = False,
) -> subprocess.CompletedProcess[str] | subprocess.CompletedProcess[bytes]:
    try:
        return subprocess.run(
            list(args),
            check=True,
            capture_output=capture_output,
            text=not capture_output,
        )
    except subprocess.CalledProcessError as error:
        stderr = error.stderr.decode() if isinstance(error.stderr, bytes) else error.stderr
        raise MixyError(f"Git command failed: {' '.join(args)}\n{stderr or ''}".strip()) from error
