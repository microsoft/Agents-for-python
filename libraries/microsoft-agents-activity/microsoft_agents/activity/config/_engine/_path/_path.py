# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from __future__ import annotations

from typing import (
    Any,
    Callable,
    Iterator,
    Mapping,
    MutableMapping,
    overload,
    Sequence
)
from typing_extensions import TYPE_CHECKING

from ._path_segment import _PathSegment, _SimplePathSegment, _Wildcard

if TYPE_CHECKING:
    from ._traverse import _TraverseState

class _Path:

    def __init__(self, *segments: str | _PathSegment):

        _segments = [
            segment if isinstance(segment, _PathSegment) else _SimplePathSegment(segment, ignore_case=True, ignore_underscores=False)
            for segment in segments if segment
        ]
        _segments = [ segment for segment in _segments if segment.string ]
        self._segments = _segments
        self._cached_string: str | None = None
        self._is_simple = not any(segment.__class__ != _SimplePathSegment for segment in self._segments)
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
        if isinstance(path, str):
            return _Path(path)
        if isinstance(path, list):
            return _Path(*path)
        if isinstance(path, _Path):
            return path
        raise TypeError(f"Unsupported type for create: {type(path)}")

    def __hash__(self) -> int:
        return hash(tuple( seg.string for seg in self._segments ))

    @staticmethod
    def from_strings(*segments: str, ignore_case: bool = True, ignore_underscores: bool = False) -> _Path:
        return _Path(*(_SimplePathSegment(segment, ignore_case=ignore_case, ignore_underscores=ignore_underscores) for segment in segments))

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
            self._cached_string = "::".join(segment.string for segment in self._segments)
        return self._cached_string

    def __repr__(self) -> str:
        return f"_Path(segments={self._segments!r})"

    def __len__(self) -> int:
        return len(self._segments)

    def __add__(self, other: str | int | _Path  | _PathSegment) -> _Path:
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

    def traverse(self, obj: Any, handler: Callable[[_TraverseState, Any], None]) -> None:
        from ._traverse import _traverse
        _traverse(self, obj, handler)

    def get(
        self,
        mapping: Mapping,
        default: Any = None,
        skip_none: bool = False,
        none_is_missing: bool = False,
    ) -> tuple[Any, _Path]:
        """Return the first matched value and its relative source path segments."""
        from ._utils import _get
        return _get(mapping, self, default=default, skip_none=skip_none, none_is_missing=none_is_missing)

    def set(
        self,
        mapping: MutableMapping,
        value: Any,
        *,
        overwrite: bool = False,
    ) -> bool:
        from ._utils import _try_set
        return _try_set(mapping, self, value, overwrite=overwrite)

    def collect(
        self,
        mapping: Mapping,
        skip_none: bool = False,
    ) -> list[Any]:
        from ._utils import _collect
        return _collect(mapping, self, skip_none=skip_none)

class _WildcardPathClass(_Path):

    def __init__(self):
        self._wildcard = _Wildcard()

    @overload
    def __getitem__(self, key: int) -> _PathSegment: ...
    @overload
    def __getitem__(self, key: slice) -> _Path: ...
    def __getitem__(self, key: Any) -> _PathSegment | _Path:
        if isinstance(key, slice):
            return self
        elif isinstance(key, int):
            return self._wildcard
        raise TypeError(f"Unsupported key type: {type(key)}")

    @property
    def folded(self) -> str:
        return "**"

    @property
    def first(self) -> str:
        return self._wildcard.string
    
    @property
    def last(self) -> str:
        return self._wildcard.string

    def __add__(self, other: str | int | _Path | _PathSegment) -> _Path:
        return self

    def check(self, other: _Path) -> bool:
        return True

    def __bool__(self) -> bool:
        return True

    def __str__(self) -> str:
        return "**"

    def __repr__(self) -> str:
        return "_WildcardPath"

    def __iter__(self) -> Iterator[_PathSegment]:
        return iter(self._segments)

    def __len__(self) -> int:
        return 1

_WildcardPath = _WildcardPathClass()

_PathProxy = str | Sequence[str] | _Path