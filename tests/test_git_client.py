import subprocess
from pathlib import Path

from mixy.domain.exceptions import MixyError
from mixy.infrastructure.process.git_client import GitClient


def test_git_client_constructs_commands() -> None:
    seen: list[list[str]] = []

    def runner(
        args: list[str],
        *,
        capture_output: bool = False,
    ) -> subprocess.CompletedProcess[str] | subprocess.CompletedProcess[bytes]:
        seen.append(args)
        if capture_output:
            return subprocess.CompletedProcess(args=args, returncode=0, stdout=b"abc123\n")
        return subprocess.CompletedProcess(args=args, returncode=0, stdout="abc123\n")

    client = GitClient(runner=runner)

    assert client.check_available() is True
    client.clone_bare("https://example.com/repo.git", Path("/tmp/repo"))
    client.fetch(Path("/tmp/repo"))
    assert client.rev_parse(Path("/tmp/repo"), "main") == "abc123"

    assert seen[0] == ["git", "--version"]
    assert seen[1][:3] == ["git", "clone", "--bare"]
    assert seen[2][-3:] == ["fetch", "--all", "--tags", "--prune"][-3:]


def test_git_client_reports_subprocess_failures() -> None:
    def runner(
        args: list[str],
        *,
        capture_output: bool = False,
    ) -> subprocess.CompletedProcess[str] | subprocess.CompletedProcess[bytes]:
        raise MixyError(f"boom: {' '.join(args)}")

    client = GitClient(runner=runner)

    assert client.check_available() is False
