# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import functools

from typing import Any, Callable, Mapping, MutableMapping, TypeVar
from typing_extensions import TypeIs

from ._constants import _PATH_SEPARATOR, _PATH_ANY

T = TypeVar("T")


class _MissingType:
    """A special class used to represent missing values in the configuration."""

    def __bool__(self):
        return False


_MISSING = _MissingType()  # Singleton instance representing a missing value


def _is_missing(val: Any) -> TypeIs[_MissingType]:
    """Check if a value is the special _MissingType instance.

    :param val: The value to check.
    :return: True if the value is an instance of _MissingType, False otherwise.
    """
    return isinstance(val, _MissingType)


def _path(*args: str) -> str:
    """Construct a ``::``-separated key path from the given arguments.

    :param args: The individual parts of the key path.
    :return: The ``::``-separated key path.
    """
    return _PATH_SEPARATOR.join(args)


def _split(key: str) -> list[str]:
    return key.split(_PATH_SEPARATOR)


def _get_with_path(
    mapping: Mapping,
    *keys: str,
    default: Any = None,
    skip_none: bool = False,
    none_is_missing: bool = False,
) -> tuple[Any, list[str]]:
    """Return the first matched value and its relative source path segments."""

    final_path: list[str] = []
    none_found: bool = False
    for key in keys:
        path = _split(key)
        current = mapping
        break_from_inner: bool = False
        path_candidate = []
        for part in path:
            if isinstance(current, Mapping) and part in current:
                path_candidate.append(part)
                current = current[part]
            else:
                break_from_inner = True
                break
        if not break_from_inner:

            if current is None:
                none_found = True
                if not final_path:
                    final_path = path_candidate
                if skip_none:
                    continue

            return current, path_candidate

    if none_found and not none_is_missing:
        return None, final_path
    return default, final_path


def _get(
    mapping: Mapping,
    *keys: str,
    default: Any = None,
    skip_none: bool = False,
    none_is_missing: bool = False,
) -> Any:
    """Retrieve a value using alternative ``::``-separated key paths.

    :param mapping: The mapping to retrieve the value from.
    :param keys: The individual key paths to try.
    :param default: The default value to return if the key path is not found.
    :param skip_none: Whether to skip None values while traversing the mapping.
    :return: The retrieved value or the default value if not found.
    """
    value, _ = _get_with_path(
        mapping,
        *keys,
        default=default,
        skip_none=skip_none,
        none_is_missing=none_is_missing,
    )
    return value


def _collect_helper(
    current: Any,
    path_left: list[str],
    collection: dict[str, Any],
    current_path: list[str],
) -> None:

    if not path_left:
        collection[_path(*current_path)] = current
        return

    if isinstance(current, Mapping):

        part = path_left[0]
        for key in current:
            if part == _PATH_ANY or part == key:
                _collect_helper(
                    current[key], path_left[1:], collection, current_path + [key]
                )
                if part != _PATH_ANY:
                    break
    if isinstance(current, list):
        part = path_left[0]
        for idx, item in enumerate(current):
            if part == _PATH_ANY or part == str(idx):
                _collect_helper(
                    item, path_left[1:], collection, current_path + [str(idx)]
                )
                if part != _PATH_ANY:
                    break


def _collect_with_paths(mapping: Mapping, *keys: str) -> dict[str, Any]:
    collection: dict[str, Any] = {}
    for key in keys:
        _collect_helper(mapping, _split(key), collection, [])
    return collection


def _collect(mapping: Mapping, *keys: str) -> list[Any]:
    return list(_collect_with_paths(mapping, *keys).values())


def _try_set(
    mapping: MutableMapping, key: str, value: Any, *, overwrite: bool = False
) -> bool:
    """Set a value in a nested mapping using a ``::``-separated key path.

    :param mapping: The mapping to set the value in.
    :param key: The ``::``-separated key path.
    :param value: The value to set.
    :param overwrite: Whether to overwrite the existing value if the key already exists.
    """
    path = _split(key)
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
    """Set a value using a ``::``-separated path, overwriting any existing value.

    :param mapping: The mapping to set the value in.
    :param key: The ``::``-separated key path.
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
    """Replace environment-variable ``__`` separators with ``::``.

    :param name: The environment variable name.
    :return: The ``::``-separated key path, preserving case.
    """
    return name.replace("__", _PATH_SEPARATOR)


def _convert_lists_helper(current: Any) -> None:

    if isinstance(current, Mapping):
        if all(key.isnumeric() for key in current.keys()):
            keys_to_convert = sorted(list(current.keys()))
            for key in keys_to_convert:
                value = current[key]


def _convert_list_helper(base: Any, key: str) -> None:

    current = base[key]

    if isinstance(current, Mapping):
        if not current:
            return

        if all(isinstance(key, int) for key in current.keys()):
            keys_to_convert = sorted(list(current.keys()))
            base[key] = [current[key] for key in keys_to_convert]

        elif all(isinstance(key, str) and key.isnumeric() for key in current.keys()):
            keys_to_convert = sorted([int(k) for k in current.keys()])
            base[key] = [current[str(key)] for key in keys_to_convert]


def _convert_lists(base: Any) -> None:

    if isinstance(base, MutableMapping):
        for current_key, current in base.items():
            if isinstance(current, Mapping):
                _convert_list_helper(base, current_key)
                _convert_lists(base[current_key])
            elif isinstance(current, list):
                _convert_lists(current)
    elif isinstance(base, list):
        for i, item in enumerate(base):
            if isinstance(item, Mapping):
                _convert_list_helper(base, i)
                _convert_lists(base[i])
            elif isinstance(item, list):
                _convert_lists(item)


def _resolve(
    primary: Mapping,
    defaults: Mapping,
    *,
    path_transformer: Callable[[str], str] | None = None,
) -> dict:
    """Resolve a mapping by merging it with a defaults mapping.

    :param primary: The primary mapping to resolve.
    :param defaults: The defaults mapping What to merge with.
    :param path_transformer: Transform paths before merging. By default, replace
        environment-variable ``__`` separators with ``::``, preserving case.
    :return: The resolved mapping.
    """

    if not path_transformer:
        path_transformer = _parse_env_var_name

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
        if (
            isinstance(value, Mapping)
            and len(value) == 0
            and isinstance(_get(resolved, path_str), Mapping)
        ):
            continue  # avoid overwriting existing mappings with empty leaf mappings
        if not _try_set(resolved, path_str, value):
            raise ValueError(f"Failed to set path {path_str} in resolved mapping.")

    _convert_lists(resolved)
    return resolved


@functools.lru_cache(maxsize=10)
def _snake_to_camel(name: str) -> str:
    """Convert a snake_case name to PascalCase.

    :param name: The snake_case name.
    :return: The PascalCase name.
    """
    camel = ""
    j = 0
    for word in name.split("_"):
        if not word.strip():
            continue

        if j == 0:
            camel += word
        else:
            camel += word.capitalize()

        j += 1

    return camel


@functools.lru_cache(maxsize=10)
def _xcase_helper(
    snake_case_name: str,
    *,
    upper_snake: bool = True,
    lower_snake: bool = False,
    camel: bool = False,
    pascal: bool = False,
    all_caps: bool = True,
) -> set[str]:
    """Generate a list of name variants for a given snake_case name.

    :param snake_case_name: The snake_case name.
    :param upper_snake: Include upper snake case variant.
    :param lower_snake: Include lower snake case variant.
    :param camel: Include camel case variant.
    :param pascal: Include pascal case variant.
    :param all_caps: Include all caps variant.
    :return: A list of name variants.
    """
    variants = set()

    if upper_snake:
        variants.add(snake_case_name.upper())
    if lower_snake:
        variants.add(snake_case_name.lower())

    if camel or pascal or all_caps:
        camel_case = _snake_to_camel(snake_case_name)

        if camel:
            variants.add(camel_case)
        if pascal:
            variants.add(camel_case.capitalize())
        if all_caps:
            variants.add(camel_case.upper())

    return variants


def _xcase(
    *snake_case_names: str,
    upper_snake: bool = True,
    lower_snake: bool = False,
    camel: bool = False,
    pascal: bool = False,
    all_caps: bool = True,
) -> list[str]:
    """Generate a list of name variants for the given snake_case names.

    :param snake_case_names: The snake_case names.
    :param upper_snake: Include upper snake case variant.
    :param lower_snake: Include lower snake case variant.
    :param camel: Include camel case variant.
    :param pascal: Include pascal case variant.
    :param all_caps: Include all caps variant.
    :return: A list of name variants.
    """
    variants = set()
    for name in snake_case_names:
        variants.update(
            _xcase_helper(
                name,
                upper_snake=upper_snake,
                lower_snake=lower_snake,
                camel=camel,
                pascal=pascal,
                all_caps=all_caps,
            )
        )
    return list(variants)


@functools.lru_cache(maxsize=10)
def _xpath(
    *path_parts: str,
    upper_snake: bool = True,
    lower_snake: bool = True,
    camel: bool = False,
    pascal: bool = False,
    all_caps: bool = True,
) -> list[str]:
    """Generate casing variants of alternative configuration paths.

    :param snake_case_paths: Alternative snake_case paths using ``::`` separators.
        These are configuration paths, not XPath expressions.
    :param upper_snake: Include upper snake case variant.
    :param lower_snake: Include lower snake case variant.
    :param camel: Include camel case variant.
    :param pascal: Include pascal case variant.
    :param all_caps: Include all caps variant.
    :return: A list of name variants.
    """

    path = _path(*path_parts)

    res = _xcase(
        path,
        upper_snake=upper_snake,
        lower_snake=lower_snake,
        camel=camel,
        pascal=pascal,
        all_caps=all_caps,
    )
    return sorted(res)


def str_in(base: str, *sub: str) -> bool:
    """Check if all substrings are present in the base string.

    :param base: The base string.
    :param sub: Substrings to check for.
    :return: True if all substrings are present in the base string, False otherwise.
    """
    return any(s in base for s in sub)


def _resolve_keys_arg(*keys: str | list[str]) -> list[str]:
    resolved_keys = []
    for key in keys:
        if isinstance(key, str):
            resolved_keys.append(key)
        elif isinstance(key, list):
            resolved_keys.extend(key)
        else:
            raise ValueError(f"Invalid key type: {type(key)}")
    return resolved_keys
