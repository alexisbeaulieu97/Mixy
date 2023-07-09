import re
import subprocess
from datetime import datetime, timezone, tzinfo
from typing import Any, Iterable, Iterator, Mapping, Optional

from mixy.constants import GIT_PROTOCOLS_PREFIXES


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


def starts_with_option(s: str, options: Iterable[str]) -> bool:
    """
    Given a string `s` and a list of strings `options`, returns a boolean
    indicating whether any of the strings in `options` starts with `s`.

    Args:
        s (str): A string to check.
        options (Iterable[str]): A list of strings to check for the presence of `s` at the start of any of the strings in the list.

    Returns:
        bool: True if any of the strings in `options` starts with `s`, False otherwise.
    """
    return any(s.startswith(option) for option in options)


def unique_list(li: list[Any]) -> list[Any]:
    """
    This function takes a list of elements `l` and returns a new list containing
    only the unique elements from `l`.

    Args:
        li (list[Any]): A list of elements.

    Returns:
        list[Any]: A list of unique elements from `li`.

    Examples:
        >>> unique_list([1, 2, 3, 1, 2])
        [1, 2, 3]
        >>> unique_list(['a', 'b', 'a', 'c'])
        ['a', 'b', 'c']
    """
    return list(set(li))


def get_nested_values(d: Mapping[Any, Any]) -> Iterator[Any]:
    """
    This function recursively traverses a nested dictionary and
    returns a generator that yields all values in the dictionary.

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
    """Returns a list of objects of the given types within a nested structure.

    Args:
        o (Any): The object to search for objects of the given type.
        t (type): The type to search for.
        ignores (tuple[type]): The types to ignore.

    Returns:
        list[Any]: A list of objects of the given type within the input object.

    Examples:
        >>> get_objects_of_type([1, 2, 'foo', ['bar', 3]], str)
        ['foo', 'bar']
        >>> get_objects_of_type({'a': 1, 'b': ['c', 'd']}, str)
        ['c', 'd']
    """
    objects: list[Any] = []
    if isinstance(o, ignores):
        return objects
    elif isinstance(o, types):
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


def get_current_time(tz: Optional[tzinfo] = None) -> datetime:
    """
    Get the current datetime in the specified timezone or the local timezone by default.

    Args:
        tz (ZoneInfo, optional): The timezone to convert the current time to.
            Defaults to the local timezone.

    Returns:
        datetime: The current datetime in the specified timezone.
    """
    if tz is None:
        return datetime.now(timezone.utc).astimezone()
    return datetime.now(tz)


def is_format(data: str, formats: Iterable[str]) -> bool:
    for f in formats:
        m = re.match(f, data)
        if m is not None:
            return True
    return False


def run_github_command(*opts: str) -> subprocess.CompletedProcess:
    for o in opts:
        if not isinstance(o, str):
            raise TypeError("Command options must be of type 'str'")

    return subprocess.run(
        ["gh", *opts],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="UTF-8",
    )
