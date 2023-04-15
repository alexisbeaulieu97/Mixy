import os
from pathlib import Path
from typing import Any

import pytest
from pyfakefs.fake_filesystem_unittest import FakeFilesystem  # type: ignore

from mixy.utils import (
    extract_repo_name,
    get_all_files,
    get_directory_contents,
    get_nested_values,
    get_objects_of_type,
    is_empty_directory,
    is_git_url,
    is_in_lists,
    join_local_path,
    starts_with_option,
    unique_list,
)

TEST_DIR = Path("/tmp/mixy_test")


def lists_are_equal(a: list[Any], b: list[Any]) -> bool:
    return sorted(a) == sorted(b)


@pytest.mark.parametrize(
    "url, expected",
    [
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
    ],
)
def test_extract_repo_name(url: str, expected: str) -> None:
    assert extract_repo_name(url) == expected


@pytest.mark.parametrize(
    "url, expected",
    [
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
        (
            "https://github.com/user/repo-with-a-long-string-of-dashes------------.git",
            True,
        ),
    ],
)
def test_is_git_url(url: str, expected: bool) -> None:
    assert is_git_url(url) == expected


@pytest.mark.parametrize(
    "item, options, expected", [("abc", ["a"], True), ("abc", ["b"], False)]
)
def test_starts_with_option(item: str, options: list[str], expected: bool):
    assert starts_with_option(item, options) == expected


@pytest.mark.parametrize(
    "l, expected",
    [
        ([1, 2, 3, 1, 2], [1, 2, 3]),
        (["a", "b", "a", "c"], ["a", "b", "c"]),
        ([1, 2, 3, 4, 5], [1, 2, 3, 4, 5]),
        ([], []),
        ([1], [1]),
        (["a", "b", "b", "c", "c"], ["a", "b", "c"]),
        (["a", "b", "c", "d", "e", "f"], ["a", "b", "c", "d", "e", "f"]),
        ([1, 1, 1, 1, 1, 1], [1]),
        (["a", "a", "a", "a", "a", "a"], ["a"]),
    ],
)
def test_unique_list(l: list[Any], expected: list[Any]):
    assert sorted(unique_list(l)) == sorted(expected)


@pytest.mark.parametrize(
    "files, expected",
    [
        (["file1.txt"], [TEST_DIR.joinpath("file1.txt")]),
        (
            ["file1.txt", "file2.txt"],
            [TEST_DIR.joinpath("file1.txt"), TEST_DIR.joinpath("file2.txt")],
        ),
        (["dir1/file1.txt"], [TEST_DIR.joinpath("dir1/file1.txt")]),
        (
            ["dir1/file1.txt", "dir1/file2.txt"],
            [TEST_DIR.joinpath("dir1/file1.txt"), TEST_DIR.joinpath("dir1/file2.txt")],
        ),
        (["dir1/dir2/file1.txt"], [TEST_DIR.joinpath("dir1/dir2/file1.txt")]),
        ([], []),
    ],
)
def test_get_all_files(fs: FakeFilesystem, files: list[Path], expected: list[Path]):
    os.makedirs(TEST_DIR)

    for f in files:
        fs.create_file(TEST_DIR.joinpath(f), create_missing_dirs=True)

    assert get_all_files(TEST_DIR) == expected


@pytest.mark.parametrize(
    "files, expected",
    [
        (["file1.txt"], False),
        (["file1.txt", "file2.txt"], False),
        (["dir1/file1.txt"], False),
        (["dir1/file1.txt", "dir1/file2.txt"], False),
        (["dir1/dir2/file1.txt"], False),
        (["dir1/dir2/"], False),
        (["file1.txt", "dir1/"], False),
        ([], True),
    ],
)
def test_is_empty_directory(fs: FakeFilesystem, files: list[Path], expected: bool):
    os.makedirs(TEST_DIR)

    for f in files:
        fs.create_file(TEST_DIR.joinpath(f), create_missing_dirs=True)

    assert is_empty_directory(TEST_DIR) == expected


@pytest.mark.parametrize(
    "a, b, expected",
    [
        (
            Path("/home/user/dir"),
            Path("/usr/local/bin"),
            Path("/home/user/dir/usr/local/bin"),
        ),
        (Path("/"), Path("/usr/local/bin"), Path("/usr/local/bin")),
        (Path("/home/user"), Path("/"), Path("/home/user")),
        (Path("/home/user"), Path("/usr/local"), Path("/home/user/usr/local")),
    ],
)
def test_join_local_path(a: Path, b: Path, expected: Path):
    assert join_local_path(a, b) == expected


@pytest.mark.parametrize(
    "files, expected",
    [
        (["file1.txt"], [TEST_DIR.joinpath("file1.txt")]),
        (
            ["file1.txt", "file2.txt"],
            [TEST_DIR.joinpath("file1.txt"), TEST_DIR.joinpath("file2.txt")],
        ),
        (["dir1/file1.txt"], [TEST_DIR.joinpath("dir1")]),
        (["dir1/file1.txt", "dir1/file2.txt"], [TEST_DIR.joinpath("dir1")]),
        (["dir1/dir2/file1.txt"], [TEST_DIR.joinpath("dir1")]),
        ([], []),
    ],
)
def test_get_directory_contents(
    fs: FakeFilesystem, files: list[Path], expected: list[Path]
):
    os.makedirs(TEST_DIR)

    for f in files:
        fs.create_file(TEST_DIR.joinpath(f), create_missing_dirs=True)

    assert lists_are_equal(get_directory_contents(TEST_DIR), expected)


@pytest.mark.parametrize(
    "d, expected",
    [
        ({"a": 1, "b": 2}, [1, 2]),
        ({"a": {"b": 2, "c": 3}, "d": 4}, [2, 3, 4]),
        ({"a": {"b": {"c": 3, "d": 4}}, "e": 5}, [3, 4, 5]),
        ({}, []),
    ],
)
def test_get_nested_values(d, expected):
    result = list(get_nested_values(d))
    assert result == expected


@pytest.mark.parametrize(
    "o, types, ignores, expected",
    [
        ([1, 2, "foo", ["bar", 3]], (str,), (), ["foo", "bar"]),
        ({"a": 1, "b": ["c", "d"]}, (str,), (), ["c", "d"]),
        ([1, 2, "foo", ["bar", 3]], (str,), (int,), ["foo", "bar"]),
        ([1, 2, "foo", ["bar", 3]], (str,), (int, list), []),
        ({"a": 1, "b": ["c", "d"]}, (str,), (int, dict), []),
        ([], (int,), (str,), []),
        ([], (str,), (int,), []),
        ({}, (int,), (str,), []),
        ({}, (str,), (int,), []),
    ],
)
def test_get_objects_of_type(
    o: Any, types: tuple[type], ignores: tuple[type], expected: list[Any]
):
    result = get_objects_of_type(o, types, ignores)
    assert result == expected


@pytest.mark.parametrize(
    "item, lists, expected",
    [
        ("a", [["a", "b", "c"]], True),
        ("a", [["a", "b"], ["c"]], True),
        ("c", [["a", "b"], ["c"]], True),
        ("c", [[], ["c"]], True),
        ("x", [["a", "b"], ["c"]], False),
        ([1, 2], [[[1, 2], [3, 4]], [[5, 6], [7, 8]]], True),
        ([5, 6], [[[1, 2], [3, 4]], [[5, 6], [7, 8]]], True),
        ([9, 10], [[[1, 2], [3, 4]], [[5, 6], [7, 8]]], False),
        ([1, 3], [[[1, 2], [3, 4]], [[5, 6], [7, 8]]], False),
    ],
)
def test_is_in_list(item: Any, lists: list[list[Any]], expected: bool):
    assert is_in_lists(item, *lists) == expected
