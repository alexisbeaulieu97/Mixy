from pathlib import Path
from typing import Any, Iterator, List, Mapping, Optional

from supertemplater.constants import GIT_PROTOCOLS_PREFIXES


def extract_repo_name(url: str) -> str:
    """
    Extracts the repository name from a given URL.

    Args:
    url (str): The URL of the repository.

    Returns:
    str: The name of the repository.
    """
    return url.split("/")[-1].replace(".git", "")


def is_git_url(url: str) -> bool:
    """
    Check if a URL is a Git URL.

    This function checks if a given URL starts with one of the prefixes for
    Git protocols (e.g. "git@", "http://", "https://").

    Args:
        url (str): The URL to check.

    Returns:
        bool: True if the URL is a Git URL, False otherwise.
    """
    return starts_with_option(url, GIT_PROTOCOLS_PREFIXES)


def starts_with_option(s: str, options: List[str]) -> bool:
    """
    Given a string `s` and a list of strings `options`, returns a boolean indicating whether any of the strings in `options`
    starts with `s`.

    Args:
        s (str): A string to check.
        options (List[str]): A list of strings to check for the presence of `s` at the start of any of the strings in the list.

    Returns:
        bool: True if any of the strings in `options` starts with `s`, False otherwise.
    """
    return any(s.startswith(option) for option in options)


def unique_list(l: list[Any]) -> list[Any]:
    """
    This function takes a list of elements `l` and returns a new list containing
    only the unique elements from `l`.

    Args:
        l (List[Any]): A list of elements.

    Returns:
        List[Any]: A list of unique elements from `l`.

    Examples:
        >>> unique_list([1, 2, 3, 1, 2])
        [1, 2, 3]
        >>> unique_list(['a', 'b', 'a', 'c'])
        ['a', 'b', 'c']
    """
    return list(set(l))


def get_all_files(
    base_dir: Path, dir_ignores: Optional[list[str]] = None
) -> List[Path]:
    """
    This function recursively traverses the directory tree rooted at `base_dir` and returns a list of all files in the tree.
    It ignores any subdirectories whose names appear in the `dir_ignores` list.

    Args:
        base_dir (Path): The root directory of the directory tree to traverse.
        dir_ignores (Optional[List[str]]): A list of directory names to ignore.

    Returns:
        List[Path]: A list of all files in the directory tree rooted at `base_dir`, ignoring any subdirectories whose names appear in `dir_ignores`.
    """
    if dir_ignores is None:
        dir_ignores = []
    files: list[Path] = []
    for item in base_dir.iterdir():
        if item.is_dir() and item.name not in dir_ignores:
            files.extend(get_all_files(item, dir_ignores))
        elif item.is_file():
            files.append(item)

    return files


def is_empty_directory(path: Path) -> bool:
    """Determines if a directory is empty.

    Args:
        path (Path): The path of the directory to check.

    Returns:
        bool: True if the directory is empty, False otherwise.
    """
    return path.is_dir() and not list(path.glob("*"))


def join_local_path(a: Path, b: Path) -> Path:
    """
    This function combines two local file paths, `a` and `b`, and returns a new `Path` object that is the result of appending `b` to `a` after making `b` relative to the root path `/`.

    Args:
        a (Path): The first path to join.
        b (Path): The second path to join.

    Example:
        >>> join_local_path(Path("/home/user/dir"), Path("/usr/local/bin"))
        Path("/home/user/dir/usr/local/bin")
    """
    return a.joinpath(b.relative_to("/"))


def get_directory_contents(
    d: Path, ignores: Optional[list[str]] = None, recurse: bool = False
) -> List[Path]:
    """
    Retrieve a list of all files and directories contained within the given directory.

    Args:
        d (Path): The directory to retrieve the contents of.

    Returns:
        A list of `Path` objects, each representing a file or directory contained within `d`.

    Raises:
        ValueError: If the given `Path` object does not represent a valid directory.
    """
    if ignores is None:
        ignores = []
    if not d.is_dir():
        raise ValueError(f"{d} is not a valid directory")
    files_and_dirs = d.rglob("*") if recurse else d.glob("*")
    ignored: list[Path] = []
    for ignore in ignores:
        ignored.extend(d.glob(ignore))
    return list(set(files_and_dirs) - set(ignored))


def get_nested_values(d: Mapping[Any, Any]) -> Iterator[Any]:
    """
    This function recursively traverses a nested dictionary and returns a generator that yields all values in the dictionary.

    Args:
        d (Mapping): The dictionary to traverse.

    Returns:
        Iterator[Any]: A generator that yields all values in the dictionary.
    """
    for v in d.values():
        if isinstance(v, Mapping):
            yield from get_nested_values(v)  # type: ignore
        else:
            yield v


def get_objects_of_type(
    o: Any, types: tuple[type], ignores: tuple[type] = tuple()
) -> list[Any]:
    """Returns a list of objects of the given type within a nested structure.

    Args:
        o (Any): The object to search for objects of the given type.
        t (type): The type to search for.
        ignores (tuple[type]): The type to ignore.

    Returns:
        List[Any]: A list of objects of the given type within the input object.

    Examples:
        >>> get_objects_of_type([1, 2, 'foo', ['bar', 3]], str)
        ['foo', 'bar']
        >>> get_objects_of_type({'a': 1, 'b': ['c', 'd']}, str)
        ['c', 'd']
    """
    objects: list[Any] = []
    if isinstance(o, types) and not isinstance(o, ignores):
        objects.append(o)
    elif isinstance(o, (list, tuple, set)):
        item: Any
        for item in o:
            objects.extend(get_objects_of_type(item, types, ignores))
    elif isinstance(o, Mapping):
        item: Any
        for item in o.values():
            objects.extend(get_objects_of_type(item, types, ignores))
    return objects


def is_in_lists(item: Any, *lists: list[Any]) -> bool:
    """
    Check if an item is in any of the given lists.

    Args:
      item (Any): The item to search for.
      *lists (list[Any]): The lists to search in.

    Returns:
      bool: True if the item is in any of the lists, False otherwise.
    """
    for lst in lists:
        if item in lst:
            return True
    return False
