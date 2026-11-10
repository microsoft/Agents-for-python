# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Callable, Mapping

from ._path import _Path, _PathProxy

@dataclass
class _TraverseState:

    path: _Path
    current: Any
    traversed: _Path = _Path()
    finished: bool = False

def _traverse_helper(
    state: _TraverseState,
    handler: Callable[[_TraverseState, Any], None],
    *,
    handle_inner: bool = True
) -> None:

    if not isinstance(state.current, (Mapping, Sequence)):
        return

    base_path = state.path
    segment = base_path[0]

    for key, next_obj in segment.iter_steps(state.current):

        if handle_inner or len(base_path) == 1:
            handler(state, next_obj)
            if state.finished:
                return

        state.path = state.path[1:]
        state.current = next_obj
        state.traversed = state.traversed + str(key)

        _traverse_helper(state, handler)

        if state.finished:
            return

        state.path = base_path


def _traverse_leaves(
    _path: _PathProxy,
    obj: Any,
    handler: Callable[[_TraverseState, Any], None]
) -> None:
    path = _Path.create(_path)
    state = _TraverseState(path=path, current=obj)
    _traverse_helper(state, handler, handle_inner=False)

def _traverse(
    _path: _PathProxy,
    obj: Any,
    handler: Callable[[_TraverseState, Any], None]
) -> None:
    path = _Path.create(_path)
    state = _TraverseState(path=path, current=obj)
    _traverse_helper(state, handler, handle_inner=True)