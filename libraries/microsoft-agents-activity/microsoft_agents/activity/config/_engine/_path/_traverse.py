# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

from .types import _Wildcard, _MISSING, _Path, _PathProxy, _SegmentValue
from ._step import iter_steps


@dataclass
class _TraverseState:
    """Shared traversal cursor and stack of actual source keys.

    During a handler call, ``current`` is the candidate's parent and
    ``path_index`` counts consumed segments. Backtracking restores the cursor,
    parent, and key stack unless ``finished`` stops traversal. Handlers retaining
    keys beyond the call must copy the stack.
    """

    path: _Path
    current: Any
    path_index: int = 0
    traversed_keys: list[_SegmentValue] = field(default_factory=list)
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
    if isinstance(state.current, (str, bytes, bytearray)):
        return

    segment = state.path[state.path_index]

    for key, next_obj in iter_steps(segment, state.current):

        state.path_index += 1
        state.traversed_keys.append(key)

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
    _path: _PathProxy,
    obj: Any,
    handler: Callable[[_TraverseState, Any], None],
    ensure_singular_path: bool = False,
) -> None:
    path = _Path.create(_path)
    if ensure_singular_path and (len(path) == 0 or not path.is_simple):
        raise ValueError("Path must be non-empty and simple.")
    state = _TraverseState(path=path, current=obj)
    _traverse_helper(state, handler, handle_inner=False)


def _traverse(
    _path: _PathProxy,
    obj: Any,
    handler: Callable[[_TraverseState, Any], None],
    ensure_singular_path: bool = False,
) -> None:
    path = _Path.create(_path)
    if ensure_singular_path and (len(path) == 0 or not path.is_simple):
        raise ValueError("Path must be non-empty and simple.")
    state = _TraverseState(path=path, current=obj)
    _traverse_helper(state, handler, handle_inner=True)


@dataclass
class _LookupResult:
    """Distinguish absence from a matched None; optionally retain source keys."""

    found: bool = False
    value: Any = _MISSING
    matched_keys: list[_SegmentValue] | None = None


def _lookup(
    obj: Mapping | Sequence,
    path: _PathProxy,
    *,
    include_path: bool = False,
    skip_none: bool = False,
) -> _LookupResult:
    """Find the first complete non-wildcard match, backtracking as needed.

    ``skip_none`` ignores ``None`` leaves without rejecting other falsey values.
    Source keys are copied only when ``include_path`` is requested.
    """

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

    _traverse_leaves(path, obj, handler, ensure_singular_path=True)
    return result
