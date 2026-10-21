# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Any, Callable, Mapping, MutableMapping, TypeIs, TypeVar, overload

from ._constants import _PATH_SEPARATOR

from . import _coercion

T = TypeVar("T")


class _MISSING_CLS:
    """A special class used to represent missing values in the configuration."""

    def __bool__(self):
        return False


_MISSING = _MISSING_CLS()  # Singleton instance representing a missing value


def _is_missing(val: Any) -> TypeIs[_MISSING_CLS]:
    """Check if a value is the special _MISSING_CLS instance.

    :param val: The value to check.
    :return: True if the value is an instance of _MISSING_CLS, False otherwise.
    """
    return isinstance(val, _MISSING_CLS)

def _path(*args: str) -> str:
    """Construct a colon-separated key path from the given arguments.

    :param args: The individual parts of the key path.
    :return: The colon-separated key path.
    """
    return _PATH_SEPARATOR.join(args)


def _get(mapping: Mapping, key: str, default: Any = None) -> Any:
    """Retrieve a value from a nested mapping using a colon-separated key path.

    :param mapping: The mapping to retrieve the value from.
    :param key: The colon-separated key path.
    :param default: The default value to return if the key path is not found.
    :return: The retrieved value or the default value if not found.
    """
    path = key.split(":")
    current = mapping
    for part in path:
        if isinstance(current, Mapping) and part in current:
            current = current[part]
        else:
            return default
    return current


def _try_set(
    mapping: MutableMapping, key: str, value: Any, *, overwrite: bool = False
) -> bool:
    """Set a value in a nested mapping using a colon-separated key path.

    :param mapping: The mapping to set the value in.
    :param key: The colon-separated key path.
    :param value: The value to set.
    :param overwrite: Whether to overwrite the existing value if the key already exists.
    """
    path = key.split(":")
    current = mapping
    for part in path[:-1]:
        if isinstance(current, MutableMapping):
            if part in current:
                current = current[part]
            else:
                current[part] = {}
                current = current[part]
        else:
            raise TypeError(
                f"Cannot set value for key path {key} in non-mutable mapping object"
            )

    if isinstance(current, MutableMapping):
        if overwrite or path[-1] not in current:
            current[path[-1]] = value
            return True
        return False
    else:
        raise TypeError(f"Cannot set value for key path {key} in non-mutable mapping")


def _set(mapping: MutableMapping, key: str, value: Any) -> None:
    """Set a value in a nested mapping using a colon-separated key path, overwriting any existing value.

    :param mapping: The mapping to set the value in.
    :param key: The colon-separated key path.
    :param value: The value to set.
    """
    _try_set(mapping, key, value, overwrite=True)


def _traverse(
    mapping: Mapping,
    func: Callable[[Any, list[str]], bool | None],
    path: list[str] | None = None,
) -> None:
    """Traverse a nested mapping and apply a function to each key-value pair.

    The function should return False to skip traversing into a nested mapping.

    :param mapping: The mapping to traverse.
    :param func: The function to apply to each key-value pair.
    :param path: The current path in the nested mapping.
    """
    if path is None:
        path = []
    for key, value in mapping.items():
        path.append(key)
        if func(value, path) is not False and isinstance(value, Mapping):
            _traverse(value, func, path)
        path.pop()


def _traverse_leaves(
    mapping: Mapping, func: Callable[[Any, list[str]], bool | None]
) -> None:
    """Traverse a nested mapping and apply a function to each leaf key-value pair.

    :param mapping: The mapping to traverse.
    :param func: The function to apply to each leaf key-value pair.
    """

    def _leaf_func(value: Any, path: list[str]) -> None:
        if isinstance(value, Mapping) and len(value) > 0:
            return
        func(value, path)

    _traverse(mapping, _leaf_func)


def _parse_env_var_name(name: str) -> str:
    """Parse an environment variable name into a colon-separated key path.

    :param name: The environment variable name.
    :return: The colon-separated key path.
    """
    return name.replace("__", ":")


def _resolve(
    primary: Mapping,
    defaults: Mapping,
    *,
    path_transformer: Callable[[str], str] | None = None,
) -> dict:
    """Resolve a mapping by merging it with a defaults mapping.

    :param primary: The primary mapping to resolve.
    :param defaults: The defaults mapping What to merge with.
    :param path_transformer: A function to transform paths before merging. Defaults to converting environment variable names to uppercase colon-separated paths.
    :return: The resolved mapping.
    """

    if not path_transformer:
        path_transformer = lambda x: _parse_env_var_name(x).upper()

    flat = {}

    def _populate(val: Any, path: list[str]):
        path_str = path_transformer(_path(*path))
        if isinstance(val, Mapping) and len(val) == 0:
            flat[path_str] = {}
        else:
            flat[path_str] = val

    _traverse_leaves(defaults, _populate)
    _traverse_leaves(primary, _populate)  # defaults get overriden

    resolved = {}
    for path_str, value in flat.items():
        if isinstance(value, Mapping) and len(value) == 0 and isinstance(_get(resolved, path_str), Mapping):
            continue # avoid overwriting existing mappings with empty leaf mappings
        if not _try_set(resolved, path_str, value):
            raise ValueError(f"Failed to set path {path_str} in resolved mapping.")

    return resolved

def _is_primitive_cls(t: type) -> bool:
    """Check if an object is a primitive type (int, float, str, bool, or None)."""
    return issubclass(t, (int, float, str, bool))

def _is_primitive(obj: object) -> bool:
    """Check if an object is a primitive type (int, float, str, bool, or None)."""
    return obj is None or _is_primitive_cls(type(obj))

def _get_primitive(obj: object, _type: Callable[[Any], T]) -> T | _MISSING_CLS:
    if _is_primitive(obj):
        try:
            return _type(obj)
        except (ValueError, TypeError):
            pass
    return _MISSING