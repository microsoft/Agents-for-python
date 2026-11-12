# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from ._engine import _Path, _SimplePathSegment, _Wildcard, _PathSegment

def _get_segments(*segments: str, **kwargs) -> list[_PathSegment]:
    return [
        _SimplePathSegment(segment, **kwargs) if segment != "*" else _Wildcard()
        for segment in segments
    ]


def _legpath(*segments: str) -> _Path:
    """Create a legacy-style path with case-insensitive and underscore-ignored segments."""
    return _Path(*_get_segments(*segments, ignore_case=True, ignore_underscores=True))

def _netpath(*segments: str) -> _Path:
    """Create a path with case-insensitive and underscore-preserved segments, 
    mimicking .NET path behavior."""
    return _Path(*_get_segments(*segments, ignore_case=True, ignore_underscores=False))