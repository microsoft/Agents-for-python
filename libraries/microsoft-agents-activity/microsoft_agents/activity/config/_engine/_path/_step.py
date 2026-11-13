# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from typing import Any, Iterator, Mapping, Sequence
from .types._path_segment import _PathSegment, _SimplePathSegment


def step_once(segment: _PathSegment, obj: Any) -> tuple[bool, Any, Any]:
    try:
        key, next_obj = next(iter_steps(segment, obj))
        return True, key, next_obj
    except StopIteration:
        return False, None, None


def iter_steps(segment: _PathSegment, obj: Any) -> Iterator[tuple[Any, Any]]:
    from ._query import _QueryDict

    if isinstance(obj, Mapping):
        if isinstance(obj, _QueryDict) and isinstance(segment, _SimplePathSegment):
            bucket = obj._shortcuts.get_bucket(segment)
            if not bucket:
                return
            for entry in bucket:
                if segment.check(entry.key):
                    yield entry.key, entry.value
        else:
            for key in obj:
                if segment.check(key):
                    yield key, obj[key]
    elif isinstance(obj, Sequence) and segment.string.isdecimal():
        index = int(segment.string)
        if 0 <= index < len(obj) or -len(obj) <= index < 0:
            yield index, obj[index]
