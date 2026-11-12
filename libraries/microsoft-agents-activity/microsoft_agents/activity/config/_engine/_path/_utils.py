
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import (
    Any,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from .types import _Path, _PathProxy, _Wildcard
from ._traverse import _traverse_leaves, _TraverseState, _lookup, _validate_singular_path
from ._step import iter_steps, step_once

def _get_with_path(
    obj: Mapping | Sequence,
    path: _PathProxy,
    default: Any = None,
    skip_none: bool = False,
    none_is_missing: bool = False,
) -> tuple[Any, _Path | None]:
    """Return the first matched value and its relative source path segments."""

    result = _lookup(
        obj,
        path,
        include_path=True,
        skip_none=skip_none,
    )

    if not result.found or (none_is_missing and result.value is None):
        return default, None
    return result.value, _Path.exact(*(result.matched_keys or []))

def _get(
    obj: Mapping | Sequence,
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
    result = _lookup(
        obj,
        path,
        include_path=False,
        skip_none=skip_none,
    )
    if not result.found or (none_is_missing and result.value is None):
        return default
    return result.value


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

    for key, val in iter_steps(segment, current):
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
            last = state.traversed_keys[-1]
            if last in collection:
                raise KeyError(f"Duplicate key found for path: {last}")
            
            collection[last] = obj
            
    _traverse_leaves(path, mapping, handler)
    return collection


def _collect(mapping: Mapping, path: _PathProxy, *, skip_none: bool = False) -> list[Any]:
    return list(_collect_with_paths(mapping, path, skip_none=skip_none).values())


def _try_set(
    obj: MutableMapping | MutableSequence, _path: _PathProxy, value: Any, *, overwrite: bool = False
) -> bool:
    """Set a value in a nested mapping using a ``::``-separated key path.

    :param mapping: The mapping to set the value in.
    :param path: The key path as a _Path instance.
    :param value: The value to set.
    :param overwrite: Whether to overwrite the existing value if the key already exists.
    """
    _validate_singular_path(_path)

    path = _Path.create(_path)

    current = obj

    for segment in path[:-1]:
        non_mutable_mapping_err: bool = False
        if isinstance(current, Mapping):
            matched, _, next_obj = step_once(segment, current)
            if matched:
                current = next_obj
                continue
            elif isinstance(current, MutableMapping):
                current[segment.string] = {}
                current = current[segment.string]
            else:
                non_mutable_mapping_err = True
        elif isinstance(current, MutableSequence):
            matched, _, next_obj = step_once(segment, current)
            if matched:
                current = next_obj
                continue
            elif isinstance(current, MutableSequence):
                raise RuntimeError("Cannot modify intermediary list elements")
            else:
                non_mutable_mapping_err = True
        else:
            non_mutable_mapping_err = True

        if non_mutable_mapping_err:
            raise TypeError(
                f"Cannot set value for key path {path} in non-mutable mapping or list object"
            )

    if isinstance(current, MutableMapping):
        matched, key, next_obj = step_once(path[-1], (current))
        if matched:
            if not overwrite:
                return False
            current[key] = value
        else:
            current[path.last] = value
        return True
    elif isinstance(current, MutableSequence):
        matched, key, next_obj = step_once(path[-1], current)
        if not matched:
            raise IndexError(f"List index out of range for key path {path}")
        if matched and not overwrite:
            return False
        current[key] = value
        return True
    else:
        raise TypeError(f"Cannot set value for key path {path} in non-mutable mapping")


def _set(obj: MutableMapping | MutableSequence, _path: _PathProxy, value: Any) -> None:
    """Set a value using a ``::``-separated path, overwriting any existing value.

    :param mapping: The mapping to set the value in.
    :param path: The ``::``-separated key path.
    :param value: The value to set.
    """
    _try_set(obj, _path, value, overwrite=True)

def _pop(obj: MutableMapping | MutableSequence, _path: _PathProxy, *, default: Any = None) -> Any:

    _validate_singular_path(_path)

    value = default

    def handler(state: _TraverseState, obj: Any) -> None:
        nonlocal value
        if state.no_path_left:
            if isinstance(state.current, MutableMapping):
                del state.current[state.traversed_keys[-1]]
                state.finished = True
                value = obj
            elif isinstance(state.current, MutableSequence):
                del state.current[int(state.traversed_keys[-1])]
                state.finished = True
                value = obj
            else:
                raise TypeError("Cannot pop value from non-mutable mapping or list object")

    _traverse_leaves(_path, obj, handler)
    return value