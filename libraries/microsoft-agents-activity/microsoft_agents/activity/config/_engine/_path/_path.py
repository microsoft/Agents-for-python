# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from typing import Any, Iterator, overload

from ._path_segment import _PathSegment

class _Path:

    def __init__(self, *segments: str | _PathSegment):

        _segments = [
            segment if isinstance(segment, _PathSegment) else _PathSegment(segment)
            for segment in segments
        ]
        _segments = [ segment for segment in _segments if segment.string ]
        self._segments = _segments
        self._cached_string: str | None = None

    @staticmethod
    def from_strings(*segments: str, ignore_case: bool = False, ignore_underscores: bool = False) -> _Path:
        return _Path(*(_PathSegment(segment, ignore_case=ignore_case, ignore_underscores=ignore_underscores) for segment in segments))

    @property
    def first(self) -> str:
        return self._segments[0].string if self._segments else ""

    @property
    def last(self) -> str:
        return self._segments[-1].string if self._segments else ""

    def check(self, other: _Path) -> bool:
        if not isinstance(other, _Path):
            raise TypeError(f"Unsupported type for check: {type(other)}")
        if len(self._segments) != len(other._segments):
            return False
        return all(s.check(o) for s, o in zip(self._segments, other._segments))

    def __bool__(self) -> bool:
        return bool(self._segments)

    @overload
    def __getitem__(self, key: int) -> _PathSegment: ...
    @overload
    def __getitem__(self, key: slice) -> _Path: ...
    def __getitem__(self, key: Any) -> _PathSegment | _Path:
        if isinstance(key, slice):
            return _Path(*self._segments[key])
        elif isinstance(key, int):
            return self._segments[key]
        raise TypeError(f"Unsupported key type: {type(key)}")

    def __slice__(self, start: int | None, stop: int | None) -> _Path:
        return _Path(*self._segments[start:stop])

    def __str__(self) -> str:
        if self._cached_string is None:
            self._cached_string = "::".join(segment.string for segment in self._segments)
        return self._cached_string

    def __repr__(self) -> str:
        return f"_Path(segments={self._segments!r})"

    def __add__(self, other: str | _Path  | _PathSegment) -> _Path:
        if isinstance(other, str):
            other = _PathSegment(other)
        if isinstance(other, _PathSegment):
            return _Path(*self._segments, other)
        if isinstance(other, _Path):
            return _Path(*self._segments, *other._segments)
        raise TypeError(f"Unsupported type for addition: {type(other)}")

    def __iter__(self) -> Iterator[_PathSegment]:
        return iter(self._segments)