# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

from .types import _Wildcard, _MISSING, _Path, _PathProxy
from ._step import iter_steps


def _validate_singular_path(path: _PathProxy) -> None:
    if (not isinstance(path, int) and not path) or (
        isinstance(path, _Path) and not path.is_simple
    ):
        raise ValueError("Path must be non-empty and simple.")
    elif isinstance(path, _Wildcard):
        raise ValueError("Path must not be a wildcard.")


@dataclass
class _TraverseState:

    path: _Path
    current: Any
    path_index: int = 0
    traversed_keys: list[str] = field(default_factory=list)
    finished: bool = False

    @property
    def no_path_left(self) -> bool:
        return self.path_index >= len(self.path)

    def traversed_path(self) -> _Path:
        return _Path.exact(*self.traversed_keys)


def _traverse_helper(
    state: _TraverseState,
    handler: Callable[[_TraverseState, Any], None],
    *,
    handle_inner: bool = True,
) -> None:

    if not isinstance(state.current, (Mapping, Sequence)) or state.no_path_left:
        return

    segment = state.path[state.path_index]

    for key, next_obj in iter_steps(segment, state.current):

        state.path_index += 1
        state.traversed_keys.append(str(key))

        if handle_inner or state.path_index == len(state.path):
            handler(state, next_obj)
            if state.finished:
                return

        prev_current = state.current
        state.current = next_obj

        _traverse_helper(state, handler, handle_inner=handle_inner)

        if state.finished:
            return

        state.traversed_keys.pop()
        state.current = prev_current
        state.path_index -= 1


def _traverse_leaves(
    _path: _PathProxy, obj: Any, handler: Callable[[_TraverseState, Any], None]
) -> None:
    path = _Path.create(_path)
    state = _TraverseState(path=path, current=obj)
    _traverse_helper(state, handler, handle_inner=False)


def _traverse(
    _path: _PathProxy, obj: Any, handler: Callable[[_TraverseState, Any], None]
) -> None:
    path = _Path.create(_path)
    state = _TraverseState(path=path, current=obj)
    _traverse_helper(state, handler, handle_inner=True)


@dataclass
class _LookupResult:

    found: bool = False
    value: Any = _MISSING
    matched_keys: list[str] | None = None


def _lookup(
    obj: Mapping | Sequence,
    path: _PathProxy,
    *,
    include_path: bool = False,
    skip_none: bool = False,
) -> _LookupResult:

    _validate_singular_path(path)

    result = _LookupResult()

    def handler(state: _TraverseState, candidate: Any) -> None:
        nonlocal result

        if skip_none and candidate is None:
            return

        result.found = True
        result.value = candidate
        if include_path:
            result.matched_keys = state.traversed_keys.copy()
        state.finished = True

    _traverse_leaves(path, obj, handler)
    return result
