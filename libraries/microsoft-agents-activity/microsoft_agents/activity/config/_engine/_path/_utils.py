# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from dataclasses import dataclass
from typing import (
    Any,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from .types import _Path, _PathProxy, _Wildcard, _SegmentValue
from ._traverse import (
    _traverse_leaves,
    _TraverseState,
    _lookup,
)
from ._step import iter_steps, step_once


def _get_with_path(
    obj: Mapping | Sequence,
    path: _PathProxy,
    default: Any = None,
    skip_none: bool = False,
    none_is_missing: bool = False,
) -> tuple[Any, _Path | None]:
    """Return the first matched value and an exact path with stored key spelling.

    ``skip_none`` searches later candidates after a ``None`` match.
    ``none_is_missing`` instead returns the default for the selected ``None``
    without continuing. Missing values return ``(default, None)``.
    """

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
    """Return the first leaf matching one non-wildcard path, without building a path.

    :param obj: Mapping or sequence to search.
    :param path: A key, list of segments, or internal path object.
    :param default: Returned when no match exists.
    :param skip_none: Continue searching after a ``None`` match.
    :param none_is_missing: Return the default for a selected ``None`` without
        searching later candidates.
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


@dataclass(frozen=True)
class _CollectEntry:

    path: _Path
    value: Any


def _collect_with_paths(
    mapping: Mapping, path: _PathProxy, *, skip_none: bool = False
) -> dict[_SegmentValue, _CollectEntry]:
    """Collect leaves into a dictionary keyed by rendered full matched paths.

    Explicit wildcard segments enumerate mapping keys; integer segments index
    sequences. Repeated leaf names under distinct paths remain separate.
    Duplicate rendered paths raise ``KeyError``. ``skip_none`` omits ``None`` leaves.
    """
    collection: dict[str, _CollectEntry] = {}

    def handler(state: _TraverseState, obj: Any) -> None:
        if skip_none and obj is None:
            return
        traversed_path = _Path.exact(*state.traversed_keys)
        if str(traversed_path) in collection:
            raise KeyError(f"Duplicate key found for path: {traversed_path}")

        collection[str(traversed_path)] = _CollectEntry(
            path=traversed_path,
            value=obj,
        )

    _traverse_leaves(path, mapping, handler)
    return collection


def _collect(
    mapping: Mapping,
    path: _PathProxy,
    *,
    skip_none: bool = False,
) -> list[Any]:
    return [
        entry.value
        for entry in _collect_with_paths(mapping, path, skip_none=skip_none).values()
    ]


def _try_set(
    obj: MutableMapping | MutableSequence,
    _path: _PathProxy,
    value: Any,
    *,
    overwrite: bool = False,
) -> bool:
    """Set one non-wildcard path, returning whether a value was assigned.

    Missing mapping parents are created. Intermediate sequence positions must
    already exist; an absent one raises ``RuntimeError``. Final sequence
    positions must exist too, otherwise ``IndexError`` is raised. Traversing an
    existing scalar or assigning to a read-only parent raises ``TypeError``.

    Assignment selects the first matching parent at each level without
    backtracking. With case/underscore-insensitive paths, an incomplete earlier
    branch can shadow an existing complete match, even with overwrite disabled.
    Use exact paths when matching sibling names are ambiguous.

    :param obj: Mutable mapping or sequence to modify.
    :param _path: A key, list of segments, or internal path object.
    :param value: The value to set.
    :param overwrite: Allow replacement of an existing match. Replacement keeps
        its stored key spelling and mapping position.
    :return: False if the selected parent already contains a match and overwrite
        is disabled, else True.
    """
    path = _Path.create(_path)

    if len(path) == 0 or not path.is_simple:
        raise ValueError("Path must be non-empty and simple when setting.")

    current = obj

    for segment in path[:-1]:
        non_mutable_mapping_err: bool = False
        if isinstance(current, Mapping):
            matched, _, next_obj = step_once(segment, current)
            if matched:
                current = next_obj
                continue
            elif isinstance(current, MutableMapping):
                current[segment.value] = {}
                current = current[segment.value]
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
            current[path[-1].value] = value
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
    """Assign one explicit path, overwriting matches under ``_try_set`` rules."""
    _try_set(obj, _path, value, overwrite=True)


def _pop(
    obj: MutableMapping | MutableSequence, _path: _PathProxy, *, default: Any = None
) -> Any:
    """Remove the first matched leaf from a mutable mapping or sequence.

    A missing path returns ``default``. Sequence deletion shifts later elements.
    Wildcards are rejected; a matched read-only parent raises ``TypeError``.
    """

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
                raise TypeError(
                    "Cannot pop value from non-mutable mapping or list object"
                )

    _traverse_leaves(_path, obj, handler, ensure_singular_path=True)
    return value
