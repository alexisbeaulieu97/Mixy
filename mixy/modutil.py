import importlib
import pkgutil
from types import ModuleType
from typing import Any, Type


def get_objects_from_module(module: ModuleType, object_type: Type[Any]) -> list[Any]:
    """
    Returns a list of objects of the specified type that are present
    in the given module.

    Args:
        module (ModuleType): The module to search for objects.
        object_type (Type[Any]): The type of objects to search for.

    Returns:
        list[Any]: A list of objects of the specified type that are present
        in the module.
    """
    objects = []
    for name in dir(module):
        obj = getattr(module, name)
        if isinstance(obj, object_type):
            objects.append(obj)
    return objects


def get_attr_from_module(module: ModuleType, attr_name: str) -> Any | None:
    """
    Returns the value of the specified attribute in the given module,
    or None if the attribute does not exist.

    Args:
        module (ModuleType): The module to search for the attribute.
        attr_name (str): The name of the attribute to search for.

    Returns:
        Any | None: The value of the specified attribute in the module,
        or None if the attribute does not exist.
    """
    return getattr(module, attr_name, None)


def get_modules_in_package(package: ModuleType) -> list[ModuleType]:
    """
    Returns a list of modules in the package with the given name.

    Args:
        package (ModuleType): The package to search for modules.

    Returns:
        list[ModuleType]: A list of modules in the package.
    """
    modules = []
    for _, modname, _ in pkgutil.iter_modules(package.__path__):
        module = importlib.import_module(f"{package.__name__}.{modname}")
        modules.append(module)
    return modules
