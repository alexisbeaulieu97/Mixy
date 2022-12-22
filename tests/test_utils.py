from typing import Any

import pytest
from pyfakefs.fake_filesystem_unittest import FakeFilesystem  # type: ignore

from supertemplater.utils import extract_repo_name, is_git_url, unique_list

extract_repo_name_cases = [
    ("https://github.com/user/repo.git", "repo"),
    ("https://github.com/user/repo-with-dashes.git", "repo-with-dashes"),
    ("https://github.com/user/repo_with_underscores.git", "repo_with_underscores"),
    ("https://github.com/user/repo.with.periods.git", "repo.with.periods"),
    (
        "https://github.com/user/repo-with_periods.and-dashes.git",
        "repo-with_periods.and-dashes",
    ),
    (
        "https://github.com/user/repo-with-a-long-string-of-dashes------------.git",
        "repo-with-a-long-string-of-dashes------------",
    ),
    ("https://github.com/user/repoWithMixedCase.git", "repoWithMixedCase"),
    (
        "https://github.com/user/repo-with-1-2-3-and_special-characters.git",
        "repo-with-1-2-3-and_special-characters",
    ),
    (
        "https://github.com/user/repo.with.multiple.periods.git",
        "repo.with.multiple.periods",
    ),
]

is_git_url_cases = [
    ("git@github.com:user/repo.git", True),
    ("ssh://user@server/project.git", True),
    ("ssh://server/project.git", True),
    ("http://github.com/user/repo.git", True),
    ("https://github.com/user/repo.git", True),
    ("ftp://github.com/user/repo.git", False),
    ("", False),
    ("   ", False),
    ("!@#$%^&*()", False),
    ("http://github.com/user/repo-1-2-3-with_special-characters.git", True),
    ("https://github.com/user/organization/repo.git", True),
    ("https://github.com/user/repo-with-a-long-string-of-dashes------------.git", True),
]

test_unique_list_cases: list[Any] = [
    ([1, 2, 3, 1, 2], [1, 2, 3]),
    (["a", "b", "a", "c"], ["a", "b", "c"]),
    ([1, 2, 3, 4, 5], [1, 2, 3, 4, 5]),
    ([], []),
    ([1], [1]),
    (["a", "b", "b", "c", "c"], ["a", "b", "c"]),
    (["a", "b", "c", "d", "e", "f"], ["a", "b", "c", "d", "e", "f"]),
    ([1, 1, 1, 1, 1, 1], [1]),
    (["a", "a", "a", "a", "a", "a"], ["a"]),
]


@pytest.mark.parametrize("url, expected", extract_repo_name_cases)
def test_extract_repo_name(url: str, expected: str) -> None:
    assert extract_repo_name(url) == expected


@pytest.mark.parametrize("url, expected", is_git_url_cases)
def test_is_git_url(url: str, expected: bool) -> None:
    assert is_git_url(url) == expected


@pytest.mark.parametrize("l, expected", test_unique_list_cases)
def test_unique_list(fs: FakeFilesystem, l: list[Any], expected: list[Any]):
    assert sorted(unique_list(l)) == sorted(expected)
