# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import (
    Any,
    Mapping,
    MutableMapping,
)

from ._path import _Path, _PathProxy
from ._path_segment import _Wildcard
from ._traverse import _traverse_leaves, _TraverseState

def _get_with_path(
    mapping: Mapping,
    path: _PathProxy,
    default: Any = None,
    skip_none: bool = False,
    none_is_missing: bool = False,
) -> tuple[Any, _Path | None]:
    """Return the first matched value and its relative source path segments."""

    return_value: Any = None
    return_path: _Path | None = None

    def handler(state: _TraverseState, obj: Any) -> None:
        nonlocal return_value, return_path
        if skip_none and obj is None:
            return

        state.finished = True
        return_value = obj
        return_path = state.traversed

    _traverse_leaves(path, mapping, handler)

    if return_path is None or (none_is_missing and return_value is None):
        return default, None
    return return_value, return_path

def _get(
    mapping: Mapping,
    path: _PathProxy,
    default: Any = None,
    skip_none: bool = False,
    none_is_missing: bool = False,
) -> Any:
    """Retrieve a value using alternative ``::``-separated key paths.

    :param mapping: The mapping to retrieve the value from.
    :param _path: The key path to try.
    :param default: The default value to return if the key path is not found.
    :param skip_none: Whether to skip None values while traversing the mapping.
    :return: The retrieved value or the default value if not found.
    """
    value, _ = _get_with_path(
        mapping,
        path,
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
) -> None:

    if not path_left:
        collection[current_path.last] = current
        return

    segment = path_left[0]

    for key, val in segment.iter_steps(current):
        _collect_helper(
            val, path_left[1:], collection, current_path + str(key)
        )
        if not isinstance(segment, _Wildcard):
            break

def _collect_with_paths(mapping: Mapping, path: _PathProxy, *, skip_none: bool = False) -> dict[str, Any]:
    collection: dict[str, Any] = {}

    def handler(state: _TraverseState, obj: Any) -> None:
            if skip_none and obj is None:
                return
            if state.traversed.last in collection:
                raise KeyError(f"Duplicate key found for path: {state.traversed.last}")
            
            collection[state.traversed.last] = obj
            
    _traverse_leaves(path, mapping, handler)
    return collection


def _collect(mapping: Mapping, path: _PathProxy, *, skip_none: bool = False) -> list[Any]:
    return list(_collect_with_paths(mapping, path, skip_none=skip_none).values())


def _try_set(
    mapping: MutableMapping, _path: _PathProxy, value: Any, *, overwrite: bool = False
) -> bool:
    """Set a value in a nested mapping using a ``::``-separated key path.

    :param mapping: The mapping to set the value in.
    :param path: The key path as a _Path instance.
    :param value: The value to set.
    :param overwrite: Whether to overwrite the existing value if the key already exists.
    """

    path = _Path.create(_path)

    current = mapping

    for segment in path[:-1]:
        non_mutable_mapping_err: bool = False
        if isinstance(current, Mapping):
            matched, _, next_obj = segment.step_once(current)
            if matched:
                current = next_obj
                continue
            elif isinstance(current, MutableMapping):
                current[segment] = {}
                current = current[segment]
            else:
                non_mutable_mapping_err = True
        else:
            non_mutable_mapping_err = True

        if non_mutable_mapping_err:
            raise TypeError(
                f"Cannot set value for key path {path} in non-mutable mapping or list object"
            )

    if isinstance(current, MutableMapping):
        if overwrite or path.last not in current:
            current[path.last] = value
            return True
        return False
    else:
        raise TypeError(f"Cannot set value for key path {path} in non-mutable mapping")


def _set(mapping: MutableMapping, _path: _PathProxy, value: Any) -> None:
    """Set a value using a ``::``-separated path, overwriting any existing value.

    :param mapping: The mapping to set the value in.
    :param path: The ``::``-separated key path.
    :param value: The value to set.
    """
    _try_set(mapping, _path, value, overwrite=True)