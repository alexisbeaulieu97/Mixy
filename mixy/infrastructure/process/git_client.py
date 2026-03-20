"""Git operations wrapper using the git CLI."""

from __future__ import annotations

import io
import shutil
import subprocess
import tarfile
from pathlib import Path
from typing import Union, cast

from mixy.domain.exceptions import SourceResolutionError


class GitClient:
    """Perform Git operations through the git executable on PATH."""

    def check_available(self) -> bool:
        return shutil.which("git") is not None

    def clone_bare(self, url: str, dest: Path) -> None:
        dest.parent.mkdir(parents=True, exist_ok=True)
        self._run_git(
            ["clone", "--bare", url, str(dest)],
            error_message=f"Failed to clone repository: {url}",
            suggestion="Check the URL and your network or SSH credentials.",
        )

    def fetch(self, repo_path: Path) -> None:
        self._run_git(
            [
                "-C",
                str(repo_path),
                "fetch",
                "--prune",
                "--force",
                "origin",
                "+refs/heads/*:refs/heads/*",
                "+refs/tags/*:refs/tags/*",
            ],
            error_message=f"Failed to fetch repository at {repo_path}",
            suggestion="Check your network connection and credentials.",
        )

    def rev_parse(self, repo_path: Path, ref: str) -> str:
        result = self._run_git(
            ["-C", str(repo_path), "rev-parse", "--verify", f"{ref}^{{commit}}"],
            error_message=f"Failed to resolve ref '{ref}' in {repo_path}",
            suggestion=f"Verify that ref '{ref}' exists in the repository.",
        )
        return cast(str, result.stdout).strip()

    def extract(self, repo_path: Path, sha: str, dest: Path) -> None:
        try:
            result = self._run_git(
                ["-C", str(repo_path), "archive", "--format=tar", sha],
                text=False,
                error_message=f"Failed to read commit {sha} from {repo_path}",
                suggestion="Verify that the commit exists and is reachable from the repository.",
            )
            archive = cast(bytes, result.stdout) if result.stdout is not None else b""
            self._extract_archive(archive, dest)
        except (OSError, tarfile.TarError) as error:
            raise SourceResolutionError(
                f"Failed to extract commit {sha} from {repo_path}: {error}",
                suggestion="Verify the repository contents and try again.",
                system_error=True,
            ) from error

    def _run_git(
        self,
        args: list[str],
        *,
        text: bool = True,
        error_message: str,
        suggestion: str,
    ) -> subprocess.CompletedProcess[Union[str, bytes]]:
        if not self.check_available():
            raise SourceResolutionError(
                "Git CLI is not available on PATH.",
                suggestion="Install git and make sure it is available on PATH.",
                system_error=True,
            )

        try:
            return subprocess.run(
                ["git", *args],
                check=True,
                capture_output=True,
                text=text,
            )
        except FileNotFoundError as error:
            raise SourceResolutionError(
                "Git CLI is not available on PATH.",
                suggestion="Install git and make sure it is available on PATH.",
                system_error=True,
            ) from error
        except subprocess.CalledProcessError as error:
            stderr = _decode_output(error.stderr)
            if stderr:
                error_message = f"{error_message}: {stderr}"
            raise SourceResolutionError(
                error_message,
                suggestion=suggestion,
                system_error=True,
            ) from error

    def _extract_archive(self, archive: bytes, dest: Path) -> None:
        if dest.exists():
            shutil.rmtree(dest)
        dest.mkdir(parents=True, exist_ok=True)

        with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as tar:
            for member in tar.getmembers():
                target = dest / member.name
                if not _is_within_directory(dest, target):
                    raise SourceResolutionError(
                        f"Archive entry escapes extraction root: {member.name}",
                        suggestion="Verify the repository contents.",
                        system_error=True,
                    )

                if member.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue

                if member.isfile():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    source = tar.extractfile(member)
                    if source is None:
                        continue
                    with source, target.open("wb") as sink:
                        shutil.copyfileobj(source, sink)
                    continue

                raise SourceResolutionError(
                    f"Unsupported archive entry type for {member.name}.",
                    suggestion="Use a repository without symlinks or special files.",
                    system_error=True,
                )


def _decode_output(output: object) -> str:
    if output is None:
        return ""
    if isinstance(output, bytes):
        return output.decode("utf-8", errors="replace").strip()
    return str(output).strip()


def _is_within_directory(directory: Path, target: Path) -> bool:
    directory_root = directory.resolve()
    target_path = target.resolve()
    try:
        target_path.relative_to(directory_root)
    except ValueError:
        return False
    return True
