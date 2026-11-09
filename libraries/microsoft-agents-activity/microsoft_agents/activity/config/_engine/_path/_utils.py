# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import (
    Any,
    Mapping,
    Sequence,
    Iterable,
    MutableMapping,
)

from ._path import _Path, _Wildcard

def _traverse(
    mapping: Mapping,
    path: _Path,
    func: Callable[[Any, _Path], None]
) -> None:

    

def _get_with_path(
    mapping: Mapping,
    path: _Path,
    default: Any = None,
    skip_none: bool = False,
    none_is_missing: bool = False,
) -> tuple[Any, _Path]:
    """Return the first matched value and its relative source path segments."""

    final_path: _Path = _Path()
    none_found: bool = False
    current = mapping
    break_from_inner: bool = False
    path_candidate: _Path = _Path()
    for segment in path:
        matched, next_obj = segment.step(current)
        if matched:
            path_candidate += segment.string
            current = next_obj
        else:
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
    paths: Sequence[_Path],
    default: Any = None,
    skip_none: bool = False,
    none_is_missing: bool = False,
) -> tuple[Any, _Path]:
    """Retrieve a value using alternative ``::``-separated key paths.

    :param mapping: The mapping to retrieve the value from.
    :param paths: The individual key paths to try.
    :param default: The default value to return if the key path is not found.
    :param skip_none: Whether to skip None values while traversing the mapping.
    :return: The retrieved value or the default value if not found.
    """
    value, _ = _get_with_path(
        mapping,
        paths,
        default=default,
        skip_none=skip_none,
        none_is_missing=none_is_missing,
    )
    return value


def _collect_helper(
    current: Any,
    path_left: _Path,
    collection: dict[str, Any],
    current_path: _Path,
    skip_none: bool = False,
) -> None:

    if not path_left:
        collection[current_path.last] = current
        return

    segment = path_left[0]

    iter: Iterable[tuple[Any, Any]]
    if isinstance(current, Mapping):
        iter = current.items()
    elif isinstance(current, Sequence):
        iter = enumerate(current)

    for key, val in iter:
        if segment.check(key):
            _collect_helper(
                val, path_left[1:], collection, current_path + str(key)
            )
            if not isinstance(segment, _Wildcard):
                break

def _collect_with_paths(mapping: Mapping, paths: Sequence[_Path]) -> dict[str, Any]:
    collection: dict[str, Any] = {}
    for path in paths:
        _collect_helper(mapping, path, collection, _Path())
    return collection


def _collect(mapping: Mapping, paths: Sequence[_Path]) -> list[Any]:
    return list(_collect_with_paths(mapping, paths).values())


def _try_set(
    mapping: MutableMapping, path: _Path, value: Any, *, overwrite: bool = False
) -> bool:
    """Set a value in a nested mapping using a ``::``-separated key path.

    :param mapping: The mapping to set the value in.
    :param path: The key path as a _Path instance.
    :param value: The value to set.
    :param overwrite: Whether to overwrite the existing value if the key already exists.
    """
    current = mapping
    for part in path[:-1]:
        if isinstance(current, MutableMapping):

            matched, next_obj = part.step(current)
            if matched:
                current = next_obj
                continue
            else:
                current[part] = {}
                current = current[part]
        else:
            raise TypeError(
                f"Cannot set value for key path {path} in non-mutable mapping or list object"
            )

    if isinstance(current, MutableMapping):
        if overwrite or path[-1] not in current:
            current[path[-1]] = value
            return True
        return False
    else:
        raise TypeError(f"Cannot set value for key path {path} in non-mutable mapping")


def _set(mapping: MutableMapping, path: _Path, value: Any) -> None:
    """Set a value using a ``::``-separated path, overwriting any existing value.

    :param mapping: The mapping to set the value in.
    :param key: The ``::``-separated key path.
    :param value: The value to set.
    """
    _try_set(mapping, path, value, overwrite=True)