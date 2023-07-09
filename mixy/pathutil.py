import shutil
from pathlib import Path

from mixy.plugins.plugin_manager import plugin_master


def is_empty_directory(path: Path) -> bool:
    """
    Determines if a directory is empty.

    Args:
        path (Path): The path of the directory to check.

    Returns:
        bool: True if the directory is empty, False otherwise.
    """
    return path.is_dir() and not list(path.glob("*"))


def join_relative_to_root(a: Path, b: Path) -> Path:
    """
    This function combines two local file paths, `a` and `b`,
    and returns a new `Path` object that is the result of appending `b` to `a`
    after making `b` relative to the root path `/`.

    Args:
        a (Path): The first path to join.
        b (Path): The second path to join.

    Example:
        >>> join_local_path(Path("/home/user/dir"), Path("/usr/local/bin"))
        Path("/home/user/dir/usr/local/bin")
    """
    if b.is_absolute():
        b = Path(*b.parts[1:])
    return a / b


def get_directory_contents(
    d: Path,
    ignores: list[str] | None = None,
    recurse: bool = False,
) -> list[Path]:
    """
    Retrieve a list of all files and directories contained within the given directory.

    Args:
        d (Path): The directory to retrieve the contents of.

    Returns:
        A list of `Path` objects, each representing
        a file or directory contained within `d`.

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


def get_all_files_in_directory(
    base_dir: Path,
    dir_ignores: list[str] | None = None,
) -> list[Path]:
    """
    This function recursively traverses the directory tree rooted
    at `base_dir` and returns a list of all files in the tree.
    It ignores any subdirectories whose names appear in the `dir_ignores` list.

    Args:
        base_dir (Path): The root directory of the directory tree to traverse.
        dir_ignores (Optional[list[str]]): A list of directory names to ignore.

    Returns:
        list[Path]: A list of all files in the directory tree rooted at `base_dir`,
        ignoring any subdirectories whose names appear in `dir_ignores`.
    """
    if dir_ignores is None:
        dir_ignores = []
    files: list[Path] = []
    for item in base_dir.iterdir():
        if item.is_dir() and item.name not in dir_ignores:
            files.extend(get_all_files_in_directory(item, dir_ignores))
        elif item.is_file():
            files.append(item)

    return files


def clear_directory(dir_path: Path) -> None:
    """
    Resursively remove all files and directories within the given directory.

    Args:
        dir_path (Path): The path of the directory to clear.
    """
    shutil.rmtree(dir_path.absolute().as_posix())


def load_configuration_file(config_file: Path) -> dict:
    """
    Loads a configuration file and returns its contents as a dictionary.

    This function first checks whether the specified path points to a file. If the path
    is not a file, a FileNotFoundError is raised. Then, it uses the hook system provided
    by the plugin_master to load the configuration from the file. If the configuration
    file format is not supported, a ValueError is raised.

    Args:
        config_file (Path): The path to the configuration file to load.

    Returns:
        dict: The contents of the configuration file, represented as a dictionary.

    Raises:
        FileNotFoundError: If the provided path does not point to a file.
        ValueError: If the file format is unsupported.

    Note:
        The specific dictionary structure returned by this function depends on the
        structure of your configuration file and the capabilities of your plugin system.
    """
    if not config_file.is_file():
        raise FileNotFoundError(
            f"Configuration file not found: {config_file.absolute()}"
        )
    config = plugin_master.hook.load_configuration(config_file=config_file)
    if not config:
        raise ValueError(
            f"Unsupported project configuration format: {config_file.suffix}"
        )
    return config
