# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from typing import (
    Any,
    Iterator,
    Sequence,
    overload,
)
from typing_extensions import TYPE_CHECKING

from ._path_segment import (
    _PathSegment,
    _SimplePathSegment,
    _Wildcard,
    _ExactPathSegment,
    _SegmentValue,
)

if TYPE_CHECKING:
    from .._traverse import _TraverseState


class _Path:
    """Internal sequence of matching policies, one per traversal level.

    String inputs create exact segments. ``from_strings`` enables case-insensitive
    matching by default; ``exact`` keeps both case and underscores significant.
    String rendering joins segments with ``::`` for display and diagnostics.
    """

    def __init__(self, *segments: _SegmentValue | _PathSegment):

        def _raise_if_empty() -> bool:
            raise ValueError("Path segments must not be empty")

        _segments = [
            segment if isinstance(segment, _PathSegment) else _ExactPathSegment(segment)
            for segment in segments
            if (segment != "" or _raise_if_empty())
        ]
        _segments = [segment for segment in _segments if segment.string]
        self._segments = _segments
        self._cached_string: str | None = None
        self._is_simple = not any(
            segment.__class__ != _SimplePathSegment for segment in self._segments
        )
        self._folded: str | None = None

    @property
    def is_simple(self) -> bool:
        return self._is_simple

    @property
    def folded(self) -> str:
        if self._folded is None:
            self._folded = "::".join(segment.folded for segment in self._segments)
        return self._folded

    @staticmethod
    def create(path: _PathProxy) -> _Path:
        """Accept a string/int key, segment list, segment, or existing path.

        Existing paths are reused. A list supplies consecutive path segments.
        """
        if isinstance(path, (int, str, _PathSegment)):
            return _Path(path)
        if isinstance(path, Sequence) and not isinstance(path, (str, bytes, bytearray)):
            return _Path(*path)
        if isinstance(path, _Path):
            return path
        raise TypeError(f"Unsupported type for create: {type(path)}")

    def __hash__(self) -> int:
        return hash(tuple(seg.string for seg in self._segments))

    @staticmethod
    def from_strings(
        *segments: _SegmentValue, ignore_case: bool = True, ignore_underscores: bool = False
    ) -> _Path:
        return _Path(
            *(
                _SimplePathSegment(
                    segment,
                    ignore_case=ignore_case,
                    ignore_underscores=ignore_underscores,
                )
                for segment in segments
            )
        )

    @staticmethod
    def exact(*segments: _SegmentValue) -> _Path:
        return _Path.from_strings(
            *segments, ignore_case=False, ignore_underscores=False
        )

    @property
    def first(self) -> str:
        return self._segments[0].string

    @property
    def last(self) -> str:
        return self._segments[-1].string

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

    # def __slice__(self, start: int | None, stop: int | None) -> _Path:
    #     return _Path(*self._segments[start:stop])

    def __str__(self) -> str:
        if self._cached_string is None:
            self._cached_string = "::".join(
                segment.string for segment in self._segments
            )
        return self._cached_string

    def __repr__(self) -> str:
        return f"_Path(segments={self._segments!r})"

    def __len__(self) -> int:
        return len(self._segments)

    def __add__(self, other: _SegmentValue | _Path | _PathSegment) -> _Path:
        if isinstance(other, int):
            other = str(other)
        if isinstance(other, str):
            other = _SimplePathSegment(other)
        if isinstance(other, _PathSegment):
            return _Path(*self._segments, other)
        if isinstance(other, _Path):
            return _Path(*self._segments, *other._segments)
        raise TypeError(f"Unsupported type for addition: {type(other)}")

    def __iter__(self) -> Iterator[_PathSegment]:
        return iter(self._segments)

_PathProxy = _SegmentValue | Sequence[_SegmentValue] | _PathSegment | _Path
